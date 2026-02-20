"""Legacy application use case tests.

These tests are being migrated to new hexagonal architecture with DTOs.
Tests for SaveCard have been migrated to tests/unit/application/test_save_card.py
Tests for GetCard have been migrated to tests/unit/application/test_get_card.py
Tests for GenerateScenarioCard exist in tests/unit/application/test_generate_scenario_card.py
"""

# New API imports
from typing import Any

import application
from application.ports import (
    content_provider,
    current_user_provider,
    map_renderer,
    repositories,
)
from application.use_cases.manage_presets import list_presets
from application.use_cases.save_card import SaveCard, SaveCardRequest
from domain.cards.card import Card, GameMode
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility


class DummyRepo:
    """Legacy repository for old functional API tests."""

    def __init__(self) -> None:
        self.saved: list[Any] = []

    def save(self, card) -> None:
        """New API: save(card) without owner_id."""
        self.saved.append(card)

    def list_for_owner(self, owner_id: str):
        return [c for c in self.saved if c.owner_id == owner_id]

    def get_by_id(self, card_id: str):
        for card in self.saved:
            if card.card_id == card_id:
                return card
        return None


def test_save_and_list_cards_new_api():
    """Migrated test using new SaveCard use case with DTOs."""
    # Create a valid Card using domain objects
    table = TableSize.standard()
    shapes = [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]
    map_spec = MapSpec(table=table, shapes=shapes)

    card = Card(
        card_id="card-test",
        owner_id="u1",
        visibility=Visibility.PRIVATE,
        shared_with=None,
        mode=GameMode.CASUAL,
        seed=7,
        table=table,
        map_spec=map_spec,
    )

    # Use new SaveCard API
    repo = DummyRepo()
    save_use_case = SaveCard(repository=repo)
    request = SaveCardRequest(actor_id="u1", card=card)
    response = save_use_case.execute(request)

    assert response.card_id == "card-test"
    assert len(repo.saved) == 1
    assert repo.saved[0].owner_id == "u1"

    # List cards via repo
    assert len(list(repo.list_for_owner("u1"))) == 1


def test_list_presets():
    presets = list_presets()
    assert any(p["id"] == "standard" for p in presets)


def test_ports_importable():
    assert application is not None
    assert content_provider is not None
    assert current_user_provider is not None
    assert map_renderer is not None
    assert repositories is not None
