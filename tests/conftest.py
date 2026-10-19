"""
tests.conftest
~~~~~~~~~~~~~~

Pytest configuration and shared fixtures for email validation tests.
Author: Mani Subramanian
"""

import pytest
from email_validator.database import SQLiteUserRepository
from email_validator.validator import EmailValidator


@pytest.fixture
def in_memory_db() -> SQLiteUserRepository:
    """Fixture providing an isolated, seeded in-memory SQLite database for each test."""
    repo = SQLiteUserRepository(db_path=":memory:", seed_defaults=True)
    yield repo
    repo.close()


@pytest.fixture
def empty_db() -> SQLiteUserRepository:
    """Fixture providing an empty in-memory SQLite database without default seeds."""
    repo = SQLiteUserRepository(db_path=":memory:", seed_defaults=False)
    yield repo
    repo.close()


@pytest.fixture
def validator(in_memory_db: SQLiteUserRepository) -> EmailValidator:
    """Fixture providing a fresh EmailValidator wired to the in-memory test database."""
    return EmailValidator(user_repository=in_memory_db)
