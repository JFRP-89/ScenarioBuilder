"""Integration tests for Flask auth blueprint (routes/auth.py).

Tests cover:
- POST /auth/login → sets HttpOnly cookie, returns actor_id
- POST /auth/logout → clears cookie
- GET /auth/me → returns profile from session
- POST /auth/reauth → rotates session, updates cookie
- POST /auth/profile → updates display name / email
- CSRF verification on mutating requests
- Session expiry behaviour
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


def _login(client, username="alice", password="alice"):
    """Helper: perform login and return response."""
    return client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )


def _get_session_cookie(response):
    """Extract sb_session cookie value from response."""
    for header_name, header_value in response.headers:
        if header_name.lower() == "set-cookie" and _COOKIE_NAME in header_value:
            for part in header_value.split(";"):
                kv = part.strip()
                if kv.startswith(f"{_COOKIE_NAME}="):
                    return kv.split("=", 1)[1]
    return None


def _get_csrf_cookie(response):
    """Extract sb_csrf cookie value from response."""
    for header_name, header_value in response.headers:
        if header_name.lower() == "set-cookie" and _CSRF_COOKIE_NAME in header_value:
            for part in header_value.split(";"):
                kv = part.strip()
                if kv.startswith(f"{_CSRF_COOKIE_NAME}="):
                    return kv.split("=", 1)[1]
    return None


# ── POST /auth/login ─────────────────────────────────────────────────────────


class TestLogin:
    def test_success_returns_ok(self, client):
        resp = _login(client)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["actor_id"] == "alice"

    def test_success_sets_session_cookie(self, client):
        resp = _login(client)
        cookie = _get_session_cookie(resp)
        assert cookie is not None
        assert len(cookie) == 64  # 32 bytes hex

    def test_success_sets_csrf_cookie(self, client):
        resp = _login(client)
        csrf = _get_csrf_cookie(resp)
        assert csrf is not None
        assert len(csrf) == 64

    def test_session_cookie_is_httponly(self, client):
        resp = _login(client)
        raw_headers = [
            v
            for k, v in resp.headers
            if k.lower() == "set-cookie" and _COOKIE_NAME in v
        ]
        assert any("httponly" in h.lower() for h in raw_headers)

    def test_wrong_password(self, client):
        resp = _login(client, password="wrong")
        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_no_cache_headers(self, client):
        resp = _login(client)
        assert "no-store" in resp.headers.get("Cache-Control", "")

    def test_unknown_user(self, client):
        resp = _login(client, username="nobody", password="nobody")
        assert resp.status_code == 401


# ── POST /auth/logout ────────────────────────────────────────────────────────


class TestLogout:
    def test_logout_clears_cookie(self, client):
        login_resp = _login(client)  # sets cookie on jar
        csrf = _get_csrf_cookie(login_resp)
        resp = client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        # Cookie should be cleared (max-age=0 or expires in past)
        raw_headers = [
            v
            for k, v in resp.headers
            if k.lower() == "set-cookie" and _COOKIE_NAME in v
        ]
        assert len(raw_headers) > 0  # clear cookie header present

    def test_logout_without_session(self, client):
        # No session → no CSRF check (middleware skips if no session_id)
        resp = client.post("/auth/logout")
        assert resp.status_code == 200


# ── GET /auth/me ──────────────────────────────────────────────────────────────


class TestMe:
    def test_returns_profile_with_session(self, client):
        _login(client)
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["profile"]["username"] == "alice"

    def test_no_session_returns_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False


# ── POST /auth/reauth ────────────────────────────────────────────────────────


class TestReauth:
    def test_success_rotates_session(self, client):
        login_resp = _login(client)
        old_cookie = _get_session_cookie(login_resp)

        # Need to extract CSRF from login response for the reauth request
        csrf = _get_csrf_cookie(login_resp)

        resp = client.post(
            "/auth/reauth",
            json={"password": "alice"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True

        new_cookie = _get_session_cookie(resp)
        assert new_cookie is not None
        assert new_cookie != old_cookie

    def test_wrong_password(self, client):
        login_resp = _login(client)
        csrf = _get_csrf_cookie(login_resp)
        resp = client.post(
            "/auth/reauth",
            json={"password": "wrong"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    def test_no_session_returns_401(self, client):
        resp = client.post("/auth/reauth", json={"password": "alice"})
        assert resp.status_code == 401


# ── POST /auth/profile ───────────────────────────────────────────────────────


class TestUpdateProfile:
    def test_success(self, client):
        login_resp = _login(client)
        csrf = _get_csrf_cookie(login_resp)
        resp = client.post(
            "/auth/profile",
            json={"name": "New Name", "email": "new@example.com"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_profile_saved(self, client):
        login_resp = _login(client)
        csrf = _get_csrf_cookie(login_resp)
        client.post(
            "/auth/profile",
            json={"name": "Updated", "email": "up@example.com"},
            headers={"X-CSRF-Token": csrf},
        )
        me_resp = client.get("/auth/me")
        profile = me_resp.get_json()["profile"]
        assert profile["name"] == "Updated"
        assert profile["email"] == "up@example.com"

    def test_invalid_name(self, client):
        login_resp = _login(client)
        csrf = _get_csrf_cookie(login_resp)
        resp = client.post(
            "/auth/profile",
            json={"name": "", "email": "ok@example.com"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 400

    def test_no_session(self, client):
        resp = client.post(
            "/auth/profile",
            json={"name": "Test", "email": "t@x.com"},
        )
        assert resp.status_code == 401


# ── CSRF verification ────────────────────────────────────────────────────────


class TestCsrfVerification:
    def test_mutating_request_without_csrf_token_is_rejected(self, client):
        """POST to a protected route without CSRF token → 403."""
        _login(client)
        # POST to profile without X-CSRF-Token
        resp = client.post(
            "/auth/profile",
            json={"name": "Test", "email": "t@x.com"},
            # No X-CSRF-Token header
        )
        assert resp.status_code == 403
        assert "csrf" in resp.get_json()["message"].lower()

    def test_mutating_request_with_wrong_csrf_is_rejected(self, client):
        _login(client)
        resp = client.post(
            "/auth/profile",
            json={"name": "Test", "email": "t@x.com"},
            headers={"X-CSRF-Token": "wrong-token"},
        )
        assert resp.status_code == 403

    def test_login_is_csrf_exempt(self, client):
        """Login does not require CSRF (no prior session)."""
        resp = _login(client)
        assert resp.status_code == 200

    def test_logout_requires_csrf(self, client):
        """Logout is a POST but does NOT start with /auth/login."""
        _login(client)
        # Logout without CSRF should be rejected
        resp = client.post("/auth/logout")
        # The middleware checks CSRF for POST with an active session
        assert resp.status_code == 403


# ── Session expiry ───────────────────────────────────────────────────────────


class TestSessionExpiry:
    def test_expired_session_returns_401_on_me(self, client):
        """After invalidating server-side, /me returns 401."""
        login_resp = _login(client)
        session_cookie = _get_session_cookie(login_resp)
        # Invalidate server-side
        session_store.invalidate_session(session_cookie)
        resp = client.get("/auth/me")
        assert resp.status_code == 401
