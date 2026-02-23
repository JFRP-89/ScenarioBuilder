"""Integration tests for Flask registration routes.

Tests cover:
- POST /auth/register → creates user, sets session cookie, returns actor_id
- GET /auth/check-username → real-time availability check
- GET /register → serves registration HTML page
- Validation: weak password, mismatch, duplicate username, invalid format
"""

from __future__ import annotations

from helpers import confirm_credential_key, credential_key
from helpers.flask_helpers import (
    COOKIE_NAME,
    CSRF_COOKIE_NAME,
    do_flask_login,
)

_STRONG_SECRET = "Str0ng!pw"


def _register(
    client,
    *,
    username="newuser",
    secret=_STRONG_SECRET,
    confirm=None,
    name="New User",
    email="new@example.com",
):
    """Helper: POST /auth/register with default valid payload."""
    payload = {
        "username": username,
        credential_key(): secret,
        confirm_credential_key(): confirm if confirm is not None else secret,
        "name": name,
        "email": email,
    }
    return client.post("/auth/register", json=payload)


# ── GET /register (page) ────────────────────────────────────────────────────


class TestRegisterPage:
    def test_serves_html(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200
        assert b"Create your account" in resp.data

    def test_redirects_when_authenticated(self, client):
        # First register to get a session
        resp = _register(client)
        assert resp.status_code == 201
        # Now GET /register should redirect
        resp2 = client.get("/register")
        assert resp2.status_code == 302
        assert "/sb/" in resp2.headers.get("Location", "")


# ── POST /auth/register ─────────────────────────────────────────────────────


class TestRegisterRoute:
    def test_success_returns_201(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["ok"] is True
        assert data["actor_id"] == "newuser"

    def test_success_sets_session_cookie(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        # Check Set-Cookie headers in response
        set_cookies = resp.headers.getlist("Set-Cookie")
        cookie_names = [c.split("=")[0] for c in set_cookies]
        assert COOKIE_NAME in cookie_names
        assert CSRF_COOKIE_NAME in cookie_names

    def test_user_can_login_after_registration(self, client):
        _register(client)
        # Login with new credentials (cookies from registration still set)
        client.delete_cookie(COOKIE_NAME)
        client.delete_cookie(CSRF_COOKIE_NAME)
        resp = do_flask_login(client, "newuser", secret=_STRONG_SECRET)
        data = resp.get_json()
        assert data["ok"] is True

    def test_duplicate_username_returns_400(self, client):
        _register(client)
        client.delete_cookie(COOKIE_NAME)
        client.delete_cookie(CSRF_COOKIE_NAME)
        resp = _register(client)  # same username
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "taken" in data["message"]

    def test_existing_user_cannot_be_registered(self, client):
        resp = _register(client, username="alice")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "taken" in data["message"]

    def test_weak_password_returns_400(self, client):
        resp = _register(client, secret="weak")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "errors" in data

    def test_password_mismatch_returns_400(self, client):
        resp = _register(client, confirm="Differ3nt!")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert any("match" in str(e) for e in data["errors"])

    def test_invalid_username_returns_400(self, client):
        resp = _register(client, username="AB")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False

    def test_invalid_email_returns_400(self, client):
        resp = _register(client, email="not-an-email")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False

    def test_empty_email_rejected(self, client):
        resp = _register(client, email="")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "email" in str(data["message"]).lower()

    def test_no_cache_headers(self, client):
        resp = _register(client)
        assert "no-store" in resp.headers.get("Cache-Control", "")

    def test_no_csrf_required(self, client):
        """Registration does not require CSRF (unauthenticated endpoint)."""
        resp = _register(client)
        assert resp.status_code == 201


# ── GET /auth/check-username ─────────────────────────────────────────────────


class TestCheckUsernameRoute:
    def test_available_username(self, client):
        resp = client.get("/auth/check-username?username=brand-new")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["available"] is True

    def test_taken_username(self, client):
        resp = client.get("/auth/check-username?username=alice")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["available"] is False
        assert "taken" in data["message"]

    def test_invalid_format(self, client):
        resp = client.get("/auth/check-username?username=AB")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["available"] is False

    def test_after_registration(self, client):
        _register(client)
        resp = client.get("/auth/check-username?username=newuser")
        data = resp.get_json()
        assert data["available"] is False

    def test_no_cache_headers(self, client):
        resp = client.get("/auth/check-username?username=test")
        assert "no-store" in resp.headers.get("Cache-Control", "")


# ── Login page link ──────────────────────────────────────────────────────────


class TestLoginPageRegistrationLink:
    """Verify login page contains a link to the registration form."""

    def test_login_page_has_register_link(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"/register" in resp.data
        assert b"Create account" in resp.data

    def test_register_page_has_login_link(self, client):
        """Symmetry: registration page should link back to login."""
        resp = client.get("/register")
        assert resp.status_code == 200
        assert b"/login" in resp.data
