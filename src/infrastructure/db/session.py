"""Database session management for SQLAlchemy.

Provides a sessionmaker factory and session lifecycle helpers.
Uses DATABASE_URL from environment. Only initializes when DATABASE_URL
points to a real PostgreSQL instance.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import quote_plus

from infrastructure.db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


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
    """Build SQLAlchemy engine from DATABASE_URL."""
    raw_url = os.environ.get("DATABASE_URL", "")
    url = _escape_password_in_url(raw_url) if raw_url else raw_url
    return create_engine(
        url,
        echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
    )


# Engine and session factory — lazily initialized in build_services()
engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations.

    Usage::

        with get_session() as session:
            repo = PostgresCardRepository(session)
            card = repo.get_by_id("card-123")
            # session is auto-committed on exit if no exception
    """
    session = SessionLocal()
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
    Base.metadata.create_all(bind=engine)
