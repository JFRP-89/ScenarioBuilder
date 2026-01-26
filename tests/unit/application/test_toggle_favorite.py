"""
RED tests for ToggleFavorite use case.

ToggleFavorite marks/unmarks a card as favorite for an actor.
Security: actor can only favorite cards they can read.

MVP Contract:
1. Happy path: marks favorite when not already favorite
2. Toggle: unmarks if already favorite
3. Forbidden: cannot favorite PRIVATE card owned by someone else
4. Not found: card_id doesn't exist
5. actor_id invalid → ValidationError
6. card_id invalid → ValidationError
7. SHARED allows favorite if actor is in shared_with
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

    def add(self, card: Card) -> None:
        self.cards[card.card_id] = card


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
        return sorted(
            [card_id for (uid, card_id) in self._favorites if uid == actor_id]
        )



# =============================================================================
# FIXTURES - Repositories
# =============================================================================
@pytest.fixture
def favorites_repo() -> FakeFavoritesRepository:
    return FakeFavoritesRepository()


# =============================================================================
# 1) HAPPY PATH: MARKS FAVORITE WHEN NOT ALREADY FAVORITE
# =============================================================================
class TestToggleFavoriteHappyPath:
    """Marks favorite when not already favorite."""

    def test_marks_favorite_when_not_favorite(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        # Arrange: PUBLIC card readable by anyone
        card = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card_repo = FakeCardRepository({"c1": card})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        request = ToggleFavoriteRequest(actor_id="u2", card_id="c1")
        response = use_case.execute(request)

        # Assert: now favorite
        assert response.is_favorite is True
        assert favorites_repo.is_favorite("u2", "c1") is True


# =============================================================================
# 2) TOGGLE: UNMARKS IF ALREADY FAVORITE
# =============================================================================
class TestToggleFavoriteUnmark:
    """Unmarks favorite if already favorite."""

    def test_unmarks_when_already_favorite(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        # Arrange: card is already favorite
        card = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card_repo = FakeCardRepository({"c1": card})
        favorites_repo.set_favorite("u2", "c1", True)

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act
        request = ToggleFavoriteRequest(actor_id="u2", card_id="c1")
        response = use_case.execute(request)

        # Assert: now NOT favorite
        assert response.is_favorite is False
        assert favorites_repo.is_favorite("u2", "c1") is False


# =============================================================================
# 3) FORBIDDEN: CANNOT FAVORITE PRIVATE CARD OWNED BY SOMEONE ELSE
# =============================================================================
class TestToggleFavoriteForbidden:
    """Cannot favorite PRIVATE card owned by someone else."""

    def test_cannot_favorite_private_card_of_other_user(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        # Arrange: PRIVATE card owned by u1
        card = make_card("c1", "u1", Visibility.PRIVATE, table, map_spec)
        card_repo = FakeCardRepository({"c1": card})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act: u2 tries to favorite
        request = ToggleFavoriteRequest(actor_id="u2", card_id="c1")

        # Assert: forbidden
        with pytest.raises(Exception, match="(?i)forbidden|permission|access"):
            use_case.execute(request)

        # Assert: favorites NOT changed
        assert favorites_repo.is_favorite("u2", "c1") is False


# =============================================================================
# 4) NOT FOUND: CARD_ID DOESN'T EXIST
# =============================================================================
class TestToggleFavoriteNotFound:
    """Card not found raises error."""

    def test_card_not_found_raises_error(
        self,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        # Arrange: empty repo
        card_repo = FakeCardRepository({})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act & Assert
        request = ToggleFavoriteRequest(actor_id="u1", card_id="nonexistent")

        with pytest.raises(Exception, match="(?i)not.?found|does.?not.?exist"):
            use_case.execute(request)


# =============================================================================
# 5) INVALID ACTOR_ID
# =============================================================================
class TestToggleFavoriteInvalidActorId:
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
        favorites_repo: FakeFavoritesRepository,
        invalid_actor_id: Optional[str],
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        card = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card_repo = FakeCardRepository({"c1": card})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        request = ToggleFavoriteRequest(actor_id=invalid_actor_id, card_id="c1")

        with pytest.raises(ValidationError, match="(?i)actor"):
            use_case.execute(request)


# =============================================================================
# 6) INVALID CARD_ID
# =============================================================================
class TestToggleFavoriteInvalidCardId:
    """Invalid card_id raises ValidationError."""

    @pytest.mark.parametrize(
        "invalid_card_id",
        [None, "", "   "],
        ids=["none", "empty", "whitespace"],
    )
    def test_invalid_card_id_raises_error(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
        invalid_card_id: Optional[str],
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        card = make_card("c1", "u1", Visibility.PUBLIC, table, map_spec)
        card_repo = FakeCardRepository({"c1": card})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        request = ToggleFavoriteRequest(actor_id="u1", card_id=invalid_card_id)

        with pytest.raises(ValidationError, match="(?i)card"):
            use_case.execute(request)


# =============================================================================
# 7) SHARED ALLOWS FAVORITE IF ACTOR IS IN SHARED_WITH
# =============================================================================
class TestToggleFavoriteShared:
    """SHARED card allows favorite if actor is in shared_with."""

    def test_shared_card_allows_favorite_for_shared_user(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        # Arrange: SHARED card with u2 in shared_with
        card = make_card(
            "c1", "u1", Visibility.SHARED, table, map_spec, shared_with=["u2"]
        )
        card_repo = FakeCardRepository({"c1": card})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act: u2 favorites the shared card
        request = ToggleFavoriteRequest(actor_id="u2", card_id="c1")
        response = use_case.execute(request)

        # Assert: success
        assert response.is_favorite is True
        assert favorites_repo.is_favorite("u2", "c1") is True

    def test_shared_card_forbids_favorite_for_non_shared_user(
        self,
        table: TableSize,
        map_spec: MapSpec,
        favorites_repo: FakeFavoritesRepository,
    ):
        from application.use_cases.toggle_favorite import (
            ToggleFavorite,
            ToggleFavoriteRequest,
        )

        # Arrange: SHARED card with u2 in shared_with (NOT u3)
        card = make_card(
            "c1", "u1", Visibility.SHARED, table, map_spec, shared_with=["u2"]
        )
        card_repo = FakeCardRepository({"c1": card})

        use_case = ToggleFavorite(
            card_repository=card_repo,
            favorites_repository=favorites_repo,
        )

        # Act: u3 tries to favorite (not in shared_with)
        request = ToggleFavoriteRequest(actor_id="u3", card_id="c1")

        # Assert: forbidden
        with pytest.raises(Exception, match="(?i)forbidden|permission|access"):
            use_case.execute(request)


# =============================================================================
# TODO(future): Additional tests for hardening phase:
# - Test owner can always favorite their own card
# - Test concurrent toggle operations
# - Test favorites limit per user
# =============================================================================
