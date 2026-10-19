"""
tests.test_validator
~~~~~~~~~~~~~~~~~~~~

Automated Pytest test suite for EmailValidator and SQLiteUserRepository.
Verifies valid, invalid, empty/None, duplicate, and available email scenarios.

Author: Mani Subramanian
"""

import pytest
from email_validator.validator import EmailValidator
from email_validator.models import ValidationStatus
from email_validator.database import SQLiteUserRepository


class TestInputSanitizationAndTypes:
    """Tests verifying robust handling of non-string, None, empty, and whitespace inputs."""

    def test_none_input_rejected(self, validator: EmailValidator):
        result = validator.validate(None)
        assert not result.is_valid
        assert not result.is_available
        assert result.status == ValidationStatus.INVALID_INPUT
        assert "must be a non-empty string" in result.message

    @pytest.mark.parametrize("invalid_type", [123, 45.67, True, [], {}, object()])
    def test_non_string_types_rejected(self, validator: EmailValidator, invalid_type):
        result = validator.validate(invalid_type)
        assert not result.is_valid
        assert not result.is_available
        assert result.status == ValidationStatus.INVALID_INPUT

    def test_empty_string_rejected(self, validator: EmailValidator):
        result = validator.validate("")
        assert not result.is_valid
        assert not result.is_available
        assert result.status == ValidationStatus.INVALID_INPUT
        assert "cannot be empty" in result.message

    @pytest.mark.parametrize("whitespace_val", ["   ", "\t", "\n\r", "   \t  \n  "])
    def test_whitespace_only_rejected(self, validator: EmailValidator, whitespace_val):
        result = validator.validate(whitespace_val)
        assert not result.is_valid
        assert not result.is_available
        assert result.status == ValidationStatus.INVALID_INPUT

    def test_leading_and_trailing_whitespace_stripped(self, validator: EmailValidator):
        # A valid un-registered email surrounded by spaces should succeed cleanly
        raw = "   newuser@example.com   \n"
        result = validator.validate(raw)
        assert result.is_valid
        assert result.is_available
        assert result.normalized_email == "newuser@example.com"
        assert result.status == ValidationStatus.AVAILABLE


class TestStructuralSyntaxValidation:
    """Tests verifying email syntax: '@' symbol, domain dot, label rules, and TLDs."""

    @pytest.mark.parametrize("missing_at", [
        "plainaddress",
        "newuserexample.com",
        "no_at_symbol.org"
    ])
    def test_missing_at_symbol_rejected(self, validator: EmailValidator, missing_at):
        result = validator.validate(missing_at)
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT
        assert "Missing '@' symbol" in result.message

    def test_multiple_at_symbols_rejected(self, validator: EmailValidator):
        result = validator.validate("first@second@example.com")
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT
        assert "multiple '@' symbols" in result.message

    def test_missing_local_part_rejected(self, validator: EmailValidator):
        result = validator.validate("@example.com")
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT
        assert "Local part" in result.message

    def test_missing_domain_part_rejected(self, validator: EmailValidator):
        result = validator.validate("user@")
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT
        assert "Domain part" in result.message

    @pytest.mark.parametrize("no_dot_domain", [
        "user@localhost",
        "user@com",
        "user@internaldomain"
    ])
    def test_missing_dot_in_domain_rejected(self, validator: EmailValidator, no_dot_domain):
        result = validator.validate(no_dot_domain)
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT
        assert "must contain a valid top-level domain" in result.message

    @pytest.mark.parametrize("invalid_dots", [
        ".user@example.com",       # Leading dot in local
        "user.@example.com",       # Trailing dot in local
        "user..name@example.com",   # Consecutive dots in local
        "user@.example.com",       # Leading dot in domain
        "user@example.com.",       # Trailing dot in domain
        "user@example..com",       # Consecutive dots in domain
    ])
    def test_improper_dot_placement_rejected(self, validator: EmailValidator, invalid_dots):
        result = validator.validate(invalid_dots)
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT

    @pytest.mark.parametrize("invalid_tld", [
        "user@example.c",          # 1 letter TLD
        "user@example.123",        # Numeric TLD
        "user@example.c-m",        # Hyphenated TLD
    ])
    def test_invalid_tld_rejected(self, validator: EmailValidator, invalid_tld):
        result = validator.validate(invalid_tld)
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID_FORMAT
        assert "Top-level domain" in result.message

    def test_rfc_maximum_total_length_exceeded(self, validator: EmailValidator):
        # RFC 5321 max total length is 254 chars
        long_local = "a" * 60
        long_domain = ("sub." * 50) + "example.com"  # 50*4 + 11 = 211; total = 60 + 1 + 211 = 272 (> 254)
        long_email = f"{long_local}@{long_domain}"
        result = validator.validate(long_email)
        assert not result.is_valid
        assert "Total length exceeds" in result.message

    def test_rfc_maximum_local_part_length_exceeded(self, validator: EmailValidator):
        # RFC 5321 max local-part is 64 chars
        too_long_local = ("a" * 65) + "@example.com"
        result = validator.validate(too_long_local)
        assert not result.is_valid
        assert "Local part exceeds maximum length" in result.message


