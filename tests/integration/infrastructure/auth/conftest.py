"""Shared fixtures for authentication integration tests.

Provides DATABASE_URL setup for tests that need a real PostgreSQL database.
Tests are automatically **skipped** when no DATABASE_URL_TEST is available.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

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


def _ensure_db_and_schema(url: str) -> None:
    """Create the test database (if needed) and run migrations."""
    url = _escape_password_in_url(url)
    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/").split("?")[0] if parsed.path else ""
    if not db_name:
        return

    admin_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/postgres", "", parsed.query, "")
    )

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            if not result.fetchone():
                safe = db_name.replace('"', '""')
                conn.execute(text(f'CREATE DATABASE "{safe}"'))
                logger.info("Created database '%s'", db_name)
        engine.dispose()
    except Exception as exc:
        logger.warning("Could not ensure DB exists: %s", exc)
        return

    # Run alembic migrations
    repo_root = Path(__file__).resolve().parents[4]
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    env["CI"] = "true"  # Prevent alembic/env.py overwriting with .env

    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if proc.returncode != 0 or not proc.stdout.strip():
        try:
            from infrastructure.db.models import Base
            from sqlalchemy import create_engine as ce

            eng = ce(url)
            Base.metadata.create_all(eng)
            eng.dispose()
        except Exception as exc:
            logger.warning("Fallback schema creation failed: %s", exc)


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

    # Ensure the test database and schema exist
    _ensure_db_and_schema(url)

    # SessionLocal reads DATABASE_URL — point it at the test database.
    os.environ["DATABASE_URL"] = url
    logger.info("Auth integration tests: DATABASE_URL → %s", url[:40] + "…")
    yield
    # Tear down: remove DATABASE_URL and reset lazy engine/session globals
    # so stale connections don't leak into subsequent test modules.
    os.environ.pop("DATABASE_URL", None)
    try:
        from infrastructure.db import session as _sess_mod

        if _sess_mod._engine is not None:  # type: ignore[attr-defined]
            _sess_mod._engine.dispose()  # type: ignore[attr-defined]
        _sess_mod._engine = None  # type: ignore[attr-defined]
        _sess_mod._session_local = None  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        pass
