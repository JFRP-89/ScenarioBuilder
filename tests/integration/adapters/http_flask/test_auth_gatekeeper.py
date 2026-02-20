"""Integration tests for Flask middleware auth gatekeeper.

Verifies that API routes (``/cards``, ``/favorites``, ``/maps``,
``/presets``) require a valid session, while public routes (``/health``,
``/login``, ``/auth/*``) remain accessible without authentication.
"""

from __future__ import annotations

import pytest
from adapters.http_flask.app import create_app
from infrastructure.auth import session_store, user_store

_COOKIE_NAME = "sb_session"
_CSRF_COOKIE_NAME = "sb_csrf"


@pytest.fixture()
def app():
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
    return client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )


def _get_csrf_cookie(response):
    for header_name, header_value in response.headers:
        if header_name.lower() == "set-cookie" and _CSRF_COOKIE_NAME in header_value:
            for part in header_value.split(";"):
                kv = part.strip()
                if kv.startswith(f"{_CSRF_COOKIE_NAME}="):
                    return kv.split("=", 1)[1]
    return None


# ── Public routes remain accessible ──────────────────────────────────────────


class TestPublicRoutes:
    def test_health_no_auth_required(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_login_page_no_auth_required(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"login" in resp.data.lower()

    def test_auth_login_post_no_prior_session(self, client):
        resp = _login(client)
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_auth_me_returns_401_without_session(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401


# ── API routes require authentication ────────────────────────────────────────


class TestApiAuthGate:
    """API routes reject unauthenticated requests with 401."""

    def test_get_cards_without_session(self, client):
        resp = client.get("/cards/")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["ok"] is False
        assert "authentication" in data["message"].lower()

    def test_get_favorites_without_session(self, client):
        resp = client.get("/favorites/")
        assert resp.status_code == 401

    def test_get_maps_without_session(self, client):
        resp = client.get("/maps/some-id")
        assert resp.status_code == 401

    def test_get_presets_without_session(self, client):
        resp = client.get("/presets/")
        assert resp.status_code == 401

    def test_post_cards_without_session(self, client):
        resp = client.post("/cards/", json={"data": "test"})
        assert resp.status_code == 401

    def test_cards_accessible_with_session(self, client):
        _login(client)
        resp = client.get("/cards/")
        # Should not be 401 — may be 200 or 400 depending on query params
        assert resp.status_code != 401


# ── CSRF still enforced on API mutations ─────────────────────────────────────


class TestCsrfOnApiRoutes:
    def test_post_cards_requires_csrf(self, client):
        """Authenticated POST without CSRF token → 403."""
        _login(client)
        resp = client.post("/cards/", json={"test": True})
        assert resp.status_code == 403

    def test_post_cards_with_csrf_passes(self, client):
        """Authenticated POST with correct CSRF token passes middleware."""
        login_resp = _login(client)
        csrf = _get_csrf_cookie(login_resp)
        resp = client.post(
            "/cards/",
            json={"test": True},
            headers={"X-CSRF-Token": csrf},
        )
        # Should pass middleware — may still fail in route logic but not 401/403
        assert resp.status_code not in (401, 403)


# ── Login page redirect when already authenticated ───────────────────────────


class TestLoginPageRedirect:
    def test_login_page_redirects_when_authenticated(self, client):
        _login(client)
        resp = client.get("/login")
        assert resp.status_code == 302
        assert "/sb" in resp.headers.get("Location", "")

    def test_login_page_shows_form_when_unauthenticated(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"<form" in resp.data


# ── Session in store after login ─────────────────────────────────────────────


class TestSessionCreation:
    def test_login_creates_session_in_store(self, client):
        """After login, the session exists in the session store."""
        resp = _login(client)
        data = resp.get_json()
        assert data["ok"] is True

        # Extract session cookie
        session_id = None
        for header_name, header_value in resp.headers:
            if header_name.lower() == "set-cookie" and _COOKIE_NAME in header_value:
                for part in header_value.split(";"):
                    kv = part.strip()
                    if kv.startswith(f"{_COOKIE_NAME}="):
                        session_id = kv.split("=", 1)[1]
        assert session_id is not None

        # Verify session exists in the store
        session = session_store.get_session(session_id)
        assert session is not None
        assert session["actor_id"] == "alice"

    def test_logout_revokes_session_in_store(self, client):
        """After logout, the session is no longer valid."""
        login_resp = _login(client)
        csrf = _get_csrf_cookie(login_resp)

        # Extract the session_id
        session_id = None
        for header_name, header_value in login_resp.headers:
            if header_name.lower() == "set-cookie" and _COOKIE_NAME in header_value:
                for part in header_value.split(";"):
                    kv = part.strip()
                    if kv.startswith(f"{_COOKIE_NAME}="):
                        session_id = kv.split("=", 1)[1]

        # Logout
        client.post("/auth/logout", headers={"X-CSRF-Token": csrf})

        # Session should be invalidated
        assert session_id is not None
        session = session_store.get_session(session_id)
        assert session is None
