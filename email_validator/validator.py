"""
email_validator.validator
~~~~~~~~~~~~~~~~~~~~~~~~~

Core email validation service implementing syntactic verification,
sanitization, and database availability lookups.

Author: Mani Subramanian
"""

from __future__ import annotations

import re
from typing import Any, Optional, Tuple

from email_validator.models import ValidationResult, ValidationStatus
from email_validator.database import UserRepository, SQLiteUserRepository


class EmailValidator:
    """
    Enterprise-ready email validation service.

    Orchestrates:
    1. Input type & emptiness verification (handling None, non-string, whitespace).
    2. Whitespace trimming and RFC 5321 length enforcement.
    3. Syntactic structure analysis (local-part, '@', domain labels, TLD).
    4. Canonical normalization (case-folding).
    5. Database uniqueness check via UserRepository.
    """

    # RFC 5321 length limits
    MAX_TOTAL_LENGTH = 254
    MAX_LOCAL_LENGTH = 64
    MAX_DOMAIN_LENGTH = 255

    # Local-part characters allowed according to standard practical email rules
    LOCAL_PART_REGEX = re.compile(r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+$")

    # Domain label format (alphanumeric and hyphens, no leading/trailing hyphens)
    DOMAIN_LABEL_REGEX = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")

    # TLD must be alphabetic and at least 2 characters
    TLD_REGEX = re.compile(r"^[a-zA-Z]{2,63}$")

    def __init__(self, user_repository: Optional[UserRepository] = None) -> None:
        """
        Initialize EmailValidator with a user repository.

        Args:
            user_repository: Repository conforming to UserRepository protocol.
                             Defaults to in-memory SQLiteUserRepository if None.
        """
        self.user_repository: UserRepository = (
            user_repository if user_repository is not None else SQLiteUserRepository()
        )

    def validate(self, email: Any) -> ValidationResult:
        """
        Validate an email address against syntax rules and check registration status.

        Args:
            email: Raw input provided by the user.

        Returns:
            ValidationResult with detailed status, message, and normalization.
        """
        # Step 1: Validate input type
        if email is None or not isinstance(email, str):
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message="Invalid input: Email must be a non-empty string.",
                status=ValidationStatus.INVALID_INPUT,
                error_detail=f"Expected str, received {type(email).__name__}."
            )

        # Step 2: Trim leading and trailing whitespace
        cleaned = email.strip()
        if not cleaned:
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message="Invalid input: Email cannot be empty or contain only whitespace.",
                status=ValidationStatus.INVALID_INPUT,
                error_detail="Empty string after trimming whitespace."
            )

        # Step 3: Check overall length constraints (RFC 5321)
        if len(cleaned) > self.MAX_TOTAL_LENGTH:
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message=f"Invalid email format: Total length exceeds {self.MAX_TOTAL_LENGTH} characters.",
                status=ValidationStatus.INVALID_FORMAT,
                error_detail=f"Length {len(cleaned)} exceeds limit {self.MAX_TOTAL_LENGTH}."
            )

        # Step 4: Verify single '@' separator
        at_count = cleaned.count("@")
        if at_count == 0:
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message="Invalid email format: Missing '@' symbol.",
                status=ValidationStatus.INVALID_FORMAT,
                error_detail="No '@' symbol present."
            )
        if at_count > 1:
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message="Invalid email format: Contains multiple '@' symbols.",
                status=ValidationStatus.INVALID_FORMAT,
                error_detail=f"Found {at_count} '@' symbols."
            )

        local_part, domain_part = cleaned.split("@")

        # Step 5: Validate local-part syntax
        local_valid, local_error = self._validate_local_part(local_part)
        if not local_valid:
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message=f"Invalid email format: {local_error}",
                status=ValidationStatus.INVALID_FORMAT,
                error_detail=local_error
            )

        # Step 6: Validate domain-part syntax
        domain_valid, domain_error = self._validate_domain_part(domain_part)
        if not domain_valid:
            return ValidationResult(
                is_valid=False,
                is_available=False,
                message=f"Invalid email format: {domain_error}",
                status=ValidationStatus.INVALID_FORMAT,
                error_detail=domain_error
            )

        # Step 7: Canonical normalization
        # In modern infrastructure, domain names are strictly case-insensitive,
        # and standard email handling treats user registration emails uniformly.
        normalized = f"{local_part}@{domain_part.lower()}"

        # Step 8: Database registration lookup
        if self.user_repository.is_registered(normalized):
            return ValidationResult(
                is_valid=True,
                is_available=False,
                message="Email is already registered",
                status=ValidationStatus.ALREADY_REGISTERED,
                normalized_email=normalized
            )

        return ValidationResult(
            is_valid=True,
            is_available=True,
            message="Email format is valid and email is available for registration.",
            status=ValidationStatus.AVAILABLE,
            normalized_email=normalized
        )

    def _validate_local_part(self, local_part: str) -> Tuple[bool, Optional[str]]:
        """Validate the local username portion preceding '@'."""
        if not local_part:
            return False, "Local part before '@' cannot be empty."

        if len(local_part) > self.MAX_LOCAL_LENGTH:
            return False, f"Local part exceeds maximum length of {self.MAX_LOCAL_LENGTH} characters."

        # Dot placement rules: cannot start/end with dot, no consecutive dots
        if local_part.startswith("."):
            return False, "Local part cannot begin with a dot ('.')."
        if local_part.endswith("."):
            return False, "Local part cannot end with a dot ('.')."
        if ".." in local_part:
            return False, "Local part cannot contain consecutive dots ('..')."

        # Allowed characters check
        if not self.LOCAL_PART_REGEX.match(local_part):
            return False, "Local part contains invalid characters."

        return True, None

    def _validate_domain_part(self, domain_part: str) -> Tuple[bool, Optional[str]]:
        """Validate the domain portion following '@'."""
        if not domain_part:
            return False, "Domain part after '@' cannot be empty."

        if len(domain_part) > self.MAX_DOMAIN_LENGTH:
            return False, f"Domain part exceeds maximum length of {self.MAX_DOMAIN_LENGTH} characters."

        # Domain must contain at least one dot separating name from TLD
        if "." not in domain_part:
            return False, "Domain must contain a valid top-level domain (e.g. '.com', '.org')."

        if domain_part.startswith("."):
            return False, "Domain cannot begin with a dot ('.')."
        if domain_part.endswith("."):
            return False, "Domain cannot end with a dot ('.')."
        if ".." in domain_part:
            return False, "Domain cannot contain consecutive dots ('..')."

        labels = domain_part.split(".")
        if len(labels) < 2:
            return False, "Domain must have at least two labels separated by a dot."

        # Validate each subdomain/domain label
        for label in labels[:-1]:
            if not label:
                return False, "Domain contains an empty label."
            if not self.DOMAIN_LABEL_REGEX.match(label):
                return False, f"Domain label '{label}' is invalid (must be alphanumeric and not start/end with hyphens)."

        # Validate Top-Level Domain (TLD)
        tld = labels[-1]
        if not self.TLD_REGEX.match(tld):
            return False, f"Top-level domain '{tld}' is invalid (must be alphabetic and at least 2 letters)."

        return True, None
