"""Unit tests for password change via user_store and auth_service.update_profile."""

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


# ── change_password (user_store) ─────────────────────────────────────────────


class TestChangePassword:
    """Tests for ``user_store.change_password``."""

    def test_change_password_success(self):
        user_store.create_user("newuser", "Str0ng!pw", "User", "u@ex.com")
        ok = user_store.change_password("newuser", "NewStr0ng!pw")
        assert ok is True

    def test_new_password_verifies(self):
        user_store.create_user("newuser", "Str0ng!pw", "User", "u@ex.com")
        user_store.change_password("newuser", "NewStr0ng!pw")
        assert user_store.verify_credentials("newuser", "NewStr0ng!pw") is True

    def test_old_password_no_longer_works(self):
        user_store.create_user("newuser", "Str0ng!pw", "User", "u@ex.com")
        user_store.change_password("newuser", "NewStr0ng!pw")
        assert user_store.verify_credentials("newuser", "Str0ng!pw") is False

    def test_nonexistent_user_returns_false(self):
        ok = user_store.change_password("ghost", "NewStr0ng!pw")
        assert ok is False

    def test_change_demo_user_password(self):
        """Demo users can also change their password."""
        ok = user_store.change_password("alice", "Alice_New!1")
        assert ok is True
        assert user_store.verify_credentials("alice", "Alice_New!1") is True
        assert user_store.verify_credentials("alice", "alice") is False

    def test_change_password_twice(self):
        user_store.create_user("newuser", "Str0ng!pw", "User", "u@ex.com")
        user_store.change_password("newuser", "Second!pw1")
        user_store.change_password("newuser", "Third!pw11")
        assert user_store.verify_credentials("newuser", "Third!pw11") is True
        assert user_store.verify_credentials("newuser", "Second!pw1") is False

    def test_profile_unchanged_after_password_change(self):
        user_store.create_user("newuser", "Str0ng!pw", "User", "u@ex.com")
        user_store.change_password("newuser", "NewStr0ng!pw")
        profile = user_store.get_user_profile("newuser")
        assert profile is not None
        assert profile["name"] == "User"
        assert profile["email"] == "u@ex.com"


# ── update_profile with password (auth_service) ────────────────────────────


