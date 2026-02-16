"""Database session management for SQLAlchemy.

Provides a sessionmaker factory and session lifecycle helpers.
Uses DATABASE_URL from environment. Only initializes when DATABASE_URL
points to a real PostgreSQL instance.

Engine and SessionLocal are created lazily on first access so that
importing this module never crashes when DATABASE_URL is missing
(e.g. in lightweight test environments without PostgreSQL).
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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


def _build_engine():
    """Build SQLAlchemy engine from DATABASE_URL.

    Returns ``None`` when DATABASE_URL is empty/unset so that importing
    this module never raises.
    """
    raw_url = os.environ.get("DATABASE_URL", "")
    if not raw_url:
        return None
    url = _escape_password_in_url(raw_url)
    return create_engine(
        url,
        echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
    )


# ---------------------------------------------------------------------------
# Lazy engine / session factory
# ---------------------------------------------------------------------------
_engine = None
_session_local = None


def _get_engine():
    """Return the module-level engine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def _get_session_local():
    """Return the module-level sessionmaker, creating it on first call."""
    global _session_local
    if _session_local is None:
        eng = _get_engine()
        if eng is None:
            raise RuntimeError(
                "DATABASE_URL is not set — cannot create a database session. "
                "Set DATABASE_URL to a valid PostgreSQL connection string."
            )
        _session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=eng
        )
    return _session_local


# Public aliases — kept as module-level *properties* via a tiny wrapper so
# existing ``from infrastructure.db.session import SessionLocal`` still works.
# Engine can legitimately be ``None`` (no DB configured).


class _SessionLocalProxy:
    """Callable proxy that defers sessionmaker creation until first call."""

    def __call__(self, *args, **kwargs):
        return _get_session_local()(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(_get_session_local(), name)


class _EngineProxy:
    """Proxy that defers engine creation until first attribute access."""

    def __getattr__(self, name: str):
        eng = _get_engine()
        if eng is None:
            raise RuntimeError(
                "DATABASE_URL is not set — cannot access the database engine."
            )
        return getattr(eng, name)


engine = _EngineProxy()  # type: ignore[assignment]
SessionLocal = _SessionLocalProxy()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations.

    Usage::

        with get_session() as session:
            repo = PostgresCardRepository(session)
            card = repo.get_by_id("card-123")
            # session is auto-committed on exit if no exception
    """
    factory = _get_session_local()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create database tables based on ORM models.

    Uses the current engine (DATABASE_URL) and creates all tables if missing.
    """
    from infrastructure.db.models import Base

    eng = _get_engine()
    if eng is None:
        raise RuntimeError(
            "DATABASE_URL is not set — cannot initialise the database."
        )
    Base.metadata.create_all(bind=eng)
