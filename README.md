# Production-Conscious Email Validator Component

**Lead Developer & Mentor:** Mani Subramanian  
**Environment:** Python 3.11+ / SQLite / Pytest  
**Repository:** [https://github.com/spmaniusa-hub/Email_Validator](https://github.com/spmaniusa-hub/Email_Validator)  
**Quick Links:** [Architecture Design (DESIGN.md)](./DESIGN.md) | [User & Developer Guide (USER_GUIDE.md)](./USER_GUIDE.md) | [Prompts Trajectory (PROMPTS.md)](./PROMPTS.md)

---

## 1. Project Overview

This component implements an enterprise-grade **Email Validation and Availability Service** for user registration pipelines. It models how a senior Python backend engineer approaches input validation: prioritizing security, maintainability, clean data modeling, defensive typing, and testability.

### Key Capabilities
- **Strict Input Sanitization:** Safely handles `None`, non-string types, empty strings, and multi-character whitespace padding.
- **Syntactic Structure Verification:** Validates the presence of a single `@`, RFC 5321 length limits, dot placement rules (no leading/trailing/consecutive dots), domain label constraints, and valid top-level domains ($\ge 2$ alphabetic characters).
- **SQLite User Store (Simulated Database):** Decoupled through the Repository Pattern with pre-seeded demonstration accounts (`somya@example.com`, `John@example.com`, `Alice@example.com`).
- **SQL Injection Defense:** All queries utilize parameterized placeholders (`?`) with case-insensitive `COLLATE NOCASE` indexes.
- **Strongly Typed Result Object:** Returns immutable `ValidationResult` dataclass instances featuring clean status codes and human-readable messages.
- **50 Automated Pytest Tests:** Comprehensive coverage across valid, invalid, duplicate, and edge-case scenarios.

---

## 2. Expected Behavior (Prompt Scenarios)

The simulation database is seeded with:
- `somya@example.com`
- `John@example.com`
- `Alice@example.com`

| Input Address | Validation Status | Output Message |
|---|:---:|---|
| `somya@example.com` | `ALREADY_REGISTERED` | `Email is already registered` |
| `newuser@example.com` | `AVAILABLE` | `Email format is valid and email is available for registration.` |
| `JOHN@EXAMPLE.COM` | `ALREADY_REGISTERED` | `Email is already registered` *(case-insensitive check)* |
| `"   padme@domain.org   "` | `AVAILABLE` | `Email format is valid and email is available for registration.` *(trimmed)* |
| `None` | `INVALID_INPUT` | `Invalid input: Email must be a non-empty string.` |
| `""` or `"   "` | `INVALID_INPUT` | `Invalid input: Email cannot be empty or contain only whitespace.` |
| `user_without_at.com` | `INVALID_FORMAT` | `Invalid email format: Missing '@' symbol.` |
| `user@domain` | `INVALID_FORMAT` | `Invalid email format: Domain must contain a valid top-level domain...` |

---

## 3. Quick Start & Execution

### A. Run Automated Demo
Run the bundled demonstration to see all test scenarios executed against the SQLite database:
```bash
python3 demo.py
```

### B. Run Interactive CLI Mode
Test your own custom email inputs with interactive prompt feedback:
```bash
python3 demo.py --interactive
```

### C. Run Automated Pytest Suite
Execute all 50 automated unit and integration tests:
```bash
python3 -m pytest -v
```

---

## 4. Code Architecture

```text
Email_Validator/
├── email_validator/
│   ├── __init__.py          # Public API exports
│   ├── models.py            # Immutable ValidationResult dataclass & ValidationStatus enum
│   ├── database.py          # SQLiteUserRepository with parameterized queries & index
│   └── validator.py         # EmailValidator service with RFC guard clauses & normalization
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest in-memory fixtures (:memory:)
│   └── test_validator.py    # 50 comprehensive unit & integration tests
├── demo.py                  # Runnable CLI demonstration (automated & interactive)
├── requirements.txt         # Minimal test dependencies (pytest)
├── DESIGN.md                # Senior architecture, ReDoS defense, RFC realities, security
├── USER_GUIDE.md            # Detailed integration and developer manual
├── PROMPTS.md               # Prompt engineering and mentoring log
└── README.md                # This document
```

---

## 5. Senior Engineering Highlights

1. **Dependency Injection:** The `EmailValidator` depends on an abstract `UserRepository` protocol rather than hardcoding SQLite queries. This enables isolated testing via in-memory databases (`:memory:`) without disk I/O.
2. **Defensive Normalization:** Trims whitespace and normalizes domains to lowercase before performing indexed database lookups.
3. **No Fluff Comments:** Code comments are placed strategically before complex logic (e.g., dot rules, RFC length limits, parameterized SQL bindings) rather than annotating obvious lines.
4. **Zero Exposure of Real User Data:** Fictional seed data and sanitized query parameters ensure complete PII protection.
