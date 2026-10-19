# Architectural Design Document: Production-Conscious Email Validator

**Lead Developer & Architect:** Mani Subramanian  
**Target Environment:** Python 3.11+ / SQLite  
**Audience:** Junior & Mid-Level Backend Developers  

---

## 1. Architectural Philosophy & Problem Statement

Input validation is the first line of defense in any registration pipeline. For a junior developer, the task *"validate an email address and check if it's taken"* often looks deceptively simple: write a regular expression, execute a SQL query, and return a boolean.

In production engineering, however, that simplistic approach introduces three severe risks:
1. **Catastrophic Backtracking (ReDoS):** Complex regex patterns can lock CPU threads at 100% when evaluating malicious strings.
2. **SQL Injection & Case Inconsistencies:** Naive string interpolation (`f"SELECT * FROM users WHERE email = '{email}'"`) opens SQL injection, while case-sensitive lookups allow duplicate registrations (`John@example.com` vs `john@example.com`).
3. **Account Enumeration Vulnerabilities:** Publicly disclosing whether an email exists allows bad actors to scrape and identify registered users.

This component is engineered with **separation of concerns, defensive typing, repository abstraction, and pragmatic validation rules**.

---

## 2. Component Architecture & Separation of Concerns

```
+-------------------------------------------------------------------------+
|                          Registration Service                           |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  EmailValidator (Service Layer)                         |
|  - Step 1: Type & null safety checks                                    |
|  - Step 2: Leading/trailing whitespace stripping                        |
|  - Step 3: RFC 5321 length limits (254 total / 64 local / 255 domain)   |
|  - Step 4: Syntactic structure checks (@, dot, labels, TLD)             |
|  - Step 5: Canonical normalization                                      |
+-------------------------------------------------------------------------+
                                     |
                                     v (Dependency Injection)
+-------------------------------------------------------------------------+
|                 UserRepository (Data Access Interface)                  |
|  - Protocol: is_registered(email) -> bool                               |
|  - Protocol: register_user(email) -> bool                               |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|               SQLiteUserRepository (Concrete Storage)                   |
|  - Parameterized queries ('?' bindings)                                 |
|  - Case-insensitive unique index (COLLATE NOCASE)                       |
|  - Supports :memory: for tests and users.db for persistent workloads   |
+-------------------------------------------------------------------------+
```

### Why Use Dependency Injection?
Rather than hardcoding SQLite queries inside `EmailValidator`, we inject `UserRepository`. This allows:
- **Fast, hermetic unit testing:** Run tests in-memory (`:memory:`) or with test doubles without disk I/O.
- **Pluggability:** In a production microservice, the team can swap SQLite for PostgreSQL, MySQL, Redis, or DynamoDB without changing a single line of validation logic.

---

## 3. Email Validation: Pragmatism vs. RFC Overkill

### The RFC 5322 Dilemma
The official RFC 822/5322 grammar for email addresses permits extraordinary syntax, including quoted strings with whitespace (`"john doe"@example.com`), IP literal domains (`user@[192.168.1.1]`), and comments inside parentheses (`john(comment)@example.com`).

Writing a regex to fully support RFC 5322 results in a notorious 6,300-character monstrosity that is unreadable, prone to ReDoS, and allows addresses that no modern email delivery service (SendGrid, Mailgun, AWS SES) will successfully route.

### Our Multi-Stage Validation Strategy
Instead of one massive regex, we apply clean, sequential guard clauses:
1. **Type & Null Check:** Fails fast if input is not `isinstance(email, str)`.
2. **Whitespace Stripping:** Users on mobile devices often accidentally paste leading or trailing spaces. Stripping them transparently improves UX.
3. **Length Safeguards:** Enforce RFC 5321 hard limits:
   - Max 254 characters total.
   - Max 64 characters for the local-part.
   - Max 255 characters for the domain-part.
4. **Single `@` Separator:** Exactly one `@` dividing local-part and domain-part.
5. **Local-Part Rules:**
   - Must not start or end with a dot (`.`).
   - Must not contain consecutive dots (`..`).
   - Alphanumeric plus safe standard characters (`._%+-`).
6. **Domain-Part Rules:**
   - Must contain at least two labels separated by a dot.
   - Labels cannot start or end with hyphens.
   - Top-Level Domain (TLD) must be strictly alphabetic and $\ge 2$ characters.
7. **The Ultimate Production Truth:**
   > *"The only 100% guarantee that an email is valid and belongs to the user is sending a cryptographically secure confirmation link via SMTP."*
   Input validation confirms syntax; email verification confirms existence and ownership.

---

## 4. Normalization and Case-Insensitivity

According to RFC 5321 §2.3.11, the local-part of a mailbox *can* theoretically be case-sensitive (`Postmaster` vs `postmaster`), while the domain is strictly case-insensitive.

However, in modern production systems (Google Workspace, Microsoft 365, Proton, Yahoo):
- Local parts are treated as **case-insensitive** for routing (`Alice@example.com` and `alice@example.com` land in the same inbox).
- Allowing case-sensitive registrations creates security vulnerabilities: account impersonation, duplicate user confusion, and billing race conditions.

**Our Implementation:**
- Domain names are lowercased during normalization: `normalized = f"{local_part}@{domain_part.lower()}"`.
- Database lookups enforce case-insensitivity using SQLite's `COLLATE NOCASE` index and queries.

---

## 5. Security & Data Protection Considerations

### 1. SQL Injection Prevention
We enforce strictly parameterized queries:
```python
# CORRECT (Parameterized):
cursor.execute("SELECT 1 FROM users WHERE email = ? COLLATE NOCASE LIMIT 1;", (email,))

# DANGEROUS (Never use string interpolation):
# cursor.execute(f"SELECT 1 FROM users WHERE email = '{email}'")
```

### 2. User Enumeration Mitigation
In public production endpoints (e.g. `POST /api/register`), directly returning `"Email is already registered"` allows attackers to test a list of leaked emails to see which targets hold accounts on your service.

**Production Recommendation for Junior Developers:**
In this exercise, returning `"Email is already registered"` directly meets the functional requirement. In an internet-facing production registration flow, you should:
- Apply strict IP and token rate-limiting.
- In sensitive workflows (e.g., password reset), return a uniform message: *"If an account exists for this address, a confirmation email has been sent."*

### 3. Masking & PII Protection
Real user emails should never be logged in raw plaintext in application traces or observability tools (Datadog, CloudWatch). For logging, hash the email with SHA-256 or mask: `j***n@example.com`.

---

## 6. Code Quality & Mentoring Guidelines

1. **Self-Documenting Code over Obvious Comments:**
   - Avoid: `x = email.strip() # strip the email`
   - Use: Comments before complex non-obvious business logic or RFC constraints.
2. **Dataclass with Slots & Immutability:**
   - `ValidationResult` uses `@dataclass(frozen=True, slots=True)` for memory efficiency, runtime speed, and immutability.
3. **Comprehensive Pytest Suite:**
   - Isolated in-memory fixtures (`:memory:`) guarantee fast, independent test execution without leftover state.
