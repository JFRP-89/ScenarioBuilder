"""
RED tests for SaveCard use case.

SaveCard persists a Card entity to the repository.
Only the card owner can save their own card.

MVP Contract:
1. Happy path: actor == owner → saves and returns card_id
2. actor_id invalid (None, "", "   ") → ValidationError
3. actor != owner → Forbidden (Exception)
"""

from __future__ import annotations

from typing import Optional

import pytest

# Domain imports (real)
from domain.cards.card import Card, GameMode
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility


# =============================================================================
# FIXTURES - Valid domain objects
# =============================================================================
@pytest.fixture
def table() -> TableSize:
    return TableSize.standard()


@pytest.fixture
def valid_shapes() -> list[dict]:
    """Shapes valid for standard table (1200x1200 mm)."""
    return [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]


@pytest.fixture
def map_spec(table: TableSize, valid_shapes: list[dict]) -> MapSpec:
    return MapSpec(table=table, shapes=valid_shapes)


@pytest.fixture
def valid_card(table: TableSize, map_spec: MapSpec) -> Card:
    """A valid Card owned by 'owner-123'."""
    return Card(
        card_id="card-001",
        owner_id="owner-123",
        visibility=Visibility.PRIVATE,
        shared_with=None,
        mode=GameMode.MATCHED,
        seed=42,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# TEST DOUBLES
# =============================================================================
class FakeCardRepository:
    """In-memory fake repository for testing."""

    def __init__(self) -> None:
        self.saved_cards: dict[str, Card] = {}
        self.save_calls: list[Card] = []

    def save(self, card: Card) -> None:
        self.save_calls.append(card)
        self.saved_cards[card.card_id] = card

    def get_by_id(self, card_id: str) -> Optional[Card]:
        return self.saved_cards.get(card_id)

    def find_by_seed(self, seed: int) -> Optional[Card]:
        return next((c for c in self.saved_cards.values() if c.seed == seed), None)

    def delete(self, card_id: str) -> bool:
        return self.saved_cards.pop(card_id, None) is not None

    def list_all(self) -> list[Card]:
        return list(self.saved_cards.values())

    def list_for_owner(self, owner_id: str) -> list[Card]:
        return [c for c in self.saved_cards.values() if c.owner_id == owner_id]


@pytest.fixture
def fake_repository() -> FakeCardRepository:
    return FakeCardRepository()


# =============================================================================
# 1) HAPPY PATH
# =============================================================================
class TestSaveCardHappyPath:
    """Actor == owner → saves and returns card_id."""

    def test_saves_card_when_actor_is_owner(
        self, valid_card: Card, fake_repository: FakeCardRepository
    ):
        # Lazy import - will fail in RED phase
        from application.use_cases.save_card import SaveCard, SaveCardRequest

        use_case = SaveCard(repository=fake_repository)
        request = SaveCardRequest(
            actor_id="owner-123",  # Same as card.owner_id
            card=valid_card,
        )

        result = use_case.execute(request)

        # Card was saved
        assert len(fake_repository.save_calls) == 1
        assert fake_repository.save_calls[0] == valid_card
        # Returns card_id
        assert result.card_id == "card-001"


# =============================================================================
# 2) INVALID ACTOR_ID
# =============================================================================
class TestSaveCardInvalidActorId:
    """Invalid actor_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_actor_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_actor_id_raises_error(
        self,
        valid_card: Card,
        fake_repository: FakeCardRepository,
        invalid_actor_id: Optional[str],
    ):
        from application.use_cases.save_card import SaveCard, SaveCardRequest

        use_case = SaveCard(repository=fake_repository)
        request = SaveCardRequest(
            actor_id=invalid_actor_id,
            card=valid_card,
        )

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)

        # Card was NOT saved
        assert len(fake_repository.save_calls) == 0


# =============================================================================
# 3) FORBIDDEN: ACTOR != OWNER
# =============================================================================
class TestSaveCardForbidden:
    """Actor != owner raises Forbidden error."""

    def test_actor_not_owner_raises_forbidden(
        self, valid_card: Card, fake_repository: FakeCardRepository
    ):
        from application.use_cases.save_card import SaveCard, SaveCardRequest

        use_case = SaveCard(repository=fake_repository)
        request = SaveCardRequest(
            actor_id="other-user",  # NOT the owner
            card=valid_card,  # owner_id="owner-123"
        )

        # Expect some kind of forbidden/permission error
        with pytest.raises(Exception, match="(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        # Card was NOT saved
        assert len(fake_repository.save_calls) == 0


# =============================================================================
# TODO(future): Additional tests for hardening phase:
# - Test saving card with SHARED visibility
# - Test saving card with PUBLIC visibility
# - Test repository failure handling
# - Test concurrent saves
# =============================================================================
