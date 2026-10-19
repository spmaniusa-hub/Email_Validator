#!/usr/bin/env python3
"""
demo.py - Interactive & Automated Email Validator Demonstration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Author: Mani Subramanian
Python: 3.11+

Demonstrates:
1. Input sanitization (None, empty, whitespace-padded inputs).
2. Structural syntax verification (RFC rules, '@', domain labels, TLD).
3. SQLite database lookup for registered users.
4. Clean, human-readable feedback for user registration flows.
"""

import sys
from email_validator import EmailValidator, SQLiteUserRepository


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def run_automated_demo() -> None:
    # Initialize repository with default seeded simulation accounts
    # Database is created in a local SQLite file 'users.db' for persistence
    repo = SQLiteUserRepository(db_path="users.db", seed_defaults=True)
    validator = EmailValidator(user_repository=repo)

    print_header("EMAIL VALIDATION COMPONENT - AUTOMATED DEMONSTRATION")
    print(f"Developer: Mani Subramanian")
    print(f"Database Engine: SQLite (users.db)")
    print(f"Registered Users in DB: {repo.get_all_registered_emails()}")

    test_inputs = [
        # --- Assignment Primary Examples ---
        ("somya@example.com", "Primary check: existing user in database"),
        ("newuser@example.com", "Primary check: valid, unregistered email"),

        # --- Case-Insensitive Duplicate Checks ---
        ("JOHN@EXAMPLE.COM", "Case-folding check: uppercase version of John@example.com"),
        ("Alice@example.com", "Case-folding check: mixed case registered user"),

        # --- Whitespace Sanitization ---
        ("   padme@domain.org   ", "Sanitization check: leading & trailing whitespace"),

        # --- Invalid Input Checks ---
        (None, "Type safety: NoneType input"),
        ("", "Emptiness check: empty string"),
        ("     ", "Emptiness check: whitespace-only string"),

        # --- Structural Syntax Failures ---
        ("user_at_domain.com", "Syntax failure: missing '@' symbol"),
        ("user@domain", "Syntax failure: missing dot in domain"),
        ("user..name@domain.com", "Syntax failure: consecutive dots in local-part"),
        ("user@domain.c", "Syntax failure: invalid TLD (must be >= 2 letters)"),
    ]

    print_header("TEST RESULTS TABLE")
    print(f"{'Input Tested':<30} | {'Status':<18} | {'Output Message'}")
    print("-" * 75)

    for raw_input, scenario in test_inputs:
        result = validator.validate(raw_input)
        display_input = str(raw_input) if raw_input is not None else "None"
        if len(display_input) > 28:
            display_input = display_input[:25] + "..."
        print(f"{display_input:<30} | {result.status.value:<18} | {result.message}")

    print("\n" + "-" * 75)
    print("Automated demonstration completed successfully.")


def run_interactive_mode() -> None:
    repo = SQLiteUserRepository(db_path="users.db", seed_defaults=True)
    validator = EmailValidator(user_repository=repo)

    print_header("INTERACTIVE EMAIL VALIDATION MODE")
    print("Type an email address to validate, or 'quit'/'exit' to stop.")
    print(f"Current DB emails: {repo.get_all_registered_emails()}\n")

    while True:
        try:
            user_input = input("Enter email: ")
            if user_input.strip().lower() in ("quit", "exit", "q"):
                print("Exiting interactive mode. Goodbye!")
                break

            result = validator.validate(user_input)
            print(f"-> Result:   {result.message}")
            print(f"-> Status:   {result.status.value}")
            if result.normalized_email:
                print(f"-> Cleaned:  {result.normalized_email}")
            if result.error_detail:
                print(f"-> Detail:   {result.error_detail}")

            # Option to register if available
            if result.is_available:
                register_prompt = input(f"   Would you like to register '{result.normalized_email}' now? (y/N): ")
                if register_prompt.strip().lower() == "y":
                    repo.register_user(result.normalized_email)
                    print(f"   Successfully registered '{result.normalized_email}' in SQLite database!\n")
            print()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-i", "--interactive"):
        run_interactive_mode()
    else:
        run_automated_demo()
        print("\nTip: To run interactive prompt, execute: python3 demo.py --interactive")
