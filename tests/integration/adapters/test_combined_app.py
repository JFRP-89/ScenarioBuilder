"""Integration tests for the combined Flask + Gradio application.

Verifies that the FastAPI shell correctly mounts:
- ``/``   → redirect to ``/sb/``
- ``/sb/`` → serves Gradio
- ``/auth/*``, ``/health``, ``/login`` → served by Flask
"""

from __future__ import annotations

import pytest
from infrastructure.auth import session_store, user_store


@pytest.fixture(autouse=True)
def _reset_stores():
    session_store.reset_sessions()
    user_store.reset_stores()
    yield
    session_store.reset_sessions()
    user_store.reset_stores()


@pytest.fixture()
def combined_client():
    """Create a Starlette TestClient for the combined ASGI app."""
    from adapters.combined_app import create_combined_app
    from starlette.testclient import TestClient

    app = create_combined_app()
    return TestClient(app, follow_redirects=False)


class TestCombinedRouting:
    def test_root_redirects_to_ui(self, combined_client):
        resp = combined_client.get("/")
        assert resp.status_code in (301, 302, 307)
        assert "/sb" in resp.headers.get("location", "")

    def test_health_served_by_flask(self, combined_client):
        resp = combined_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_login_page_served_by_flask(self, combined_client):
        resp = combined_client.get("/login")
        assert resp.status_code == 200
        assert b"login" in resp.content.lower()

    def test_auth_login_creates_session(self, combined_client):
        resp = combined_client.post(
            "/auth/login",
            json={"username": "alice", "password": "alice"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["actor_id"] == "alice"
        # Cookie should be set
        assert "sb_session" in resp.cookies

    def test_auth_me_with_session(self, combined_client):
        # Login first
        combined_client.post(
            "/auth/login",
            json={"username": "alice", "password": "alice"},
        )
        # /auth/me should return profile
        resp = combined_client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["profile"]["username"] == "alice"

    def test_auth_me_without_session_returns_401(self, combined_client):
        resp = combined_client.get("/auth/me")
        assert resp.status_code == 401

    def test_gradio_ui_accessible(self, combined_client):
        resp = combined_client.get("/ui/", follow_redirects=True)
        # Gradio serves HTML at /ui/
        assert resp.status_code == 200

    def test_api_route_requires_session(self, combined_client):
        resp = combined_client.get("/cards/")
        assert resp.status_code == 401

    def test_api_route_accessible_with_session(self, combined_client):
        combined_client.post(
            "/auth/login",
            json={"username": "alice", "password": "alice"},
        )
        resp = combined_client.get("/cards/")
        # Should not be 401
        assert resp.status_code != 401

    def test_login_then_logout_then_api_401(self, combined_client):
        # Login
        login_resp = combined_client.post(
            "/auth/login",
            json={"username": "alice", "password": "alice"},
        )
        csrf = login_resp.cookies.get("sb_csrf", "")
        # Logout
        combined_client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        # API should now be 401
        resp = combined_client.get("/cards/")
        assert resp.status_code == 401
