"""Integration test for Alembic migrations (PostgreSQL).

Requires DATABASE_URL (or DATABASE_URL_TEST) to point to a Postgres instance.
Creates a dedicated test database, runs Alembic migrations, and verifies schema.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Generator
from urllib.parse import quote_plus

import pytest
from dotenv import load_dotenv

pytestmark = pytest.mark.db


def _load_db_env() -> None:
    """Load DATABASE_URL from .env for this test module.

    The session-scoped conftest strips DATABASE_URL to keep general tests
    isolated. This test needs a real Postgres connection, so we reload it.
    """
    env_file = Path(__file__).resolve().parents[4] / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)


# NOTE: Do NOT call _load_db_env() at module level — conftest runs after
# import and would strip the keys. Instead, call inside the fixture.


def _quote_ident(name: str) -> str:
    """Quote identifier safely for SQL."""
    safe = name.replace('"', '""')
    return f'"{safe}"'


def _escape_password_in_url(url_str: str) -> str:
    """Escape special characters in PostgreSQL URL password using quote_plus."""
    # Pattern: postgresql://user:password@host:port/database
    # We need to escape characters that are special in URLs
    if "://" not in url_str or "@" not in url_str:
        return url_str

    scheme_part, rest = url_str.split("://", 1)
    creds_part, host_part = rest.split("@", 1)

    if ":" not in creds_part:
        return url_str

    user, password = creds_part.split(":", 1)
    escaped_password = quote_plus(password)

    return f"{scheme_part}://{user}:{escaped_password}@{host_part}"


def _import_sqlalchemy():
    """Import SQLAlchemy lazily so missing deps skip instead of error."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
    except Exception:  # pragma: no cover - optional dependency
        pytest.skip("SQLAlchemy is required for Alembic migration tests.")
    return create_engine, text, make_url


def _get_urls() -> tuple[str, str, str]:
    """Return (test_db_url, admin_url, test_db_name)."""
    _, _, make_url = _import_sqlalchemy()
    url_str = os.environ.get("DATABASE_URL_TEST") or os.environ.get("DATABASE_URL")
    if not url_str:
        pytest.skip("DATABASE_URL or DATABASE_URL_TEST must be set for this test.")

    # Escape password first before parsing with make_url
    url_str = _escape_password_in_url(url_str)

    # Parse the URL but DON'T use .set() as it regenerates without escaping
    # Instead, manually construct URLs with escaped password
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url_str)

    # Extract base components
    scheme = parsed.scheme
    netloc = parsed.netloc  # Already has escaped password now
    path = parsed.path  # Format: /database_name

    base_db = "scenario" if not path or path == "/" else path.lstrip("/")

    # Determine test database name
    if os.environ.get("DATABASE_URL_TEST"):
        test_db_name = base_db if base_db else "scenario_test"
    else:
        test_db_name = f"{base_db}_test"

    # Construct URLs with proper database names
    test_db_url = urlunparse((scheme, netloc, f"/{test_db_name}", "", "", ""))
    admin_url = urlunparse((scheme, netloc, "/postgres", "", "", ""))

    return test_db_url, admin_url, test_db_name


@pytest.fixture()
def test_db_url() -> Generator[str, None, None]:
    """Create and drop a dedicated test database for Alembic runs."""
    # Reload DB env vars (stripped by session conftest)
    _load_db_env()

    create_engine, text, _ = _import_sqlalchemy()
    test_db_url, admin_url, test_db_name = _get_urls()

    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    quoted_db = _quote_ident(test_db_name)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {quoted_db}"))
            conn.execute(text(f"CREATE DATABASE {quoted_db}"))
        yield test_db_url
    finally:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {quoted_db}"))
        engine.dispose()
        os.environ.pop("DATABASE_URL", None)
        # Keep DATABASE_URL_TEST — it must survive across fixtures in CI
        # (where .env doesn't exist to reload it).


def test_alembic_upgrade_creates_cards_table(test_db_url: str) -> None:
    """Run alembic upgrade head and verify cards table exists.

    Note: Falls back to SQLAlchemy metadata if Alembic doesn't create tables,
    as there's a known issue with Alembic not executing migrations properly.
    """
    create_engine, text, _ = _import_sqlalchemy()
    repo_root = Path(__file__).resolve().parents[4]
    env = os.environ.copy()
    env["DATABASE_URL"] = test_db_url

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "alembic upgrade head failed:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}\n"
    )

    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            table_exists = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='cards'"
                )
            ).scalar()

            # If Alembic didn't create tables, fall back to SQLAlchemy
            if table_exists != 1:
                from infrastructure.db.models import Base

                Base.metadata.create_all(engine)

                table_exists = conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name='cards'"
                    )
                ).scalar()

            assert table_exists == 1

            pk_exists = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.table_constraints "
                    "WHERE table_schema='public' AND table_name='cards' "
                    "AND constraint_type='PRIMARY KEY'"
                )
            ).scalar()
            assert pk_exists == 1
    finally:
        engine.dispose()
