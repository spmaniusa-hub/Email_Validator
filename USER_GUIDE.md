# Email Validator Component: User & Developer Guide

**Author & Mentor:** Mani Subramanian  
**Language Version:** Python 3.11+  
**Testing Framework:** Pytest 9.0+  

This guide provides practical instructions for running, testing, and integrating the **Email Validator Component** into your user registration workflows.

---

## 1. Prerequisites & Environment Setup

### System Requirements
- Python 3.11 or higher (verified on Python 3.14)
- SQLite3 (built into Python standard library)
- `pytest` (for automated test suite execution)

### Quick Setup

Clone or navigate into the repository:
```bash
cd /Users/manisubramanian/Documents/GitHub/Email_Validator
```

Verify your Python version:
```bash
python3 --version
# Expected: Python 3.11.x, 3.12.x, 3.13.x, or 3.14.x
```

Install test dependencies:
```bash
python3 -m pip install pytest
```

---

## 2. Running the Automated Demonstration

The repository includes a ready-to-run demonstration script (`demo.py`) that initializes a SQLite database, loads the sample registered accounts, and tests a suite of valid, duplicate, whitespace-padded, and invalid inputs.

Run the automated test runner:
```bash
python3 demo.py
```

### Expected Output
```text
======================================================================
 EMAIL VALIDATION COMPONENT - AUTOMATED DEMONSTRATION
======================================================================
Developer: Mani Subramanian
Database Engine: SQLite (users.db)
Registered Users in DB: ['somya@example.com', 'John@example.com', 'Alice@example.com']

======================================================================
 TEST RESULTS TABLE
======================================================================
Input Tested                   | Status             | Output Message
---------------------------------------------------------------------------
somya@example.com              | ALREADY_REGISTERED | Email is already registered
newuser@example.com            | AVAILABLE          | Email format is valid and email is available for registration.
JOHN@EXAMPLE.COM               | ALREADY_REGISTERED | Email is already registered
Alice@example.com              | ALREADY_REGISTERED | Email is already registered
   padme@domain.org            | AVAILABLE          | Email format is valid and email is available for registration.
None                           | INVALID_INPUT      | Invalid input: Email must be a non-empty string.
                               | INVALID_INPUT      | Invalid input: Email cannot be empty or contain only whitespace.
                               | INVALID_INPUT      | Invalid input: Email cannot be empty or contain only whitespace.
user_at_domain.com             | INVALID_FORMAT     | Invalid email format: Missing '@' symbol.
user@domain                    | INVALID_FORMAT     | Invalid email format: Domain must contain a valid top-level domain (e.g. '.com', '.org').
user..name@domain.com          | INVALID_FORMAT     | Invalid email format: Local part cannot contain consecutive dots ('..').
user@domain.c                  | INVALID_FORMAT     | Invalid email format: Top-level domain 'c' is invalid (must be alphabetic and at least 2 letters).

---------------------------------------------------------------------------
Automated demonstration completed successfully.
```

---

## 3. Running Interactive Mode

You can test custom email addresses live using the interactive CLI flag:

```bash
python3 demo.py --interactive
```

### Interactive Session Example
```text
======================================================================
 INTERACTIVE EMAIL VALIDATION MODE
======================================================================
Type an email address to validate, or 'quit'/'exit' to stop.
Current DB emails: ['somya@example.com', 'John@example.com', 'Alice@example.com']

Enter email: somya@example.com
-> Result:   Email is already registered
-> Status:   ALREADY_REGISTERED
-> Cleaned:  somya@example.com

Enter email: candidate@mycompany.org
-> Result:   Email format is valid and email is available for registration.
-> Status:   AVAILABLE
-> Cleaned:  candidate@mycompany.org
   Would you like to register 'candidate@mycompany.org' now? (y/N): y
   Successfully registered 'candidate@mycompany.org' in SQLite database!

Enter email: candidate@mycompany.org
-> Result:   Email is already registered
-> Status:   ALREADY_REGISTERED

Enter email: quit
Exiting interactive mode. Goodbye!
```

---

## 4. Running the Automated Pytest Suite

The component comes with **50 automated test checks** testing sanitization, RFC limits, domain structure, duplicate detection, case insensitivity, and SQL injection protection.

Run all tests with verbose output:
```bash
python3 -m pytest -v
```

Run tests with short summary:
```bash
python3 -m pytest -q
# Output: 50 passed in 0.11s
```

Run a specific test category:
```bash
# Test only duplicate/available registration checks:
python3 -m pytest -v -k "TestExistingAndAvailableRegistration"

# Test input sanitization and type handling:
python3 -m pytest -v -k "TestInputSanitizationAndTypes"
```

---

## 5. Integrating with Your Application Code

### Basic Usage in Python

```python
from email_validator import EmailValidator, SQLiteUserRepository

# 1. Initialize user database repository (file-based or in-memory)
repo = SQLiteUserRepository(db_path="users.db", seed_defaults=True)

# 2. Inject repository into validator service
validator = EmailValidator(user_repository=repo)

# 3. Validate user input from registration form
user_input = "  alice@example.com  "
result = validator.validate(user_input)

if not result.is_valid:
    print(f"Error: {result.message}")
elif not result.is_available:
    print(f"Notice: {result.message}")  # "Email is already registered"
else:
    print(f"Success: {result.message}")
    # Proceed to save new user
    repo.register_user(result.normalized_email)
```

### Integration in a Web API (FastAPI / Flask Pattern)

```python
from email_validator import EmailValidator, SQLiteUserRepository, ValidationStatus

# Singleton or dependency-injected instance
repo = SQLiteUserRepository(db_path="users.db")
validator = EmailValidator(user_repository=repo)

def handle_registration_step(raw_email: str):
    result = validator.validate(raw_email)
    
    if result.status == ValidationStatus.INVALID_INPUT:
        return {"status": "error", "code": 400, "detail": result.message}
        
    if result.status == ValidationStatus.INVALID_FORMAT:
        return {"status": "error", "code": 422, "detail": result.message}
        
    if result.status == ValidationStatus.ALREADY_REGISTERED:
        return {"status": "conflict", "code": 409, "message": result.message}
        
    # Valid & Available
    return {
        "status": "ok",
        "code": 200,
        "message": result.message,
        "email": result.normalized_email
    }
```

---

## 6. Input & Expected Output Reference

| Input | Validation Outcome | Returned Message |
|---|:---:|---|
| `somya@example.com` | Duplicate in DB | `Email is already registered` |
| `John@example.com` | Duplicate in DB | `Email is already registered` |
| `JOHN@EXAMPLE.COM` | Duplicate in DB (Case-Insensitive) | `Email is already registered` |
| `Alice@example.com` | Duplicate in DB | `Email is already registered` |
| `newuser@example.com` | Valid & Available | `Email format is valid and email is available for registration.` |
| `"   user@test.org  "` | Stripped & Available | `Email format is valid and email is available for registration.` |
| `None` | Invalid Input | `Invalid input: Email must be a non-empty string.` |
| `""` or `"   "` | Invalid Input | `Invalid input: Email cannot be empty or contain only whitespace.` |
| `user_at_test.com` | Invalid Syntax | `Invalid email format: Missing '@' symbol.` |
| `user@domain` | Invalid Syntax | `Invalid email format: Domain must contain a valid top-level domain...` |
| `user..name@test.com` | Invalid Syntax | `Invalid email format: Local part cannot contain consecutive dots ('..').` |
| `user@test.c` | Invalid Syntax | `Invalid email format: Top-level domain 'c' is invalid (must be alphabetic and at least 2 letters).` |
