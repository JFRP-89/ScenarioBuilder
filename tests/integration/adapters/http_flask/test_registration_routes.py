"""Integration tests for Flask registration routes.

Tests cover:
- POST /auth/register → creates user, sets session cookie, returns actor_id
- GET /auth/check-username → real-time availability check
- GET /register → serves registration HTML page
- Validation: weak password, mismatch, duplicate username, invalid format
"""

from __future__ import annotations

import pytest
from adapters.http_flask.app import create_app
from infrastructure.auth import session_store, user_store

_COOKIE_NAME = "sb_session"
_CSRF_COOKIE_NAME = "sb_csrf"


@pytest.fixture()
def app():
    """Create a Flask test app and reset auth stores."""
    session_store.reset_sessions()
    user_store.reset_stores()
    application = create_app()
    application.config["TESTING"] = True
    yield application
    session_store.reset_sessions()
    user_store.reset_stores()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register(client, **overrides):
    """Helper: POST /auth/register with default valid payload."""
    payload = {
        "username": "newuser",
        "password": "Str0ng!pw",
        "confirm_password": "Str0ng!pw",
        "name": "New User",
        "email": "new@example.com",
    }
    payload.update(overrides)
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
        assert _COOKIE_NAME in cookie_names
        assert _CSRF_COOKIE_NAME in cookie_names

    def test_user_can_login_after_registration(self, client):
        _register(client)
        # Login with new credentials (cookies from registration still set)
        client.delete_cookie(_COOKIE_NAME)
        client.delete_cookie(_CSRF_COOKIE_NAME)
        resp = client.post(
            "/auth/login",
            json={"username": "newuser", "password": "Str0ng!pw"},
        )
        data = resp.get_json()
        assert data["ok"] is True

    def test_duplicate_username_returns_400(self, client):
        _register(client)
        client.delete_cookie(_COOKIE_NAME)
        client.delete_cookie(_CSRF_COOKIE_NAME)
        resp = _register(client)  # same username
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "taken" in data["message"]

    def test_demo_user_cannot_be_registered(self, client):
        resp = _register(client, username="alice")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "taken" in data["message"]

    def test_weak_password_returns_400(self, client):
        resp = _register(client, password="weak", confirm_password="weak")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "errors" in data

    def test_password_mismatch_returns_400(self, client):
        resp = _register(client, confirm_password="Differ3nt!")
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

    def test_empty_email_accepted(self, client):
        resp = _register(client, email="")
        assert resp.status_code == 201

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


class TestLoginPageLink:
    def test_login_page_has_register_link(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"/register" in resp.data
        assert b"Create account" in resp.data
