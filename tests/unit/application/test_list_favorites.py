"""
RED tests for ListFavorites use case.

ListFavorites returns card_ids that actor has marked as favorite,
filtered to only include cards the actor can still read.

MVP Contract:
1. Returns list of favorite card_ids
2. Filters out cards that no longer exist
3. Filters out cards actor can no longer read (security)
4. actor_id invalid → ValidationError
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
) -> Card:
    """Factory to create valid Card instances for testing."""
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=shared_with,
        mode=GameMode.MATCHED,
        seed=123,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# TEST DOUBLES
# =============================================================================
class FakeCardRepository:
    """In-memory fake card repository for testing."""

    def __init__(self, cards: Optional[dict[str, Card]] = None) -> None:
        self.cards: dict[str, Card] = cards or {}

    def get_by_id(self, card_id: str) -> Optional[Card]:
        return self.cards.get(card_id)

    def save(self, card: Card) -> None:
        self.cards[card.card_id] = card

    def find_by_seed(self, seed: int) -> Optional[Card]:
        return next((c for c in self.cards.values() if c.seed == seed), None)

    def delete(self, card_id: str) -> bool:
        return self.cards.pop(card_id, None) is not None

    def list_all(self) -> list[Card]:
        return list(self.cards.values())

    def list_for_owner(self, owner_id: str) -> list[Card]:
        return [c for c in self.cards.values() if c.owner_id == owner_id]


class FakeFavoritesRepository:
    """In-memory fake favorites repository for testing."""

    def __init__(self) -> None:
        self._favorites: set[tuple[str, str]] = set()

    def is_favorite(self, actor_id: str, card_id: str) -> bool:
        return (actor_id, card_id) in self._favorites

    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None:
        key = (actor_id, card_id)
        if value:
            self._favorites.add(key)
        else:
            self._favorites.discard(key)

    def list_favorites(self, actor_id: str) -> list[str]:
        return [card_id for (uid, card_id) in self._favorites if uid == actor_id]

    def remove_all_for_card(self, card_id: str) -> None:
        self._favorites = {(a, c) for a, c in self._favorites if c != card_id}


# =============================================================================
# FIXTURES - Repositories
# =============================================================================
@pytest.fixture
def favorites_repo() -> FakeFavoritesRepository:
    return FakeFavoritesRepository()


# =============================================================================
# 1) HAPPY PATH: RETURNS LIST OF FAVORITE CARD_IDS
# =============================================================================
class TestListFavoritesHappyPath:
    """Returns list of favorite card_ids."""

    def test_returns_favorite_cards(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        # Arrange: 2 PUBLIC cards, u2 favorites both
        card1 = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card2 = make_card("c2", "u1", Visibility.PUBLIC, table, map_spec)
        card3 = make_card(
            "c3", "u1", Visibility.PUBLIC, table, map_spec
        )  # not favorited
        card_repo = FakeCardRepository({"c1": card1, "c2": card2, "c3": card3})

        favorites_repo.set_favorite("u2", "c1", True)
        favorites_repo.set_favorite("u2", "c2", True)

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        request = ListFavoritesRequest(actor_id="u2")
        response = use_case.execute(request)

        # Assert
        assert set(response.card_ids) == {"c1", "c2"}


# =============================================================================
# 2) FILTERS OUT CARDS THAT NO LONGER EXIST
# =============================================================================
class TestListFavoritesFiltersMissing:
    """Filters out cards that no longer exist."""

    def test_filters_out_deleted_cards(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        # Arrange: only c1 exists, but user favorited c1 and c2
        card1 = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card_repo = FakeCardRepository({"c1": card1})  # c2 doesn't exist

        favorites_repo.set_favorite("u2", "c1", True)
        favorites_repo.set_favorite("u2", "c2", True)  # card doesn't exist

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        request = ListFavoritesRequest(actor_id="u2")
        response = use_case.execute(request)

        # Assert: only c1 returned
        assert response.card_ids == ["c1"]


# =============================================================================
# 3) SECURITY: FILTERS OUT CARDS ACTOR CAN NO LONGER READ
# =============================================================================
class TestListFavoritesSecurityFilter:
    """Filters out cards actor can no longer read."""

    def test_filters_out_unreadable_cards(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        # Arrange: c1 is PUBLIC (readable), c2 is PRIVATE by u1 (not readable by u2)
        card1 = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card2 = make_card("c2", "u1", Visibility.PRIVATE, table, map_spec)
        card_repo = FakeCardRepository({"c1": card1, "c2": card2})

        # Both favorited (maybe c2 was public before)
        favorites_repo.set_favorite("u2", "c1", True)
        favorites_repo.set_favorite("u2", "c2", True)

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        request = ListFavoritesRequest(actor_id="u2")
        response = use_case.execute(request)

        # Assert: only c1 returned (c2 is PRIVATE, not readable)
        assert response.card_ids == ["c1"]


# =============================================================================
# 3b) STALE FAVORITES PRUNING: deleted cards cleaned from DB
# =============================================================================
class TestListFavoritesPrunesDeletedCards:
    """Stale favorites for deleted cards are removed from the DB."""

    def test_deleted_card_favorite_is_removed_from_repo(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        # Arrange: c1 exists, c2 was deleted
        card1 = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card_repo = FakeCardRepository({"c1": card1})

        favorites_repo.set_favorite("u2", "c1", True)
        favorites_repo.set_favorite("u2", "c2", True)  # stale

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        use_case.execute(ListFavoritesRequest(actor_id="u2"))

        # Assert: stale entry removed from underlying repo
        assert not favorites_repo.is_favorite("u2", "c2")
        assert favorites_repo.is_favorite("u2", "c1")


# =============================================================================
# 3c) STALE FAVORITES PRUNING: unreadable cards cleaned from DB
# =============================================================================
class TestListFavoritesPrunesUnreadableCards:
    """Stale favorites for cards no longer readable are removed from the DB."""

    def test_private_card_favorite_is_removed_from_repo(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        # Arrange: c2 became PRIVATE — u2 can no longer read it
        card1 = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card2 = make_card("c2", "u1", Visibility.PRIVATE, table, map_spec)
        card_repo = FakeCardRepository({"c1": card1, "c2": card2})

        favorites_repo.set_favorite("u2", "c1", True)
        favorites_repo.set_favorite("u2", "c2", True)  # stale

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        use_case.execute(ListFavoritesRequest(actor_id="u2"))

        # Assert: stale entry pruned
        assert not favorites_repo.is_favorite("u2", "c2")
        assert favorites_repo.is_favorite("u2", "c1")

    def test_shared_card_no_longer_shared_is_pruned(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        # Arrange: c2 is SHARED with u3 only — u2 was removed from share list
        card1 = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card2 = make_card(
            "c2", "u1", Visibility.SHARED, table, map_spec, shared_with=["u3"]
        )
        card_repo = FakeCardRepository({"c1": card1, "c2": card2})

        favorites_repo.set_favorite("u2", "c1", True)
        favorites_repo.set_favorite("u2", "c2", True)  # stale

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        use_case.execute(ListFavoritesRequest(actor_id="u2"))

        # Assert: stale entry for c2 removed
        assert not favorites_repo.is_favorite("u2", "c2")
        assert favorites_repo.is_favorite("u2", "c1")


# =============================================================================
# 4) INVALID ACTOR_ID
# =============================================================================
class TestListFavoritesInvalidActorId:
    """Invalid actor_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_actor_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_actor_id_raises_error(
        self,
        favorites_repo: FakeFavoritesRepository,
        invalid_actor_id: Optional[str],
    ):
        from application.use_cases.list_favorites import (
            ListFavorites,
            ListFavoritesRequest,
        )

        card_repo = FakeCardRepository({})

        use_case = ListFavorites(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        request = ListFavoritesRequest(actor_id=invalid_actor_id)

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)


# =============================================================================
# TODO(future): Additional tests for hardening phase:
# - Test empty favorites list
# - Test pagination
# - Test favorites count limit
# =============================================================================
