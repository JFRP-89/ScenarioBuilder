"""Shared fixtures for Flask adapter integration tests."""

from __future__ import annotations

import pytest
from infrastructure.auth import session_store


def create_test_session(test_client, actor_id: str = "u1") -> dict:
    """Create a server-side session and inject its cookie into *test_client*.

    Returns ``{"session_id": ..., "csrf_token": ...}``.

    This replaces the legacy ``X-Actor-Id`` header approach: the middleware
    now requires a valid ``sb_session`` cookie for API routes.
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


@pytest.fixture()
def session_factory():
    """Return the ``create_test_session`` helper for use in test fixtures."""
    return create_test_session
