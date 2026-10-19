"""
email_validator.models
~~~~~~~~~~~~~~~~~~~~~~

Data models and status enumerations for email validation results.
Author: Mani Subramanian
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationStatus(str, Enum):
    """Enumeration representing the categorical outcome of an email validation check."""
    AVAILABLE = "AVAILABLE"
    ALREADY_REGISTERED = "ALREADY_REGISTERED"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable representation of an email validation outcome.

    Attributes:
        is_valid: True if the email syntax is strictly valid and usable.
        is_available: True if the email is both structurally valid and not yet registered.
        message: Human-readable message suitable for user display.
        status: Strongly-typed ValidationStatus enum.
        normalized_email: Cleaned, normalized email string (if format was valid).
        error_detail: Technical explanation of the failure (if invalid), useful for logs.
    """
    is_valid: bool
    is_available: bool
    message: str
    status: ValidationStatus
    normalized_email: Optional[str] = None
    error_detail: Optional[str] = None

    def __str__(self) -> str:
        return self.message

    @property
    def can_proceed_to_registration(self) -> bool:
        """Helper for downstream registration workflows."""
        return self.is_valid and self.is_available
