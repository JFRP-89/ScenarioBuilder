"""Unit tests for user_store.create_user and registration in auth_service."""

from __future__ import annotations

import pytest
from infrastructure.auth import auth_service, session_store, user_store


@pytest.fixture(autouse=True)
def _clean():
    """Reset all stores before each test."""
    session_store.reset_sessions()
    user_store.reset_stores()
    yield
    session_store.reset_sessions()
    user_store.reset_stores()


# ── create_user (user_store) ─────────────────────────────────────────────────


class TestCreateUser:
    def test_create_new_user(self):
        ok = user_store.create_user("newuser", "Str0ng!pw", "New User", "new@ex.com")
        assert ok is True
        assert user_store.user_exists("newuser")

    def test_create_user_can_login(self):
        user_store.create_user("newuser", "Str0ng!pw", "New User", "new@ex.com")
        assert user_store.verify_credentials("newuser", "Str0ng!pw") is True

    def test_create_user_wrong_password_fails(self):
        user_store.create_user("newuser", "Str0ng!pw", "New User", "new@ex.com")
        assert user_store.verify_credentials("newuser", "wrong") is False

    def test_create_duplicate_returns_false(self):
        user_store.create_user("newuser", "Str0ng!pw", "New User", "new@ex.com")
        ok = user_store.create_user("newuser", "Other!pw1", "Dup", "dup@ex.com")
        assert ok is False

    def test_create_user_profile(self):
        user_store.create_user("newuser", "Str0ng!pw", "New User", "new@ex.com")
        profile = user_store.get_user_profile("newuser")
        assert profile is not None
        assert profile["username"] == "newuser"
        assert profile["name"] == "New User"
        assert profile["email"] == "new@ex.com"

    def test_cannot_overwrite_demo_user(self):
        ok = user_store.create_user("alice", "Str0ng!pw", "Fake", "fake@ex.com")
        assert ok is False
        # Original demo user should still work
        assert user_store.verify_credentials("alice", "alice") is True


# ── register (auth_service) ─────────────────────────────────────────────────


class TestRegister:
    def test_success(self):
        result = auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Str0ng!pw",
            "New User",
            "new@ex.com",
        )
        assert result["ok"] is True
        assert result["actor_id"] == "newuser"
        assert "session_id" in result
        assert "csrf_token" in result

    def test_auto_login_session_valid(self):
        result = auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Str0ng!pw",
            "",
            "",
        )
        session = session_store.get_session(str(result["session_id"]))
        assert session is not None
        assert session["actor_id"] == "newuser"

    def test_invalid_username_format(self):
        result = auth_service.register(
            "AB",
            "Str0ng!pw",
            "Str0ng!pw",
            "",
            "",
        )
        assert result["ok"] is False
        assert "errors" in result

    def test_weak_password_missing_uppercase(self):
        result = auth_service.register(
            "newuser",
            "weak1234!",
            "weak1234!",
            "",
            "",
        )
        assert result["ok"] is False
        assert any("uppercase" in str(e) for e in result["errors"])  # type: ignore[attr-defined]

    def test_weak_password_missing_digit(self):
        result = auth_service.register(
            "newuser",
            "Weakpass!",
            "Weakpass!",
            "",
            "",
        )
        assert result["ok"] is False
        assert any("digit" in str(e) for e in result["errors"])  # type: ignore[attr-defined]

    def test_weak_password_missing_special(self):
        result = auth_service.register(
            "newuser",
            "Weakpass1",
            "Weakpass1",
            "",
            "",
        )
        assert result["ok"] is False
        assert any("special" in str(e) for e in result["errors"])  # type: ignore[attr-defined]

    def test_weak_password_too_short(self):
        result = auth_service.register(
            "newuser",
            "Ab1!",
            "Ab1!",
            "",
            "",
        )
        assert result["ok"] is False
        assert any("8 characters" in str(e) for e in result["errors"])  # type: ignore[attr-defined]

    def test_password_mismatch(self):
        result = auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Different1!",
            "",
            "",
        )
        assert result["ok"] is False
        assert any("match" in str(e) for e in result["errors"])  # type: ignore[attr-defined]

    def test_duplicate_username(self):
        result = auth_service.register(
            "alice",
            "Str0ng!pw",
            "Str0ng!pw",
            "",
            "",
        )
        assert result["ok"] is False
        assert "taken" in str(result["message"])

    def test_invalid_email_format(self):
        result = auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Str0ng!pw",
            "",
            "not-email",
        )
        assert result["ok"] is False
        assert any("email" in str(e).lower() for e in result["errors"])  # type: ignore[attr-defined]

    def test_valid_email_accepted(self):
        result = auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Str0ng!pw",
            "Name",
            "good@example.com",
        )
        assert result["ok"] is True

    def test_empty_email_accepted(self):
        result = auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Str0ng!pw",
            "",
            "",
        )
        assert result["ok"] is True

    def test_name_defaults_to_username(self):
        auth_service.register("newuser", "Str0ng!pw", "Str0ng!pw", "", "")
        profile = user_store.get_user_profile("newuser")
        assert profile is not None
        assert profile["name"] == "newuser"

    def test_name_preserved_when_provided(self):
        auth_service.register(
            "newuser",
            "Str0ng!pw",
            "Str0ng!pw",
            "John Doe",
            "",
        )
        profile = user_store.get_user_profile("newuser")
        assert profile is not None
        assert profile["name"] == "John Doe"

    def test_multiple_validation_errors(self):
        """Bad username + bad password + mismatch → multiple errors."""
        result = auth_service.register(
            "X",
            "short",
            "different",
            "",
            "",
        )
        assert result["ok"] is False
        errors = result["errors"]
        assert isinstance(errors, list)
        assert len(errors) >= 3  # username + password issues + mismatch


# ── check_username_available ─────────────────────────────────────────────────


class TestCheckUsernameAvailable:
    def test_available(self):
        result = auth_service.check_username_available("brand-new")
        assert result["available"] is True

    def test_taken(self):
        result = auth_service.check_username_available("alice")
        assert result["available"] is False
        assert "taken" in str(result["message"])

    def test_invalid_format(self):
        result = auth_service.check_username_available("AB")
        assert result["available"] is False
