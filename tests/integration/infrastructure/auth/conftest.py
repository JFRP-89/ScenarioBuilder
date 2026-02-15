"""Shared fixtures for authentication integration tests.

Provides DATABASE_URL setup for tests that need a real PostgreSQL database.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

import pytest
from dotenv import load_dotenv


def _load_db_env() -> None:
    """Reload DATABASE_URL from .env (stripped by session conftest)."""
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
    """Restore DATABASE_URL for tests (stripped by session conftest).

    The global conftest removes DATABASE_URL so general unit tests use
    InMemoryCardRepository. This fixture restores it for integration tests.
    """
    _load_db_env()
    yield
