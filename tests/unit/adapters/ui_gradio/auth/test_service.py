"""Unit tests — auth service (authenticate, logout, profile)."""

from __future__ import annotations

import pytest

from adapters.ui_gradio.auth._service import (
    authenticate,
    get_logged_in_label,
    get_profile,
    logout,
    update_profile,
)
from adapters.ui_gradio.auth._store import (
    MAX_FAILED_ATTEMPTS,
    reset_stores,
)
from helpers import seed_test_users


@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset stores before each test and seed test users."""
    reset_stores()
    seed_test_users()
    yield
    reset_stores()


# =====================================================================
# authenticate()
# =====================================================================
class TestAuthenticate:
    """Test authentication flow including lockout."""

    def test_valid_login(self):
        result = authenticate("alice", "alice")
        assert result["ok"] is True
        assert result["actor_id"] == "alice"
        assert "Welcome" in str(result["message"])

    def test_wrong_password(self):
        result = authenticate("alice", "wrong-pass")
        assert result["ok"] is False
        assert result["actor_id"] is None
        assert "Invalid credentials" in str(result["message"])

    def test_unknown_user(self):
        result = authenticate("unknown-user-abc", "password")
        assert result["ok"] is False
        assert result["actor_id"] is None
        # Same message as wrong password (anti-enumeration)
        assert "Invalid credentials" in str(result["message"])

    def test_invalid_username_format(self):
        result = authenticate("UPPERCASE", "password")
        assert result["ok"] is False
        assert "Invalid credentials" in str(result["message"])

    def test_invalid_password_format(self):
        result = authenticate("alice", "a b c")  # spaces not allowed
        assert result["ok"] is False
        assert "Invalid credentials" in str(result["message"])

    def test_lockout_after_three_failures(self):
        for _ in range(MAX_FAILED_ATTEMPTS):
            authenticate("alice", "wrong")

        # Now locked
        result = authenticate("alice", "alice")
        assert result["ok"] is False
        assert "locked" in str(result["message"]).lower()

    def test_lockout_message_contains_timestamp(self):
        for _ in range(MAX_FAILED_ATTEMPTS):
            authenticate("alice", "wrong")

        result = authenticate("alice", "alice")
        assert "UTC" in str(result["message"])

    def test_successful_login_clears_failed_attempts(self):
        # 2 failures (below threshold)
        authenticate("bob", "wrong")
        authenticate("bob", "wrong")

        # Successful login → clears counter
        result = authenticate("bob", "bob")
        assert result["ok"] is True

        # 2 more failures; total from "scratch" so not locked yet
        authenticate("bob", "wrong")
        authenticate("bob", "wrong")
        result = authenticate("bob", "bob")
        assert result["ok"] is True

    def test_injection_attempt_rejected(self):
        result = authenticate("admin'; DROP--", "password")
        assert result["ok"] is False
        assert "Invalid credentials" in str(result["message"])

    @pytest.mark.parametrize(
        "username",
        ["alice", "bob", "charlie", "dave"],
    )
    def test_all_test_users_can_login(self, username: str):
        result = authenticate(username, username)
        assert result["ok"] is True
        assert result["actor_id"] == username


# =====================================================================
# logout()
# =====================================================================
class TestLogout:
    """Logout clears the session (actor_id → empty)."""

    def test_logout_clears_actor_id(self):
        result = logout("alice")
        assert result["ok"] is True
        assert result["actor_id"] == ""
        assert "logged out" in str(result["message"]).lower()


# =====================================================================
# get_profile()
# =====================================================================
class TestGetProfile:
    """Profile retrieval."""

    def test_get_existing_profile(self):
        result = get_profile("alice")
        assert result["ok"] is True
        profile = result["profile"]
        assert profile["username"] == "alice"
        assert profile["name"] == "Alice"
        assert "@" in profile["email"]

    def test_get_unknown_profile(self):
        result = get_profile("unknown-user-xyz")
        assert result["ok"] is False


# =====================================================================
# update_profile()
# =====================================================================
class TestUpdateProfile:
    """Profile update with validation."""

    def test_valid_update(self):
        result = update_profile("alice", "Alice W.", "alice.w@example.com")
        assert result["ok"] is True
        assert "updated" in str(result["message"]).lower()

        profile = get_profile("alice")
        assert profile["profile"]["name"] == "Alice W."
        assert profile["profile"]["email"] == "alice.w@example.com"

    def test_invalid_email_rejected(self):
        result = update_profile("alice", "Alice", "not-an-email")
        assert result["ok"] is False
        assert "email" in str(result["message"]).lower()

    def test_empty_name_rejected(self):
        result = update_profile("alice", "", "alice@example.com")
        assert result["ok"] is False
        assert "name" in str(result["message"]).lower()

    def test_unknown_user_rejected(self):
        result = update_profile("no-such-user", "Name", "a@b.com")
        assert result["ok"] is False

    def test_profile_can_be_updated_multiple_times(self):
        update_profile("bob", "Bob 1", "bob1@example.com")
        update_profile("bob", "Bob 2", "bob2@example.com")
        profile = get_profile("bob")
        assert profile["profile"]["name"] == "Bob 2"
        assert profile["profile"]["email"] == "bob2@example.com"

    def test_duplicate_email_rejected(self):
        """Cannot change email to one already used by another user."""
        alice_profile = get_profile("alice")
        assert alice_profile["ok"] is True
        alice_email = alice_profile["profile"]["email"]
        result = update_profile("bob", "Bob", alice_email)
        assert result["ok"] is False
        assert "email" in str(result["message"]).lower()

    def test_keeping_own_email_allowed(self):
        """User can keep their current email when updating name only."""
        alice_profile = get_profile("alice")
        assert alice_profile["ok"] is True
        alice_email = alice_profile["profile"]["email"]
        result = update_profile("alice", "Alice Updated", alice_email)
        assert result["ok"] is True


# =====================================================================
# get_logged_in_label()
# =====================================================================
class TestGetLoggedInLabel:
    """Label generation for UI — returns HTML user pill."""

    def test_empty_actor_returns_empty_label(self):
        label = get_logged_in_label("")
        assert label == ""

    def test_regular_user_shows_pill_with_display_name(self):
        label = get_logged_in_label("alice")
        assert "sb-userpill" in label
        assert "Alice" in label
        assert "alice" not in label  # raw username must NOT leak

    def test_unknown_user_falls_back_to_username(self):
        label = get_logged_in_label("unknown_user")
        assert "sb-userpill" in label
        assert "unknown_user" in label

    def test_pill_contains_icon(self):
        label = get_logged_in_label("alice")
        assert "sb-userpill__icon" in label
        assert "<svg" in label

    def test_pill_name_is_html_escaped(self):
        # seed a user with special characters in name
        from infrastructure.auth.user_store import create_user

        create_user("xss", "pw", '<script>alert("x")</script>', "xss@test.com")
        label = get_logged_in_label("xss")
        assert "<script>" not in label
        assert "&lt;script&gt;" in label
