"""Integration tests for user database seeding.

Tests the seed_demo_users_to_database() function that populates the users
table with demo users after the application boots.

Requires a running PostgreSQL instance (``RUN_DB_TESTS=1``).
"""

import pytest

pytestmark = pytest.mark.db


@pytest.fixture
def clean_users_table():
    """Fixture to clean the users table before each test."""
    from infrastructure.db.models import UserModel
    from infrastructure.db.session import SessionLocal
    from sqlalchemy import delete

    session = SessionLocal()
    try:
        session.execute(delete(UserModel))
        session.commit()
    finally:
        session.close()
    yield
    # Cleanup after test
    session = SessionLocal()
    try:
        session.execute(delete(UserModel))
        session.commit()
    finally:
        session.close()


class TestUserSeeding:
    """Tests for demo user database seeding."""

    def test_seed_demo_users_creates_five_users(self, clean_users_table):
        """Test that seeding creates exactly 5 demo users."""
        from infrastructure.auth.user_store import seed_demo_users_to_database
        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal

        seed_demo_users_to_database()

        session = SessionLocal()
        try:
            users = session.query(UserModel).all()
            assert len(users) == 5, "Should create exactly 5 demo users"
        finally:
            session.close()

    def test_seed_demo_users_idempotent(self, clean_users_table):
        """Test that seeding is idempotent (running twice doesn't duplicate)."""
        from infrastructure.auth.user_store import seed_demo_users_to_database
        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal

        seed_demo_users_to_database()
        seed_demo_users_to_database()

        session = SessionLocal()
        try:
            users = session.query(UserModel).all()
            assert len(users) == 5, "Should still have 5 users after second seed"
        finally:
            session.close()

    def test_seed_demo_users_correct_data(self, clean_users_table):
        """Test that seeded users have correct data."""
        from infrastructure.auth.user_store import seed_demo_users_to_database
        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal

        seed_demo_users_to_database()

        session = SessionLocal()
        try:
            expected = {
                "demo-user": {"name": "Demo User", "email": "demo@example.com"},
                "alice": {"name": "Alice", "email": "alice@example.com"},
                "bob": {"name": "Bob", "email": "bob@example.com"},
                "charlie": {"name": "Charlie", "email": "charlie@example.com"},
                "dave": {"name": "Dave", "email": "dave@example.com"},
            }

            for username, expected_data in expected.items():
                user = session.query(UserModel).filter_by(username=username).first()
                assert user is not None, f"User {username} should exist"
                assert user.name == expected_data["name"]
                assert user.email == expected_data["email"]
                assert user.password_hash is not None, "Password hash should be set"
                assert user.salt is not None, "Salt should be set"
        finally:
            session.close()

    def test_seed_demo_users_passwords_preserved(self, clean_users_table):
        """Test that seeded user passwords match in-memory store."""
        from infrastructure.auth.user_store import (
            _USERS,
            seed_demo_users_to_database,
        )
        from infrastructure.db.models import UserModel
        from infrastructure.db.session import SessionLocal

        seed_demo_users_to_database()

        session = SessionLocal()
        try:
            for username in _USERS:
                db_user = session.query(UserModel).filter_by(username=username).first()
                assert db_user is not None, f"User {username} should exist in DB"

                # Verify password_hash and salt match in-memory store
                in_memory = _USERS[username]
                assert db_user.password_hash == in_memory["password_hash"]
                assert db_user.salt == in_memory["salt"]
        finally:
            session.close()
