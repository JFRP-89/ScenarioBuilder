"""Shared fixtures for infrastructure/db integration tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from infrastructure.db.session import escape_password_in_url


def _load_db_env() -> None:
    """Load DATABASE_URL from .env for this test module.

    The session-scoped conftest strips DATABASE_URL to keep general tests
    isolated. This test needs a real Postgres connection, so we reload it.
    """
    env_file = Path(__file__).resolve().parents[4] / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)


def _quote_ident(name: str) -> str:
    """Quote identifier safely for SQL."""
    safe = name.replace('"', '""')
    return f'"{safe}"'


def _get_urls() -> tuple[str, str, str]:
    """Return (db_url, admin_url, db_name)."""
    url_str = os.environ.get("DATABASE_URL_TEST") or os.environ.get(
        "DATABASE_URL",
    )
    if not url_str:
        pytest.skip(
            "DATABASE_URL or DATABASE_URL_TEST must be set for this test.",
        )

    url_str = escape_password_in_url(url_str)
    parsed = urlparse(url_str)

    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path

    base_db = "scenario" if not path or path == "/" else path.lstrip("/")
    db_name = f"{base_db}_alembic"

    db_url = urlunparse(
        (scheme, netloc, f"/{db_name}", "", parsed.query, ""),
    )
    admin_url = urlunparse(
        (scheme, netloc, "/postgres", "", parsed.query, ""),
    )

    return db_url, admin_url, db_name


@pytest.fixture()
def alembic_db_url() -> Generator[str, None, None]:
    """Create and drop a dedicated test database for Alembic runs."""
    _load_db_env()

    db_url, admin_url, db_name = _get_urls()

    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    quoted_db = _quote_ident(db_name)
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :db AND pid != pg_backend_pid()"
                ),
                {"db": db_name},
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {quoted_db}"))
            conn.execute(text(f"CREATE DATABASE {quoted_db}"))
        yield db_url
    finally:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :db AND pid != pg_backend_pid()"
                ),
                {"db": db_name},
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {quoted_db}"))
        engine.dispose()
        os.environ.pop("DATABASE_URL", None)
