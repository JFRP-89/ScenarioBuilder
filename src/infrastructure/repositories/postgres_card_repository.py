"""PostgreSQL implementation of CardRepository using SQLAlchemy ORM.

Maps between domain.cards.card.Card and infrastructure.db.models.CardModel.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from domain.cards.card import Card, parse_game_mode
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.db.models import CardModel
from sqlalchemy.orm import Session


class PostgresCardRepository:
    """PostgreSQL implementation of CardRepository port.

    Uses SQLAlchemy ORM for persistence.
    Receives a session_factory so each operation gets a fresh session,
    avoiding leaked connections in long-running processes.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save(self, card: Card) -> None:
        """Save a card to PostgreSQL.

        Converts domain Card → CardModel, then insert or update (upsert).
        """
        session = self._session_factory()
        try:
            model = session.query(CardModel).filter_by(card_id=card.card_id).first()

            if model is None:
                model = CardModel(card_id=card.card_id)

            model.owner_id = card.owner_id
            model.visibility = card.visibility.value
            model.shared_with = list(card.shared_with) if card.shared_with else None
            model.mode = card.mode.value
            model.seed = card.seed
            model.table_width = card.table.width_mm
            model.table_height = card.table.height_mm
            model.table_unit = "mm"
            model.map_spec = self._map_spec_to_json(card.map_spec)
            model.name = card.name
            model.armies = card.armies
            model.deployment = card.deployment
            model.layout = card.layout
            model.objectives = (
                card.objectives
                if isinstance(card.objectives, (dict, type(None)))
                else str(card.objectives)
            )
            model.initial_priority = card.initial_priority
            model.special_rules = card.special_rules

            session.add(model)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, card_id: str) -> Optional[Card]:
        """Retrieve a card by ID, or None if not found."""
        session = self._session_factory()
        try:
            model = session.query(CardModel).filter_by(card_id=card_id).first()
            if model is None:
                return None
            return self._model_to_domain(model)
        finally:
            session.close()

    def delete(self, card_id: str) -> bool:
        """Delete a card by ID. Returns True if found and deleted."""
        session = self._session_factory()
        try:
            model = session.query(CardModel).filter_by(card_id=card_id).first()
            if model is None:
                return False
            session.delete(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_all(self) -> list[Card]:
        """List all cards in the database."""
        session = self._session_factory()
        try:
            models = session.query(CardModel).all()
            return [self._model_to_domain(m) for m in models]
        finally:
            session.close()

    # ── Serialization helpers ────────────────────────────────────────────────

    @staticmethod
    def _map_spec_to_json(map_spec: MapSpec) -> dict[str, Any]:
        """Convert MapSpec domain object to JSON-serializable dict."""
        return {
            "table": {
                "width_mm": map_spec.table.width_mm,
                "height_mm": map_spec.table.height_mm,
            },
            "shapes": map_spec.shapes,
            "objective_shapes": map_spec.objective_shapes,
            "deployment_shapes": map_spec.deployment_shapes,
        }

    @staticmethod
    def _json_to_map_spec(data: dict[str, Any]) -> MapSpec:
        """Convert JSON dict back to MapSpec domain object."""
        table_data = data.get("table", {})
        table = TableSize(
            width_mm=table_data.get("width_mm", 1200),
            height_mm=table_data.get("height_mm", 1200),
        )
        return MapSpec(
            table=table,
            shapes=data.get("shapes", []),
            objective_shapes=data.get("objective_shapes"),
            deployment_shapes=data.get("deployment_shapes"),
        )

    def _model_to_domain(self, model: CardModel) -> Card:
        """Convert CardModel (ORM) → Card (domain)."""
        return Card(
            card_id=model.card_id,
            owner_id=model.owner_id,
            visibility=Visibility(model.visibility),
            shared_with=model.shared_with if model.shared_with else None,
            mode=parse_game_mode(model.mode),
            seed=model.seed,
            table=TableSize(
                width_mm=model.table_width,
                height_mm=model.table_height,
            ),
            map_spec=self._json_to_map_spec(model.map_spec),
            name=model.name,
            armies=model.armies,
            deployment=model.deployment,
            layout=model.layout,
            objectives=model.objectives,
            initial_priority=model.initial_priority,
            special_rules=model.special_rules,
        )
