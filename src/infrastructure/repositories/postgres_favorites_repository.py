"""PostgreSQL implementation of FavoritesRepository using SQLAlchemy ORM.

Maps between domain favorites (actor_id, card_id) pairs and
infrastructure.db.models.FavoritesModel.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from infrastructure.db.models import FavoritesModel
from sqlalchemy.orm import Session


class PostgresFavoritesRepository:
    """PostgreSQL implementation of FavoritesRepository port.

    Uses SQLAlchemy ORM for persistence.
    Receives a session_factory so each operation gets a fresh session.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def is_favorite(self, actor_id: str, card_id: str) -> bool:
        """Check if a card is favorited by an actor."""
        session = self._session_factory()
        try:
            model = (
                session.query(FavoritesModel)
                .filter_by(actor_id=actor_id, card_id=card_id)
                .first()
            )
            return model is not None
        finally:
            session.close()

    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None:
        """Set or unset a card as favorite for an actor.

        When value=True, inserts a row (idempotent — skips if exists).
        When value=False, deletes the row (idempotent — noop if absent).
        """
        session = self._session_factory()
        try:
            existing = (
                session.query(FavoritesModel)
                .filter_by(actor_id=actor_id, card_id=card_id)
                .first()
            )

            if value:
                if existing is None:
                    model = FavoritesModel(
                        actor_id=actor_id,
                        card_id=card_id,
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(model)
                    session.commit()
                # If already exists, do nothing (idempotent).
            else:
                if existing is not None:
                    session.delete(existing)
                    session.commit()
                # If not present, do nothing (idempotent).
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_favorites(self, actor_id: str) -> list[str]:
        """List all favorite card_ids for an actor, sorted lexicographically."""
        session = self._session_factory()
        try:
            models = (
                session.query(FavoritesModel)
                .filter_by(actor_id=actor_id)
                .order_by(FavoritesModel.card_id)
                .all()
            )
            return [m.card_id for m in models]  # type: ignore[misc]
        finally:
            session.close()
