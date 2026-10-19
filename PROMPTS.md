# Prompts & Mentoring Trajectory: Email Validation Component

**Developer & Mentor:** Mani Subramanian  
**Course & Project:** Python Backend Engineering / User Registration Pipeline  
**Target Environment:** Python 3.11+, SQLite, Pytest  

---

## 1. Primary User Request (Task Brief)

```text
Role : Act as a senior python developer who writes clean, maintainable, production-conscious and mentors junior developers.
Context : I am building the email validation components for user registration system. I am learning python but I want to understand how a real developer would approach this task.
The component will receive email address entered by users and determine whether they meet our application’s validation rules.This is not my complete registration system but only input validation component for email.
Task : Implement Email validation in python that :
1. Accept an email address as input.
2. Checks whether the input is a string and handled None, Empty Strings, whitespaces.
3. Removes leading and training whitespaces before validation.
4. check the basic email structure, including an @ symbol and valid domain with a dot.
5. If the email format is valid, check whether that email address is already registered in application’s user database and return email is already registered.
6. If the email is not registered, it should return a message like email format is valid and email is available for registration.
Technical constraints :
1. Use Python 3.11 or above.
2. For the demo, use a small SQLite database to simulate the registered users.
3. Include the automated tests using python in-built testing framework Pytest.
4. Do not expose the real user information.
Add the developer name as Mani Subramanian
Add appropriate comments to the generated code
Create PROMPTS.md README.md and USER_GUIDE.MD
add the design considerations to DESIGN.md
Examples : Expected Behavior
Assume the database already contain the below emails :
- somya@example.com
- John@example.com
- Alice@example.com
Program should produce the following results :
Input: somya@example.com -> Output: Email is already registered
Input: newuser@example.com -> Output: Email format is valid and email is available for registration.
```

---

## 2. Senior Developer Mentoring Breakdown & Planning Prompts

When approaching this task as a senior engineer mentoring junior developers, we break the solution into distinct architectural questions:

### Prompt / Architectural Question 1: Data Modeling & Return Types
```text
Question: Should our function return a plain string, a tuple (bool, str), or a structured object?
Senior Insight: Returning plain strings makes programmatic downstream use brittle (e.g. if my frontend or API handler needs to check if the email is valid, it shouldn't have to do string matching on "Email is already registered").
Decision: Use a strongly typed @dataclass(frozen=True, slots=True) called ValidationResult that contains:
- is_valid: bool
- is_available: bool
- message: str (human-readable)
- status: ValidationStatus enum (AVAILABLE, ALREADY_REGISTERED, INVALID_FORMAT, INVALID_INPUT)
- normalized_email: Optional[str]
```

### Prompt / Architectural Question 2: Database Coupling vs. Dependency Injection
```text
Question: Should the EmailValidator create its own SQLite connection directly inside the validate() method?
Senior Insight: Hardcoding database connection calls inside a validator tightly couples validation to a specific database driver. It also makes unit tests slow and messy because tests would write to disk and require manual teardown.
Decision: Define a UserRepository Protocol (interface) and implement a SQLiteUserRepository. Inject the repository into the validator:
validator = EmailValidator(user_repository=repo)
This enables running tests in-memory (:memory:) with zero cleanup overhead.
```

### Prompt / Architectural Question 3: Regex vs. Guard Clauses
```text
Question: Should we use a giant RFC 822 regex or step-by-step validation checks?
Senior Insight: Giant regexes are unmaintainable, prone to catastrophic backtracking (ReDoS), and produce poor error messages.
Decision: Use clean sequential guard clauses:
1. Type and None check
2. Whitespace strip and emptiness check
3. Length bounds (RFC 5321 max total length 254, local 64, domain 255)
4. Single '@' check
5. Local-part syntax check (no leading/trailing/consecutive dots)
6. Domain-part syntax check (at least one dot, valid labels, TLD >= 2 letters)
7. Normalization and database lookup
```

---

## 3. Test-Driven Development (TDD) Prompt Structure

To demonstrate production discipline, tests were created before finalizing features:

```python
# TDD Phase 1: Test edge cases and input sanitization
def test_none_input_rejected(): ...
def test_whitespace_stripped(): ...

# TDD Phase 2: Test syntax boundaries
def test_missing_at_symbol(): ...
def test_missing_dot_in_domain(): ...
def test_consecutive_dots_rejected(): ...

# TDD Phase 3: Test database lookups & case-insensitivity
def test_seeded_emails_already_registered(): ...
def test_case_insensitive_duplicate_check(): ...
def test_available_email(): ...

# TDD Phase 4: Test security defenses
def test_sql_injection_attempt_is_safely_parameterized(): ...
```

---

## 4. Key Takeaways for Junior Developers

1. **Never use string concatenation for SQL queries:** Always use parameterized placeholders (`?` in SQLite, `%s` in Postgres).
2. **Normalize before querying:** Always lowercase domain names and compare emails case-insensitively using `COLLATE NOCASE`.
3. **Comment the 'Why', not the 'What':** Comment before non-obvious business logic, RFC constraints, or security measures rather than simple variable assignments.
4. **Isolate test environments:** Use in-memory databases (`:memory:`) in Pytest fixtures to keep tests blazing fast ($< 0.2\text{s}$ for 50 tests) and independent.
