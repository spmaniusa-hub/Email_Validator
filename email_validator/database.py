"""
email_validator.database
~~~~~~~~~~~~~~~~~~~~~~~~

Database access layer for user email lookups using SQLite.
Implements the Repository Pattern to decouple storage from validation logic.

Author: Mani Subramanian
"""

from __future__ import annotations

import sqlite3
from typing import Protocol, Sequence, Optional
from contextlib import contextmanager


class UserRepository(Protocol):
    """Abstract interface defining the user storage contract."""

    def is_registered(self, email: str) -> bool:
        """Return True if the email already exists in the registered database."""
        ...

    def register_user(self, email: str) -> bool:
        """Register a new email into the database."""
        ...


class SQLiteUserRepository:
    """
    Production-conscious SQLite implementation of UserRepository.

    Features:
    - Case-insensitive email index (COLLATE NOCASE) for O(1) lookups.
    - Strict parameterized queries to eliminate SQL injection vulnerabilities.
    - Connection pooling/isolation friendly (supports file-based or :memory: paths).
    - Automatic seeding of initial demonstration users.
    """

    DEFAULT_SEEDED_EMAILS: Sequence[str] = (
        "somya@example.com",
        "John@example.com",
        "Alice@example.com",
    )

    def __init__(self, db_path: str = ":memory:", seed_defaults: bool = True) -> None:
        """
        Initialize the SQLite connection and schema.

        Args:
            db_path: Path to SQLite database file, or ':memory:' for isolated testing.
            seed_defaults: If True, populates initial sample users for demonstration.
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._init_db(seed_defaults)

    def _get_connection(self) -> sqlite3.Connection:
        """Manage and return active database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _init_db(self, seed_defaults: bool) -> None:
        """Create users table with unique case-insensitive email constraints."""
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            # Create an explicit index on email for O(1) indexed lookups
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_email
                ON users(email COLLATE NOCASE);
                """
            )

        if seed_defaults:
            self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Insert the baseline simulation users if they do not already exist."""
        conn = self._get_connection()
        with conn:
            for email in self.DEFAULT_SEEDED_EMAILS:
                conn.execute(
                    "INSERT OR IGNORE INTO users (email) VALUES (?);",
                    (email.strip(),)
                )

    def is_registered(self, email: str) -> bool:
        """
        Check whether an email address is already registered.

        Safe against SQL injection using parameterized queries with case-folding.
        """
        if not email:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()
        # Parameterized query protects against injection attacks
        cursor.execute(
            "SELECT 1 FROM users WHERE email = ? COLLATE NOCASE LIMIT 1;",
            (email.strip(),)
        )
        row = cursor.fetchone()
        return row is not None

    def register_user(self, email: str) -> bool:
        """
        Register a new email into the database.

        Returns:
            True if registration succeeded, False if already registered or invalid.
        """
        if not email:
            return False

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (email) VALUES (?);",
                    (email.strip(),)
                )
            return True
        except sqlite3.IntegrityError:
            # Duplicate key violation (email already registered)
            return False

    def get_all_registered_emails(self) -> list[str]:
        """Return a list of all registered emails (sanitized / fictional)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users ORDER BY id ASC;")
        return [row["email"] for row in cursor.fetchall()]

    def close(self) -> None:
        """Close connection cleanly."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SQLiteUserRepository":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
