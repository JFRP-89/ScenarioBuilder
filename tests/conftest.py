"""Test fixtures and configuration.

Two execution profiles
----------------------
**local-dev** (default):
    ``pytest tests/unit tests/integration -q``
    No PostgreSQL required. Tests marked ``@pytest.mark.db`` are skipped
    automatically.

**with-db**:
    ``RUN_DB_TESTS=1 DATABASE_URL_TEST=postgresql+psycopg2://… pytest …``
    DB tests run only when both the flag is set *and* the database
    responds to a quick ``SELECT 1``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Only strip DATABASE_URL so SessionLocal never connects during unit tests.
# DATABASE_URL_TEST is kept — it's only read by test infrastructure, never
# by production code, and integration conftests need it in CI (where .env
# does not exist).
_DB_KEYS = {"DATABASE_URL"}


# ---------------------------------------------------------------------------
# 1. Safe .env loading — strip DB keys so general tests stay DB-free
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load .env at session start, but remove DATABASE_URL.

    This ensures non-DB tests always use ``InMemoryCardRepository`` and
    never attempt a PostgreSQL connection via ``SessionLocal``.
    DATABASE_URL is restored after the session so the process leaves
    the environment as it found it.
    """
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
    # Remove production DB key so general tests use InMemoryCardRepository.
    # DATABASE_URL_TEST is intentionally kept — see _DB_KEYS comment.
    saved = {}
    for key in _DB_KEYS:
        if key in os.environ:
            saved[key] = os.environ.pop(key)
    yield
    # Restore after session ends
    os.environ.update(saved)


# ---------------------------------------------------------------------------
# 2. DB reachability probe — cached once per session
# ---------------------------------------------------------------------------
def _db_is_reachable() -> bool:
    """Return ``True`` when ``DATABASE_URL_TEST`` DB answers ``SELECT 1``.

    DATABASE_URL_TEST is still in os.environ (not stripped by load_env),
    so we read it directly.  Fallback: re-read from .env for local dev.
    """
    url = os.environ.get("DATABASE_URL_TEST", "")
    if not url:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            from dotenv import dotenv_values

            vals = dotenv_values(env_file)
            url = vals.get("DATABASE_URL_TEST", "")
    if not url:
        return False
    try:
        from sqlalchemy import create_engine, text

        eng = create_engine(url, connect_args={"connect_timeout": 3})
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return True
    except Exception:
        return False


# Cache the result so we only probe once.
_db_reachable: bool | None = None


def db_enabled() -> bool:
    """Return ``True`` only when DB tests should run.

    Conditions (both must hold):
    1. ``RUN_DB_TESTS`` env var is ``1`` / ``true`` / ``yes``.
    2. The database at ``DATABASE_URL_TEST`` answers ``SELECT 1``.
    """
    global _db_reachable
    run_flag = os.environ.get("RUN_DB_TESTS", "").strip().lower()
    if run_flag not in ("1", "true", "yes"):
        return False
    if _db_reachable is None:
        _db_reachable = _db_is_reachable()
    return _db_reachable


# ---------------------------------------------------------------------------
# 3. Auto-skip @pytest.mark.db tests when DB is not available
# ---------------------------------------------------------------------------
def pytest_collection_modifyitems(config, items):
    """Skip ``@pytest.mark.db`` tests unless DB profile is active."""
    if db_enabled():
        return  # DB available — run everything

    skip_db = pytest.mark.skip(
        reason="DB tests disabled (set RUN_DB_TESTS=1 and DATABASE_URL_TEST)"
    )
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip_db)
