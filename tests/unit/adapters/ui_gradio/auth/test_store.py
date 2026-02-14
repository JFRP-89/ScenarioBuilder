"""Unit tests — in-memory auth store (users, hashing, lockout)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from adapters.ui_gradio.auth._store import (
    LOCKOUT_DURATION,
    MAX_FAILED_ATTEMPTS,
    clear_failed_attempts,
    get_user_profile,
    is_locked,
    record_failed_attempt,
    reset_stores,
    update_user_profile,
    user_exists,
    verify_credentials,
)
from infrastructure.auth.user_store import (
    _hash_password,
    _verify_password,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset stores before each test."""
    reset_stores()
    yield
    reset_stores()


# =====================================================================
# Hashing helpers
# =====================================================================
class TestPasswordHashing:
    """PBKDF2 hashing must be deterministic given same salt."""

    def test_hash_produces_bytes(self):
        pw_hash, salt = _hash_password("password")
        assert isinstance(pw_hash, bytes)
        assert isinstance(salt, bytes)
        assert len(pw_hash) == 32
        assert len(salt) == 32

    def test_same_password_different_salt_produces_different_hash(self):
        h1, s1 = _hash_password("password")
        h2, s2 = _hash_password("password")
        # Different salts → different hashes
        assert s1 != s2
        assert h1 != h2

    def test_verify_correct_password(self):
        pw_hash, salt = _hash_password("secret")
        assert _verify_password("secret", pw_hash, salt) is True

    def test_verify_wrong_password(self):
        pw_hash, salt = _hash_password("secret")
        assert _verify_password("wrong", pw_hash, salt) is False


# =====================================================================
# Demo users
# =====================================================================
class TestDemoUsers:
    """Demo users must be seeded on import."""

    @pytest.mark.parametrize(
        "username",
        ["demo-user", "alice", "bob", "charlie", "dave"],
    )
    def test_demo_user_exists(self, username: str):
        assert user_exists(username) is True

    def test_unknown_user_does_not_exist(self):
        assert user_exists("unknown-user") is False

    @pytest.mark.parametrize(
        "username",
        ["demo-user", "alice", "bob", "charlie", "dave"],
    )
    def test_demo_password_equals_username(self, username: str):
        assert verify_credentials(username, username) is True

    def test_wrong_password_rejected(self):
        assert verify_credentials("alice", "wrong") is False

    def test_unknown_user_rejected(self):
        assert verify_credentials("no-such-user", "password") is False


# =====================================================================
# Profiles
# =====================================================================
class TestProfiles:
    """Profile CRUD for demo users."""

    def test_get_profile_returns_data(self):
        profile = get_user_profile("alice")
        assert profile is not None
        assert profile["username"] == "alice"
        assert profile["name"] == "Alice"
        assert profile["email"] == "alice@example.com"

    def test_get_profile_unknown_returns_none(self):
        assert get_user_profile("unknown") is None

    def test_update_profile(self):
        assert update_user_profile("bob", "Bobby", "bobby@test.org") is True
        profile = get_user_profile("bob")
        assert profile is not None
        assert profile["name"] == "Bobby"
        assert profile["email"] == "bobby@test.org"

    def test_update_profile_unknown_user_returns_false(self):
        assert update_user_profile("unknown", "X", "x@x.com") is False

    @pytest.mark.parametrize(
        "username",
        ["demo-user", "alice", "bob", "charlie", "dave"],
    )
    def test_demo_users_have_valid_emails(self, username: str):
        profile = get_user_profile(username)
        assert profile is not None
        assert "@" in profile["email"]
        assert "." in profile["email"].split("@")[1]


# =====================================================================
# Lockout
# =====================================================================
class TestLockout:
    """Brute-force lockout after MAX_FAILED_ATTEMPTS."""

    def test_not_locked_initially(self):
        locked, until = is_locked("alice")
        assert locked is False
        assert until is None

    def test_three_failures_trigger_lockout(self):
        for _ in range(MAX_FAILED_ATTEMPTS - 1):
            locked, _ = record_failed_attempt("alice")
            assert locked is False

        locked, until = record_failed_attempt("alice")
        assert locked is True
        assert until is not None
        assert until > datetime.now(timezone.utc)

    def test_lockout_duration_is_one_hour(self):
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_attempt("alice")

        locked, until = is_locked("alice")
        assert locked is True
        assert until is not None
        expected_min = (
            datetime.now(timezone.utc) + LOCKOUT_DURATION - timedelta(seconds=5)
        )
        assert until >= expected_min

    def test_clear_failed_attempts_resets(self):
        for _ in range(2):
            record_failed_attempt("alice")
        clear_failed_attempts("alice")

        locked, _ = is_locked("alice")
        assert locked is False

    def test_lockout_expires(self):
        """After lockout expires, is_locked returns False."""
        from unittest.mock import patch

        # Lock the user
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_attempt("alice")

        locked, _ = is_locked("alice")
        assert locked is True

        # Fast-forward past lockout
        future = datetime.now(timezone.utc) + LOCKOUT_DURATION + timedelta(seconds=1)
        with patch(
            "infrastructure.auth.user_store.datetime",
        ) as mock_dt:
            mock_dt.now.return_value = future
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            locked, _ = is_locked("alice")
            assert locked is False

    def test_lockout_applies_to_unknown_users(self):
        """Lockout counters work for any username (anti-enumeration)."""
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_attempt("nonexistent-user")
        locked, _ = is_locked("nonexistent-user")
        assert locked is True
