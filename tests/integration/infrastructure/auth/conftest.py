"""Shared fixtures for authentication integration tests.

Provides DATABASE_URL setup for tests that need a real PostgreSQL database.
Tests are automatically **skipped** when no DATABASE_URL_TEST is available.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from helpers.db import run_alembic_upgrade
from helpers.fake_clock import FakeClock
from infrastructure.auth import postgres_session_store as pss_mod
from infrastructure.auth.postgres_session_store import PostgresSessionStore
from infrastructure.clock import SystemClock
from infrastructure.db.models import Base
from infrastructure.db.session import (
    SessionLocal,
    escape_password_in_url,
    reset_lazy_state,
)

logger = logging.getLogger(__name__)


def _load_db_env() -> None:
    """Best-effort reload of DB vars from .env (for local dev)."""
    env_file = Path(__file__).resolve().parents[4] / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)


# ---------------------------------------------------------------------------
# DB bootstrapping helpers
# ---------------------------------------------------------------------------


def _create_db_if_needed(admin_url: str, db_name: str) -> None:
    """Create the test database when it does not yet exist."""
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            if not result.fetchone():
                safe = db_name.replace('"', '""')
                conn.execute(text(f'CREATE DATABASE "{safe}"'))
                logger.info("Created database '%s'", db_name)
    finally:
        engine.dispose()


def _run_migrations(url: str) -> None:
    """Run Alembic migrations, falling back to SQLAlchemy metadata."""
    proc = run_alembic_upgrade(url)

    if proc.returncode != 0 or not proc.stdout.strip():
        eng = create_engine(url)
        try:
            Base.metadata.create_all(eng)
        finally:
            eng.dispose()


def _ensure_db_and_schema(url: str) -> None:
    """Create the test database (if needed) and run migrations."""
    url = escape_password_in_url(url)
    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/").split("?")[0] if parsed.path else ""
    if not db_name:
        return

    admin_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/postgres", "", parsed.query, ""),
    )

    try:
        _create_db_if_needed(admin_url, db_name)
    except SQLAlchemyError as exc:
        logger.warning("Could not ensure DB exists: %s", exc)
        return

    try:
        _run_migrations(url)
    except (SQLAlchemyError, OSError) as exc:
        logger.warning("Fallback schema creation failed: %s", exc)


# ---------------------------------------------------------------------------
# Session-scoped DB URL fixture
# ---------------------------------------------------------------------------


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

    _ensure_db_and_schema(url)

    os.environ["DATABASE_URL"] = url
    logger.info("Auth integration tests: DATABASE_URL → %s", url[:40] + "…")
    yield
    os.environ.pop("DATABASE_URL", None)
    with contextlib.suppress(SQLAlchemyError):  # pragma: no cover
        reset_lazy_state()


# ---------------------------------------------------------------------------
# Per-test fixtures (shared with test_postgres_session_store)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _deterministic_clock():
    """Install a FakeClock for each test, restore SystemClock after."""
    clock = FakeClock()
    pss_mod.set_clock(clock)
    yield clock
    pss_mod.set_clock(SystemClock())


@pytest.fixture()
def fake_clock(_deterministic_clock: FakeClock) -> FakeClock:
    """Expose the FakeClock for tests that need to manipulate time."""
    return _deterministic_clock


@pytest.fixture()
def store():
    """Fresh PostgresSessionStore instance, cleaned before and after."""
    s = PostgresSessionStore(session_factory=SessionLocal)
    s.reset_sessions()
    yield s
    s.reset_sessions()
