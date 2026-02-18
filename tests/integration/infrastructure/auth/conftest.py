"""Shared fixtures for authentication integration tests.

Provides DATABASE_URL setup for tests that need a real PostgreSQL database.
Tests are automatically **skipped** when no DATABASE_URL_TEST is available.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def _load_db_env() -> None:
    """Best-effort reload of DB vars from .env (for local dev)."""
    env_file = Path(__file__).resolve().parents[4] / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)


def _escape_password_in_url(url_str: str) -> str:
    """Escape special characters in PostgreSQL URL password."""
    if "://" not in url_str or "@" not in url_str:
        return url_str
    scheme_part, rest = url_str.split("://", 1)
    creds_part, host_part = rest.split("@", 1)
    if ":" not in creds_part:
        return url_str
    user, password = creds_part.split(":", 1)
    return f"{scheme_part}://{user}:{quote_plus(password)}@{host_part}"


@pytest.fixture(scope="session", autouse=True)
def restore_database_url_session():
    """Set DATABASE_URL so SessionLocal connects to the test database.

    The root conftest strips DATABASE_URL to keep unit tests DB-free.
    Integration tests need it back, pointing at DATABASE_URL_TEST.
    In CI, DATABASE_URL_TEST is an env var set by the workflow.
    Locally, it comes from .env (reloaded here as a fallback).
    """
    _load_db_env()
    url = os.environ.get("DATABASE_URL_TEST") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL_TEST must be set for auth integration tests.")
    # SessionLocal reads DATABASE_URL — point it at the test database.
    os.environ["DATABASE_URL"] = url
    logger.info("Auth integration tests: DATABASE_URL → %s", url[:40] + "…")
    yield
    # Tear down: remove DATABASE_URL and reset lazy engine/session globals
    # so stale connections don't leak into subsequent test modules.
    os.environ.pop("DATABASE_URL", None)
    try:
        from infrastructure.db import session as _sess_mod

        if _sess_mod._engine is not None:
            _sess_mod._engine.dispose()
        _sess_mod._engine = None
        _sess_mod._session_local = None
    except Exception:  # pragma: no cover
        pass
