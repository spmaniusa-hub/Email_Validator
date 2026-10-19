"""
email_validator package
~~~~~~~~~~~~~~~~~~~~~~~

Production-conscious email validation and availability check component.
Author: Mani Subramanian
"""

from email_validator.models import ValidationResult, ValidationStatus
from email_validator.database import UserRepository, SQLiteUserRepository
from email_validator.validator import EmailValidator

__all__ = [
    "EmailValidator",
    "ValidationResult",
    "ValidationStatus",
    "UserRepository",
    "SQLiteUserRepository",
]

__version__ = "1.0.0"
__author__ = "Mani Subramanian"
