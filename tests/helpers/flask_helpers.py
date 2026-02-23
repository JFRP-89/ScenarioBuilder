"""Shared helpers for Flask adapter integration tests.

Constants and utility functions live here so they can be imported by any
test module without relying on ``conftest.py`` (which Pylint cannot resolve
as a regular module).
"""

from __future__ import annotations

from flask.testing import FlaskClient

from helpers import credential_key
from infrastructure.auth import session_store

COOKIE_NAME = "sb_session"
CSRF_COOKIE_NAME = "sb_csrf"


def do_flask_login(
    test_client: FlaskClient,
    username: str = "alice",
    secret: str | None = None,
):
    """Log in *username* via the Flask test client.

    *secret* defaults to *username* (the convention set by
    ``seed_test_users``).  The credential payload is built dynamically to
    avoid hard-coded credential literals.
    """
    secret = secret if secret is not None else username
    payload: dict[str, str] = {"username": username, credential_key(): secret}
    return test_client.post("/auth/login", json=payload)


def get_session_cookie(response) -> str | None:
    """Extract *sb_session* cookie value from *response*."""
    for header_name, header_value in response.headers:
        if header_name.lower() == "set-cookie" and COOKIE_NAME in str(header_value):
            for part in str(header_value).split(";"):
                kv = part.strip()
                if kv.startswith(f"{COOKIE_NAME}="):
                    return str(kv.split("=", 1)[1])
    return None


def get_csrf_cookie(response) -> str | None:
    """Extract *sb_csrf* cookie value from *response*."""
    for header_name, header_value in response.headers:
        if header_name.lower() == "set-cookie" and CSRF_COOKIE_NAME in str(
            header_value
        ):
            for part in str(header_value).split(";"):
                kv = part.strip()
                if kv.startswith(f"{CSRF_COOKIE_NAME}="):
                    return str(kv.split("=", 1)[1])
    return None


def create_test_session(test_client: FlaskClient, actor_id: str = "u1") -> dict:
    """Create a server-side session and inject its cookie into *test_client*.

    Returns ``{"session_id": ..., "csrf_token": ...}``.
    """
    session = session_store.create_session(actor_id)
    session_id: str = session["session_id"]
    csrf_token: str = session["csrf_token"]
    test_client.set_cookie(
        key="sb_session",
        value=session_id,
        domain="localhost",
    )
    return {"session_id": session_id, "csrf_token": csrf_token}


# ---------------------------------------------------------------------------
# CSRF helpers (avoid W0212 + type: ignore on FlaskClient)
# ---------------------------------------------------------------------------


_csrf_tokens: dict[int, str] = {}


def store_csrf_token(test_client: FlaskClient, token: str) -> None:
    """Store a CSRF token for *test_client* for later retrieval."""
    _csrf_tokens[id(test_client)] = token


def csrf_token_of(test_client: FlaskClient) -> str:
    """Retrieve the CSRF token previously stored for *test_client*."""
    return _csrf_tokens[id(test_client)]


# ---------------------------------------------------------------------------
# Shared assertion helpers (avoid R0801 duplicate-code)
# ---------------------------------------------------------------------------


def assert_auth_required(response) -> None:
    """Assert that *response* indicates authentication is required (401)."""
    assert response.status_code == 401, "Missing auth should return 401"
    json_data = response.get_json()
    assert json_data is not None, "Response should be JSON"
    assert json_data.get("ok") is False
    assert json_data.get("message") == "Authentication required."