class TestExistingAndAvailableRegistration:
    """Tests verifying database duplicate checks against the seeded SQLite database."""

    @pytest.mark.parametrize("existing_email", [
        "somya@example.com",
        "John@example.com",
        "Alice@example.com",
    ])
    def test_seeded_emails_reported_as_already_registered(
        self, validator: EmailValidator, existing_email: str
    ):
        result = validator.validate(existing_email)
        assert result.is_valid, "A registered email has valid formatting"
        assert not result.is_available, "A registered email is not available"
        assert result.status == ValidationStatus.ALREADY_REGISTERED
        # Required exact prompt phrase
        assert result.message == "Email is already registered"

    @pytest.mark.parametrize("case_variant", [
        "SOMYA@EXAMPLE.COM",
        "Somya@Example.Com",
        "john@example.com",
        "JOHN@EXAMPLE.COM",
        "alice@example.com",
        "ALICE@EXAMPLE.COM",
    ])
    def test_case_insensitive_duplicate_check(
        self, validator: EmailValidator, case_variant: str
    ):
        result = validator.validate(case_variant)
        assert result.is_valid
        assert not result.is_available
        assert result.status == ValidationStatus.ALREADY_REGISTERED
        assert result.message == "Email is already registered"

    @pytest.mark.parametrize("available_email", [
        "newuser@example.com",
        "jane.doe+dev@techcorp.io",
        "lead-architect@cloud-native.org",
        "support@subdomain.example.co.uk",
    ])
    def test_available_unregistered_email(
        self, validator: EmailValidator, available_email: str
    ):
        result = validator.validate(available_email)
        assert result.is_valid
        assert result.is_available
        assert result.status == ValidationStatus.AVAILABLE
        # Required exact prompt phrase
        assert result.message == "Email format is valid and email is available for registration."
        assert result.can_proceed_to_registration is True

    def test_lifecycle_validate_then_register_then_duplicate(
        self, validator: EmailValidator, in_memory_db: SQLiteUserRepository
    ):
        """Simulate the end-to-end user registration lifecycle."""
        email = "candidate@startup.io"

        # 1. First check: should be available
        initial_check = validator.validate(email)
        assert initial_check.is_available
        assert initial_check.message == "Email format is valid and email is available for registration."

        # 2. Register the candidate
        registered = in_memory_db.register_user(email)
        assert registered is True

        # 3. Second check: should now report already registered
        second_check = validator.validate(email)
        assert not second_check.is_available
        assert second_check.status == ValidationStatus.ALREADY_REGISTERED
        assert second_check.message == "Email is already registered"


class TestDatabaseDirectOperations:
    """Direct tests for the SQLiteUserRepository component."""

    def test_default_seeded_emails_count(self, in_memory_db: SQLiteUserRepository):
        emails = in_memory_db.get_all_registered_emails()
        assert len(emails) == 3
        assert "somya@example.com" in emails

    def test_duplicate_registration_returns_false(self, in_memory_db: SQLiteUserRepository):
        # somya is already in DB
        res = in_memory_db.register_user("somya@example.com")
        assert res is False

    def test_sql_injection_attempt_is_safely_parameterized(
        self, in_memory_db: SQLiteUserRepository
    ):
        malicious_input = "hacker@example.com'; DROP TABLE users; --"
        # Parameterized query handles malicious input literally without executing SQL
        is_reg = in_memory_db.is_registered(malicious_input)
        assert is_reg is False

        # Verify users table is intact
        emails = in_memory_db.get_all_registered_emails()
        assert len(emails) >= 3
