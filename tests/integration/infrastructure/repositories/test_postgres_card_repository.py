"""Integration tests for PostgresCardRepository (real PostgreSQL).

Requires a running PostgreSQL instance — see .env / DATABASE_URL.
The ``repo_db_url`` / ``session_factory`` fixtures (in conftest.py)
create a disposable test database and run Alembic migrations.
"""

from __future__ import annotations

import pytest
from domain.cards.card import Card, GameMode
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility

pytestmark = pytest.mark.db

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_card(
    card_id: str = "card-001",
    owner_id: str = "owner-a",
    **overrides,
) -> Card:
    """Build a minimal valid Card with sensible defaults."""
    defaults = {
        "card_id": card_id,
        "owner_id": owner_id,
        "visibility": Visibility.PRIVATE,
        "shared_with": None,
        "mode": GameMode.MATCHED,
        "seed": 42,
        "table": TableSize(width_mm=1200, height_mm=1200),
        "map_spec": MapSpec(
            table=TableSize(width_mm=1200, height_mm=1200),
            shapes=[{"type": "rect", "x": 100, "y": 200, "width": 50, "height": 50}],
            objective_shapes=[{"type": "objective_point", "cx": 600, "cy": 600}],
            deployment_shapes=[
                {
                    "type": "rect",
                    "border": "north",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 300,
                },
            ],
        ),
        "name": "Test Scenario",
        "armies": "Good vs Evil",
        "deployment": "Standard",
        "layout": "Open field",
        "objectives": "Hold Ground",
        "initial_priority": "Good",
        "special_rules": [{"name": "Night Fight", "description": "Reduced visibility"}],
    }
    defaults.update(overrides)
    return Card(**defaults)


def _make_repo(session_factory):
    """Build a PostgresCardRepository from the test session_factory."""
    from infrastructure.repositories.postgres_card_repository import (
        PostgresCardRepository,
    )

    return PostgresCardRepository(session_factory=session_factory)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestPostgresCardRepository:
    """Integration test suite for PostgresCardRepository."""

    def test_save_and_get_roundtrip(self, session_factory) -> None:
        """Save a card, get it back by ID, verify all fields match."""
        repo = _make_repo(session_factory)
        card = _make_card()

        repo.save(card)
        loaded = repo.get_by_id(card.card_id)

        assert loaded is not None
        assert loaded.card_id == card.card_id
        assert loaded.owner_id == card.owner_id
        assert loaded.visibility == card.visibility
        assert loaded.shared_with == card.shared_with
        assert loaded.mode == card.mode
        assert loaded.seed == card.seed
        assert loaded.table.width_mm == card.table.width_mm
        assert loaded.table.height_mm == card.table.height_mm
        assert loaded.map_spec.shapes == card.map_spec.shapes
        assert loaded.map_spec.objective_shapes == card.map_spec.objective_shapes
        assert loaded.map_spec.deployment_shapes == card.map_spec.deployment_shapes
        assert loaded.name == card.name
        assert loaded.armies == card.armies
        assert loaded.deployment == card.deployment
        assert loaded.layout == card.layout
        assert loaded.objectives == card.objectives
        assert loaded.initial_priority == card.initial_priority
        assert loaded.special_rules == card.special_rules

    def test_get_by_id_missing_returns_none(self, session_factory) -> None:
        """get_by_id for a non-existent card returns None."""
        repo = _make_repo(session_factory)
        assert repo.get_by_id("nonexistent-id") is None

    def test_delete_existing_returns_true(self, session_factory) -> None:
        """delete removes an existing card and returns True."""
        repo = _make_repo(session_factory)
        card = _make_card(card_id="to-delete")
        repo.save(card)

        result = repo.delete("to-delete")
        assert result is True
        assert repo.get_by_id("to-delete") is None

    def test_delete_missing_returns_false(self, session_factory) -> None:
        """delete returns False when the card does not exist."""
        repo = _make_repo(session_factory)
        assert repo.delete("no-such-card") is False

    def test_list_all(self, session_factory) -> None:
        """list_all returns all saved cards."""
        repo = _make_repo(session_factory)
        c1 = _make_card(card_id="list-1", name="Alpha")
        c2 = _make_card(card_id="list-2", name="Beta")
        repo.save(c1)
        repo.save(c2)

        cards = repo.list_all()
        ids = {c.card_id for c in cards}
        assert {"list-1", "list-2"} <= ids

    def test_save_upsert_overwrites(self, session_factory) -> None:
        """Saving a card with the same ID updates instead of duplicating."""
        repo = _make_repo(session_factory)
        card_v1 = _make_card(card_id="upsert-1", name="Original")
        repo.save(card_v1)

        card_v2 = _make_card(card_id="upsert-1", name="Updated")
        repo.save(card_v2)

        loaded = repo.get_by_id("upsert-1")
        assert loaded is not None
        assert loaded.name == "Updated"

        # Ensure only one row exists
        all_cards = repo.list_all()
        upsert_cards = [c for c in all_cards if c.card_id == "upsert-1"]
        assert len(upsert_cards) == 1

    def test_shared_with_roundtrip(self, session_factory) -> None:
        """shared_with list survives the save/load cycle."""
        repo = _make_repo(session_factory)
        card = _make_card(
            card_id="shared-1",
            visibility=Visibility.SHARED,
            shared_with=["user-x", "user-y"],
        )
        repo.save(card)

        loaded = repo.get_by_id("shared-1")
        assert loaded is not None
        assert loaded.visibility == Visibility.SHARED
        assert sorted(loaded.shared_with) == ["user-x", "user-y"]

    def test_dict_objectives_roundtrip(self, session_factory) -> None:
        """Objectives stored as a dict survive the save/load cycle."""
        repo = _make_repo(session_factory)
        objectives_dict = {"primary": "Hold Ground", "secondary": "Secure Flanks"}
        card = _make_card(card_id="obj-dict", objectives=objectives_dict)
        repo.save(card)

        loaded = repo.get_by_id("obj-dict")
        assert loaded is not None
        assert loaded.objectives == objectives_dict
