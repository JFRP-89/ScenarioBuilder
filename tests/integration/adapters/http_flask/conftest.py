"""Shared fixtures for Flask adapter integration tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from adapters.http_flask.app import create_app
from helpers import seed_test_users
from helpers.flask_helpers import create_test_session
from infrastructure.auth import session_store, user_store

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> Generator[Flask, None, None]:
    """Create a Flask test app and reset auth stores."""
    session_store.reset_sessions()
    user_store.reset_stores()
    seed_test_users()
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    yield flask_app
    session_store.reset_sessions()
    user_store.reset_stores()


@pytest.fixture()
def client(request) -> FlaskClient:
    """Flask test client backed by the *app* fixture."""
    flask_app: Flask = request.getfixturevalue("app")
    return flask_app.test_client()


@pytest.fixture()
def session_factory():
    """Return the ``create_test_session`` helper for use in test fixtures."""
    return create_test_session
