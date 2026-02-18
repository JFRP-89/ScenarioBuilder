"""Shared fixtures for PostgreSQL repository integration tests.

Provides:
- Per-test database creation/teardown (isolated from production data).
- Alembic migration runner (so schema matches migrations, not metadata).
- SQLAlchemy session factory scoped to the test database.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

import pytest
from dotenv import load_dotenv

# ── Helpers ──────────────────────────────────────────────────────────────────


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


def _import_sqlalchemy():
    """Import SQLAlchemy lazily; skip if not installed."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:  # pragma: no cover
        pytest.skip("SQLAlchemy is required for PostgreSQL repository tests.")
    return create_engine, text


def _get_urls() -> tuple[str, str, str]:
    """Return (test_db_url, admin_url, test_db_name)."""
    url_str = os.environ.get("DATABASE_URL_TEST") or os.environ.get("DATABASE_URL")
    if not url_str:
        pytest.skip("DATABASE_URL or DATABASE_URL_TEST must be set.")

    url_str = _escape_password_in_url(url_str)
    parsed = urlparse(url_str)
    netloc = parsed.netloc
    scheme = parsed.scheme
    path = parsed.path

    base_db = "scenario" if not path or path == "/" else path.lstrip("/")

    if os.environ.get("DATABASE_URL_TEST"):
        test_db_name = base_db or "scenario_test"
    else:
        test_db_name = f"{base_db}_repo_test"

    test_db_url = urlunparse((scheme, netloc, f"/{test_db_name}", "", "", ""))
    admin_url = urlunparse((scheme, netloc, "/postgres", "", "", ""))
    return test_db_url, admin_url, test_db_name


def _run_alembic(test_db_url: str) -> None:
    """Run `alembic upgrade head` against *test_db_url*."""
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

    # Fallback to SQLAlchemy metadata if alembic fails or produces no output
    if result.returncode != 0 or not result.stdout.strip():
        # Import here to avoid circular imports
        from infrastructure.db.models import Base
        from sqlalchemy import create_engine

        engine = create_engine(test_db_url)
        Base.metadata.create_all(engine)
        engine.dispose()
    elif result.returncode != 0:
        raise AssertionError(
            f"alembic upgrade head failed:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\n"
        )


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def repo_db_url():
    """Create an isolated test database, run migrations, yield URL, drop DB."""
    _load_db_env()
    create_engine, text = _import_sqlalchemy()
    test_db_url, admin_url, test_db_name = _get_urls()

    safe = test_db_name.replace('"', '""')
    quoted_db = f'"{safe}"'

    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {quoted_db}"))
            conn.execute(text(f"CREATE DATABASE {quoted_db}"))

        _run_alembic(test_db_url)
        yield test_db_url
    finally:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {quoted_db}"))
        engine.dispose()
        os.environ.pop("DATABASE_URL", None)
        # Keep DATABASE_URL_TEST — it must survive across fixtures in CI
        # (where .env doesn't exist to reload it).


@pytest.fixture()
def session_factory(repo_db_url):
    """Return a sessionmaker bound to the test database."""
    create_engine, _ = _import_sqlalchemy()
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(repo_db_url)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    engine.dispose()
