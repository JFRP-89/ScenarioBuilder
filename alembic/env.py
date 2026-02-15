"""Alembic environment configuration.

Reads DATABASE_URL from environment and uses Base.metadata for autogenerate.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from urllib.parse import quote_plus

from sqlalchemy import create_engine, pool

from alembic import context

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

# Allow imports from src/ when running alembic from repo root.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

def _load_env_file(path: str, override: bool = False) -> None:
    """Minimal .env loader for environments without python-dotenv."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if not override and key in os.environ:
                continue
            os.environ[key] = value


if load_dotenv is not None:
    load_dotenv(os.path.join(REPO_ROOT, ".env"), override=True)
else:
    _load_env_file(os.path.join(REPO_ROOT, ".env"), override=True)


def _escape_password_in_url(url_str: str) -> str:
    """Escape special characters in PostgreSQL URL password."""
    if "://" not in url_str or "@" not in url_str:
        return url_str

    scheme_part, rest = url_str.split("://", 1)
    creds_part, host_part = rest.split("@", 1)

    if ":" not in creds_part:
        return url_str

    user, password = creds_part.split(":", 1)
    escaped_password = quote_plus(password)
    return f"{scheme_part}://{user}:{escaped_password}@{host_part}"


def _build_postgres_url_from_env() -> str | None:
    """Build DATABASE_URL from POSTGRES_* env vars when present."""
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db_name = os.environ.get("POSTGRES_DB")
    if not user or not password or not db_name:
        return None

    host = os.environ.get("POSTGRES_HOST", "localhost") or "localhost"
    port = os.environ.get("POSTGRES_PORT")
    port_part = f":{port}" if port else ""
    return f"postgresql://{user}:{quote_plus(password)}@{host}{port_part}/{db_name}"


def _ensure_database_exists(url: str) -> None:
    """Create the target database if it does not exist.

    Connects to the 'postgres' admin database, checks pg_database,
    and issues CREATE DATABASE when necessary.  Uses psycopg2 directly
    to avoid the UnicodeDecodeError that SQLAlchemy raises when the
    target DB is missing on Windows (non-UTF8 error message from server).
    """
    if not url.startswith("postgresql"):
        return

    from urllib.parse import urlparse

    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        return

    # Build admin URL pointing to 'postgres' system database
    admin_url = url.rsplit("/", 1)[0] + "/postgres"

    try:
        import psycopg2

        conn = psycopg2.connect(admin_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
        )
        exists = cur.fetchone() is not None
        if not exists:
            # Identifiers can't be parameterised; safe because db_name
            # comes from our own .env, not user input.
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"  [alembic/env] Created database '{db_name}'")
        cur.close()
        conn.close()
    except Exception as exc:
        # If we can't even reach the admin DB, let Alembic fail with
        # a clearer message from the normal connection path.
        print(f"  [alembic/env] Warning: could not ensure DB exists: {exc}")

from infrastructure.db.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL from env
built_url = _build_postgres_url_from_env()
DATABASE_URL = built_url or os.environ.get("DATABASE_URL") or "sqlite:///./scenario_dev.db"
DATABASE_URL = _escape_password_in_url(DATABASE_URL)

# Create the database if it doesn't exist yet
_ensure_database_exists(DATABASE_URL)

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    # Create engine with url from env var or alembic config
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")
    if not sqlalchemy_url:
        sqlalchemy_url = DATABASE_URL
    
    connectable = create_engine(sqlalchemy_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()
    
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
