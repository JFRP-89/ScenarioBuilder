"""SQLAlchemy ORM models for PostgreSQL persistence.

These models map domain entities (Card) to database tables.
They live in the infrastructure layer and are not imported by domain/application.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


class CardModel(Base):
    """SQLAlchemy model for Card domain entity.

    Maps to cards table in PostgreSQL.
    Stores all Card attributes including MapSpec and nested data as JSON.
    """

    __tablename__ = "cards"

    # Primary key
    card_id = Column(String(255), primary_key=True, nullable=False)

    # Ownership and visibility
    owner_id = Column(String(255), nullable=False, index=True)
    visibility = Column(String(20), nullable=False, index=True)  # PRIVATE/SHARED/PUBLIC
    shared_with = Column(JSON, nullable=True)  # List[str] or None

    # Core scenario attributes
    mode = Column(String(20), nullable=False, index=True)  # CASUAL/NARRATIVE/MATCHED
    seed = Column(Integer, nullable=False)
    table_width = Column(Integer, nullable=False)
    table_height = Column(Integer, nullable=False)
    table_unit = Column(String(10), nullable=False)  # cm/inch

    # Map specification (stored as JSON)
    map_spec = Column(JSON, nullable=False)

    # Optional fields
    name = Column(String(500), nullable=True)
    armies = Column(Text, nullable=True)
    deployment = Column(Text, nullable=True)
    layout = Column(Text, nullable=True)
    objectives = Column(JSON, nullable=True)  # str or dict
    initial_priority = Column(String(255), nullable=True)
    special_rules = Column(JSON, nullable=True)  # List[dict] or None

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<CardModel(card_id={self.card_id!r}, owner={self.owner_id!r}, mode={self.mode!r})>"


class FavoritesModel(Base):
    """SQLAlchemy model for user favorites.

    Maps to favorites table in PostgreSQL.
    Composite PK (actor_id, card_id) mirrors the InMemory set[tuple[str, str]].
    """

    __tablename__ = "favorites"

    actor_id = Column(String(255), primary_key=True, nullable=False)
    card_id = Column(String(255), primary_key=True, nullable=False)

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<FavoritesModel(actor={self.actor_id!r}, card={self.card_id!r})>"


class UserModel(Base):
    """SQLAlchemy model for user authentication.

    Maps to users table in PostgreSQL.
    Stores username (PK), password hash, salt, name, and email.
    """

    __tablename__ = "users"

    username = Column(String(255), primary_key=True, nullable=False, index=True)
    password_hash = Column(LargeBinary, nullable=False)
    salt = Column(LargeBinary, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<UserModel(username={self.username!r}, name={self.name!r})>"


class SessionModel(Base):
    """SQLAlchemy model for server-side sessions.

    Maps to sessions table in PostgreSQL.
    Stores session data: session_id, username, timestamps, CSRF, revocation.
    """

    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True, nullable=False)
    username = Column(String(255), nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # CSRF token (stored as plaintext hex — already cryptographically random)
    csrf_token = Column(String(64), nullable=False)

    # Reauth timestamp (nullable — set when re-authentication occurs)
    reauth_at = Column(DateTime(timezone=True), nullable=True)

    # Soft-revocation timestamp (set on logout / rotate-out)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sessions_expires_at", "expires_at"),
        Index("ix_sessions_revoked_at", "revoked_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SessionModel(session_id={self.session_id[:8]!r}…, "
            f"username={self.username!r})>"
        )
