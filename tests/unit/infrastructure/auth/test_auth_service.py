"""Unit tests for infrastructure.auth.auth_service."""

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


# ── authenticate ─────────────────────────────────────────────────────────────


class TestAuthenticate:
    def test_success(self):
        result = auth_service.authenticate("alice", "alice")
        assert result["ok"] is True
        assert result["actor_id"] == "alice"
        assert "session_id" in result
        assert "csrf_token" in result
        assert isinstance(result["message"], str)

    def test_wrong_password(self):
        result = auth_service.authenticate("alice", "wrong")
        assert result["ok"] is False
        assert result["actor_id"] is None

    def test_unknown_user(self):
        result = auth_service.authenticate("nobody", "nobody")
        assert result["ok"] is False
        assert result["actor_id"] is None

    def test_invalid_username_format(self):
        result = auth_service.authenticate("A!", "password123")
        assert result["ok"] is False

    def test_invalid_password_format(self):
        result = auth_service.authenticate("alice", "a b")
        assert result["ok"] is False

    def test_creates_session(self):
        result = auth_service.authenticate("alice", "alice")
        assert result["ok"] is True
        session_id = str(result["session_id"])
        session = session_store.get_session(session_id)
        assert session is not None
        assert session["actor_id"] == "alice"

    def test_lockout_after_max_attempts(self):
        for _ in range(3):
            auth_service.authenticate("alice", "wrong")
        result = auth_service.authenticate("alice", "alice")
        assert result["ok"] is False
        assert "locked" in str(result["message"]).lower()

    def test_pre_existing_lockout(self):
        for _ in range(3):
            auth_service.authenticate("alice", "wrong")
        result = auth_service.authenticate("alice", "alice")
        assert result["ok"] is False


# ── logout ───────────────────────────────────────────────────────────────────


class TestLogout:
    def test_invalidates_session(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.logout(session_id)
        assert result["ok"] is True
        assert session_store.get_session(session_id) is None

    def test_logout_unknown_session(self):
        result = auth_service.logout("nonexistent")
        assert result["ok"] is True  # Idempotent


# ── get_me ───────────────────────────────────────────────────────────────────


class TestGetMe:
    def test_returns_profile(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.get_me(session_id)
        assert result["ok"] is True
        profile = result["profile"]
        assert profile["username"] == "alice"

    def test_expired_session(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        session_store.invalidate_session(session_id)
        result = auth_service.get_me(session_id)
        assert result["ok"] is False


# ── reauth ───────────────────────────────────────────────────────────────────


class TestReauth:
    def test_success_rotates_session(self):
        login_res = auth_service.authenticate("alice", "alice")
        old_id = str(login_res["session_id"])
        result = auth_service.reauth(old_id, "alice")
        assert result["ok"] is True
        assert result["session_id"] != old_id
        # Old session invalid
        assert session_store.get_session(old_id) is None

    def test_wrong_password(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.reauth(session_id, "wrong")
        assert result["ok"] is False

    def test_expired_session(self):
        result = auth_service.reauth("nonexistent", "alice")
        assert result["ok"] is False

    def test_invalid_password_format(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.reauth(session_id, "a b")
        assert result["ok"] is False

    def test_lockout_during_reauth(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        for _ in range(3):
            auth_service.reauth(session_id, "wrong")
            # Session might still be valid; get fresh session_id
            session = session_store.get_session(session_id)
            if session is None:
                break
        result = auth_service.reauth(session_id, "alice")
        assert result["ok"] is False


# ── check_reauth ─────────────────────────────────────────────────────────────


class TestCheckReauth:
    def test_false_without_reauth(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        assert auth_service.check_reauth(session_id) is False

    def test_true_after_reauth(self):
        login_res = auth_service.authenticate("alice", "alice")
        old_id = str(login_res["session_id"])
        reauth_res = auth_service.reauth(old_id, "alice")
        new_id = str(reauth_res["session_id"])
        assert auth_service.check_reauth(new_id) is True


# ── update_profile ───────────────────────────────────────────────────────────


class TestUpdateProfile:
    def test_success(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.update_profile(session_id, "New Name", "new@example.com")
        assert result["ok"] is True

    def test_invalid_name(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.update_profile(session_id, "", "new@example.com")
        assert result["ok"] is False

    def test_invalid_email(self):
        login_res = auth_service.authenticate("alice", "alice")
        session_id = str(login_res["session_id"])
        result = auth_service.update_profile(session_id, "Valid Name", "bad-email")
        assert result["ok"] is False

    def test_expired_session(self):
        result = auth_service.update_profile("nonexistent", "Name", "a@b.com")
        assert result["ok"] is False
