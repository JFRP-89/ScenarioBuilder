"""
RED tests for ListCards use case.

ListCards returns a list of cards visible to the actor based on a filter.

MVP Contract:
1. filter="mine" returns only actor's own cards
2. filter="public" returns only public cards (any owner)
3. filter="shared_with_me" returns SHARED cards where actor is in shared_with
4. Security: never returns a PRIVATE card owned by someone else
5. actor_id invalid → ValidationError
6. filter invalid → ValidationError
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


# =============================================================================
# CARD FACTORIES
# =============================================================================
def make_card(
    card_id: str,
    owner_id: str,
    visibility: Visibility,
    table: TableSize,
    map_spec: MapSpec,
    shared_with: Optional[list[str]] = None,
    mode: GameMode = GameMode.MATCHED,
    seed: int = 42,
) -> Card:
    """Factory to create valid Card instances for testing."""
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=shared_with,
        mode=mode,
        seed=seed,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# TEST DOUBLES
# =============================================================================
class FakeCardRepository:
    """In-memory fake repository for testing."""

    def __init__(self, cards: Optional[list[Card]] = None) -> None:
        self.cards: list[Card] = cards or []

    def list_all(self) -> list[Card]:
        """Return all cards in repository."""
        return list(self.cards)

    def add(self, card: Card) -> None:
        """Add a card to the repository."""
        self.cards.append(card)


# =============================================================================
# 1) MINE - RETURNS ONLY ACTOR'S OWN CARDS
# =============================================================================
class TestListCardsMine:
    """filter='mine' returns only cards owned by actor."""

    def test_mine_returns_only_actors_cards(self, table: TableSize, map_spec: MapSpec):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        # Arrange: u1 owns 2 cards, u2 owns 1 card
        card_u1_private = make_card("card-001", "u1", Visibility.PRIVATE, table, map_spec)
        card_u1_public = make_card("card-002", "u1", Visibility.PUBLIC, table, map_spec)
        card_u2_public = make_card("card-003", "u2", Visibility.PUBLIC, table, map_spec)

        repo = FakeCardRepository([card_u1_private, card_u1_public, card_u2_public])
        use_case = ListCards(repository=repo)

        # Act
        request = ListCardsRequest(actor_id="u1", filter="mine")
        response = use_case.execute(request)

        # Assert: only u1's cards
        assert len(response.cards) == 2
        card_ids = {c.card_id for c in response.cards}
        assert card_ids == {"card-001", "card-002"}
        for card in response.cards:
            assert card.owner_id == "u1"


# =============================================================================
# 2) PUBLIC - RETURNS ONLY PUBLIC CARDS (ANY OWNER)
# =============================================================================
class TestListCardsPublic:
    """filter='public' returns only public cards from any owner."""

    def test_public_returns_only_public_cards(self, table: TableSize, map_spec: MapSpec):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        # Arrange: mix of visibilities
        card_u1_private = make_card("card-001", "u1", Visibility.PRIVATE, table, map_spec)
        card_u1_public = make_card("card-002", "u1", Visibility.PUBLIC, table, map_spec)
        card_u2_public = make_card("card-003", "u2", Visibility.PUBLIC, table, map_spec)
        card_u2_shared = make_card(
            "card-004", "u2", Visibility.SHARED, table, map_spec, shared_with=["u3"]
        )

        repo = FakeCardRepository([card_u1_private, card_u1_public, card_u2_public, card_u2_shared])
        use_case = ListCards(repository=repo)

        # Act
        request = ListCardsRequest(actor_id="u1", filter="public")
        response = use_case.execute(request)

        # Assert: only public cards
        assert len(response.cards) == 2
        for card in response.cards:
            assert card.visibility == "public"
        card_ids = {c.card_id for c in response.cards}
        assert card_ids == {"card-002", "card-003"}


# =============================================================================
# 3) SHARED_WITH_ME - RETURNS SHARED CARDS WHERE ACTOR IS IN SHARED_WITH
# =============================================================================
class TestListCardsSharedWithMe:
    """filter='shared_with_me' returns SHARED cards where actor is in shared_with."""

    def test_shared_with_me_returns_correct_cards(self, table: TableSize, map_spec: MapSpec):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        # Arrange
        card_shared_with_u2 = make_card(
            "card-001", "u1", Visibility.SHARED, table, map_spec, shared_with=["u2"]
        )
        card_shared_with_u3 = make_card(
            "card-002", "u1", Visibility.SHARED, table, map_spec, shared_with=["u3"]
        )
        card_shared_with_u2_and_u3 = make_card(
            "card-003",
            "u1",
            Visibility.SHARED,
            table,
            map_spec,
            shared_with=["u2", "u3"],
        )
        card_public = make_card("card-004", "u1", Visibility.PUBLIC, table, map_spec)

        repo = FakeCardRepository(
            [
                card_shared_with_u2,
                card_shared_with_u3,
                card_shared_with_u2_and_u3,
                card_public,
            ]
        )
        use_case = ListCards(repository=repo)

        # Act: u2 asks for shared_with_me
        request = ListCardsRequest(actor_id="u2", filter="shared_with_me")
        response = use_case.execute(request)

        # Assert: only cards where u2 is in shared_with
        assert len(response.cards) == 2
        card_ids = {c.card_id for c in response.cards}
        assert card_ids == {"card-001", "card-003"}
        for card in response.cards:
            assert card.visibility == "shared"


# =============================================================================
# 4) SECURITY: NEVER RETURNS A PRIVATE CARD OWNED BY SOMEONE ELSE
# =============================================================================
class TestListCardsSecurityPrivate:
    """Never returns a PRIVATE card owned by someone else."""

    def test_public_filter_does_not_leak_private_cards(self, table: TableSize, map_spec: MapSpec):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        # Arrange: u1 has a PRIVATE card
        card_u1_private = make_card("card-001", "u1", Visibility.PRIVATE, table, map_spec)
        card_u1_public = make_card("card-002", "u1", Visibility.PUBLIC, table, map_spec)

        repo = FakeCardRepository([card_u1_private, card_u1_public])
        use_case = ListCards(repository=repo)

        # Act: u2 asks for public
        request = ListCardsRequest(actor_id="u2", filter="public")
        response = use_case.execute(request)

        # Assert: u1's PRIVATE card is NOT returned
        card_ids = {c.card_id for c in response.cards}
        assert "card-001" not in card_ids
        # Only public card returned
        assert card_ids == {"card-002"}

    def test_shared_with_me_does_not_leak_private_cards(self, table: TableSize, map_spec: MapSpec):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        # Arrange
        card_u1_private = make_card("card-001", "u1", Visibility.PRIVATE, table, map_spec)
        card_u1_shared = make_card(
            "card-002", "u1", Visibility.SHARED, table, map_spec, shared_with=["u2"]
        )

        repo = FakeCardRepository([card_u1_private, card_u1_shared])
        use_case = ListCards(repository=repo)

        # Act: u2 asks for shared_with_me
        request = ListCardsRequest(actor_id="u2", filter="shared_with_me")
        response = use_case.execute(request)

        # Assert: u1's PRIVATE card is NOT returned
        card_ids = {c.card_id for c in response.cards}
        assert "card-001" not in card_ids
        assert card_ids == {"card-002"}


# =============================================================================
# 5) INVALID ACTOR_ID
# =============================================================================
class TestListCardsInvalidActorId:
    """Invalid actor_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_actor_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_actor_id_raises_error(
        self,
        table: TableSize,
        map_spec: MapSpec,
        invalid_actor_id: Optional[str],
    ):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        repo = FakeCardRepository([])
        use_case = ListCards(repository=repo)

        request = ListCardsRequest(actor_id=invalid_actor_id, filter="mine")

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)


# =============================================================================
# 6) INVALID FILTER
# =============================================================================
class TestListCardsInvalidFilter:
    """Invalid filter raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_filter",
        ["", "all", "everything", None, "private", "MY_CARDS"],
        ids=["empty", "all", "everything", "none", "private", "wrong_case"],
    )
    def test_invalid_filter_raises_error(
        self,
        table: TableSize,
        map_spec: MapSpec,
        invalid_filter: Optional[str],
    ):
        from application.use_cases.list_cards import ListCards, ListCardsRequest

        repo = FakeCardRepository([])
        use_case = ListCards(repository=repo)

        request = ListCardsRequest(actor_id="u1", filter=invalid_filter)

        with pytest.raises(ValidationError, match="(?i)filter"):
            use_case.execute(request)


# =============================================================================
# TODO(future): Additional tests for hardening phase:
# - Test pagination
# - Test sorting
# - Test empty results
# - Test large datasets
# - Test response includes table_mm and shapes
# =============================================================================