class TestUpdateProfilePasswordChange:
    """Tests for ``auth_service.update_profile`` password change flow."""

    def _login_alice(self) -> str:
        """Authenticate alice and return session_id."""
        res = auth_service.authenticate("alice", "alice")
        return str(res["session_id"])

    def test_empty_passwords_no_change(self):
        sid = self._login_alice()
        result = auth_service.update_profile(sid, "Alice", "alice@example.com")
        assert result["ok"] is True
        assert result["message"] == "Profile updated."
        # Old password still works
        assert user_store.verify_credentials("alice", "alice") is True

    def test_empty_strings_no_change(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "",
            "",
        )
        assert result["ok"] is True
        assert result["message"] == "Profile updated."

    def test_password_change_success(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is True
        assert result["message"] == "Profile and password updated."
        assert user_store.verify_credentials("alice", "NewStr0ng!1") is True
        assert user_store.verify_credentials("alice", "alice") is False

    def test_password_mismatch(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "NewStr0ng!1",
            "Different!1",
        )
        assert result["ok"] is False
        assert "match" in str(result["message"]).lower()
        # Password should NOT have changed
        assert user_store.verify_credentials("alice", "alice") is True

    def test_weak_password_too_short(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "Ab1!",
            "Ab1!",
        )
        assert result["ok"] is False
        assert "8" in str(result["message"])
        assert user_store.verify_credentials("alice", "alice") is True

    def test_weak_password_no_uppercase(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "weak1234!",
            "weak1234!",
        )
        assert result["ok"] is False
        assert "uppercase" in str(result["message"]).lower()

    def test_weak_password_no_digit(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "Weakpass!",
            "Weakpass!",
        )
        assert result["ok"] is False
        assert "digit" in str(result["message"]).lower()

    def test_weak_password_no_special(self):
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "Weakpass1",
            "Weakpass1",
        )
        assert result["ok"] is False
        assert "special" in str(result["message"]).lower()

    def test_only_new_password_filled(self):
        """Only new_password set → mismatch because confirm is empty."""
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "NewStr0ng!1",
            "",
        )
        assert result["ok"] is False
        assert "match" in str(result["message"]).lower()

    def test_only_confirm_filled(self):
        """Only confirm set → mismatch because new_password is empty."""
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "alice@example.com",
            "",
            "NewStr0ng!1",
        )
        assert result["ok"] is False
        assert "match" in str(result["message"]).lower()

    def test_password_change_with_profile_update(self):
        """Both profile fields and password change at once."""
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice New",
            "alice_new@example.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is True
        assert result["message"] == "Profile and password updated."
        profile = user_store.get_user_profile("alice")
        assert profile is not None
        assert profile["name"] == "Alice New"
        assert profile["email"] == "alice_new@example.com"
        assert user_store.verify_credentials("alice", "NewStr0ng!1") is True

    def test_expired_session_with_password(self):
        result = auth_service.update_profile(
            "nonexistent",
            "Name",
            "a@b.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is False

    def test_invalid_name_blocks_password_change(self):
        """Validation of name must run before password change."""
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "",
            "alice@example.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is False
        assert "name" in str(result["message"]).lower()
        # Password should NOT have changed
        assert user_store.verify_credentials("alice", "alice") is True

    def test_invalid_email_blocks_password_change(self):
        """Validation of email must run before password change."""
        sid = self._login_alice()
        result = auth_service.update_profile(
            sid,
            "Alice",
            "bad-email",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is False
        assert "email" in str(result["message"]).lower()
        assert user_store.verify_credentials("alice", "alice") is True


# ── update_profile with password (adapter _service) ────────────────────────


class TestAdapterUpdateProfilePasswordChange:
    """Tests for ``adapters.ui_gradio.auth._service.update_profile``."""

    def test_password_change_success(self):
        from adapters.ui_gradio.auth._service import update_profile

        user_store.create_user("testuser", "Str0ng!pw", "User", "u@ex.com")
        result = update_profile(
            "testuser",
            "User",
            "u@ex.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is True
        assert result["message"] == "Profile and password updated."
        assert user_store.verify_credentials("testuser", "NewStr0ng!1") is True

    def test_empty_passwords_skips_change(self):
        from adapters.ui_gradio.auth._service import update_profile

        user_store.create_user("testuser", "Str0ng!pw", "User", "u@ex.com")
        result = update_profile("testuser", "User", "u@ex.com", "", "")
        assert result["ok"] is True
        assert result["message"] == "Profile updated."
        assert user_store.verify_credentials("testuser", "Str0ng!pw") is True

    def test_password_mismatch(self):
        from adapters.ui_gradio.auth._service import update_profile

        user_store.create_user("testuser", "Str0ng!pw", "User", "u@ex.com")
        result = update_profile(
            "testuser",
            "User",
            "u@ex.com",
            "NewStr0ng!1",
            "Different!1",
        )
        assert result["ok"] is False
        assert "match" in str(result["message"]).lower()

    def test_weak_password(self):
        from adapters.ui_gradio.auth._service import update_profile

        user_store.create_user("testuser", "Str0ng!pw", "User", "u@ex.com")
        result = update_profile(
            "testuser",
            "User",
            "u@ex.com",
            "short",
            "short",
        )
        assert result["ok"] is False

    def test_invalid_name_blocks_all(self):
        from adapters.ui_gradio.auth._service import update_profile

        user_store.create_user("testuser", "Str0ng!pw", "User", "u@ex.com")
        result = update_profile(
            "testuser",
            "",
            "u@ex.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is False
        assert "name" in str(result["message"]).lower()

    def test_user_not_found(self):
        from adapters.ui_gradio.auth._service import update_profile

        result = update_profile(
            "ghost",
            "Name",
            "a@b.com",
            "NewStr0ng!1",
            "NewStr0ng!1",
        )
        assert result["ok"] is False
        assert "not found" in str(result["message"]).lower()
