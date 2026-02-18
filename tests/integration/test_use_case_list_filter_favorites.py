"""Integration tests for ListCards, ListFavorites, and ToggleFavorite use cases.

These tests exercise the use cases through real service wiring (build_services)
with InMemoryCardRepository + InMemoryFavoritesRepository.
"""

from __future__ import annotations

import pytest
from application.use_cases.list_cards import (
    ListCards,
    ListCardsRequest,
    ListCardsResponse,
    _validate_filter,
)
from application.use_cases.list_favorites import (
    ListFavorites,
    ListFavoritesRequest,
    ListFavoritesResponse,
)
from application.use_cases.toggle_favorite import (
    ToggleFavorite,
    ToggleFavoriteRequest,
    ToggleFavoriteResponse,
)
from domain.cards.card import Card, GameMode
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility
from infrastructure.repositories.in_memory_card_repository import (
    InMemoryCardRepository,
)
from infrastructure.repositories.in_memory_favorites_repository import (
    InMemoryFavoritesRepository,
)


# =============================================================================
# HELPERS
# =============================================================================
def _make_card(
    card_id: str,
    owner_id: str = "actor-1",
    visibility: Visibility = Visibility.PRIVATE,
    shared_with: frozenset[str] | None = None,
    seed: int = 100,
) -> Card:
    table = TableSize.standard()
    shapes = [{"type": "rect", "x": 10, "y": 10, "width": 200, "height": 200}]
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=shared_with,
        mode=GameMode.MATCHED,
        seed=seed,
        table=table,
        map_spec=MapSpec(table=table, shapes=shapes),
    )


# =============================================================================
# _validate_filter
# =============================================================================
class TestValidateFilter:
    """Integration: _validate_filter with real inputs."""

    def test_valid_mine(self) -> None:
        assert _validate_filter("mine") == "mine"

    def test_valid_public(self) -> None:
        assert _validate_filter("public") == "public"

    def test_valid_shared_with_me(self) -> None:
        assert _validate_filter("shared_with_me") == "shared_with_me"

    def test_strips_whitespace(self) -> None:
        assert _validate_filter("  mine  ") == "mine"

    def test_none_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be None"):
            _validate_filter(None)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            _validate_filter("   ")

    def test_non_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be a string"):
            _validate_filter(42)

    def test_unknown_filter_raises(self) -> None:
        with pytest.raises(ValidationError, match="unknown filter"):
            _validate_filter("bogus")


# =============================================================================
# ListCards USE CASE
# =============================================================================
class TestListCardsUseCase:
    """Integration: ListCards with InMemoryCardRepository."""

    def test_mine_filter_returns_only_owned(self) -> None:
        repo = InMemoryCardRepository()
        my_card = _make_card("c1", owner_id="u1")
        other_card = _make_card("c2", owner_id="u2")
        repo.save(my_card)
        repo.save(other_card)

        uc = ListCards(repo)
        resp = uc.execute(ListCardsRequest(actor_id="u1", filter="mine"))

        assert isinstance(resp, ListCardsResponse)
        ids = [c.card_id for c in resp.cards]
        assert "c1" in ids
        assert "c2" not in ids

    def test_public_filter_returns_public_cards(self) -> None:
        repo = InMemoryCardRepository()
        pub = _make_card("c1", owner_id="u1", visibility=Visibility.PUBLIC)
        priv = _make_card("c2", owner_id="u2", visibility=Visibility.PRIVATE)
        repo.save(pub)
        repo.save(priv)

        uc = ListCards(repo)
        resp = uc.execute(ListCardsRequest(actor_id="u3", filter="public"))

        ids = [c.card_id for c in resp.cards]
        assert "c1" in ids
        assert "c2" not in ids

    def test_shared_with_me_filter(self) -> None:
        repo = InMemoryCardRepository()
        shared = _make_card(
            "c1",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u3"}),
        )
        not_shared = _make_card(
            "c2",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u4"}),
        )
        repo.save(shared)
        repo.save(not_shared)

        uc = ListCards(repo)
        resp = uc.execute(ListCardsRequest(actor_id="u3", filter="shared_with_me"))

        ids = [c.card_id for c in resp.cards]
        assert "c1" in ids
        assert "c2" not in ids

    def test_snapshot_has_expected_fields(self) -> None:
        repo = InMemoryCardRepository()
        card = _make_card("c1", owner_id="u1")
        repo.save(card)

        uc = ListCards(repo)
        resp = uc.execute(ListCardsRequest(actor_id="u1", filter="mine"))

        snap = resp.cards[0]
        assert snap.card_id == "c1"
        assert snap.owner_id == "u1"
        assert snap.visibility == "private"
        assert snap.mode == "matched"
        assert snap.seed == 100
        assert snap.table_mm is not None
        assert snap.table_mm["width_mm"] == 1200

    def test_invalid_actor_id_raises(self) -> None:
        repo = InMemoryCardRepository()
        uc = ListCards(repo)
        with pytest.raises(ValidationError):
            uc.execute(ListCardsRequest(actor_id="", filter="mine"))

    def test_invalid_filter_raises(self) -> None:
        repo = InMemoryCardRepository()
        uc = ListCards(repo)
        with pytest.raises(ValidationError):
            uc.execute(ListCardsRequest(actor_id="u1", filter="invalid"))


# =============================================================================
# ToggleFavorite USE CASE
# =============================================================================
class TestToggleFavoriteUseCase:
    """Integration: ToggleFavorite with repos."""

    def test_toggle_on_and_off(self) -> None:
        card_repo = InMemoryCardRepository()
        fav_repo = InMemoryFavoritesRepository()
        card = _make_card("c1", owner_id="u1")
        card_repo.save(card)

        uc = ToggleFavorite(card_repo, fav_repo)

        # First toggle: on
        resp = uc.execute(ToggleFavoriteRequest(actor_id="u1", card_id="c1"))
        assert isinstance(resp, ToggleFavoriteResponse)
        assert resp.is_favorite is True
        assert resp.card_id == "c1"

        # Second toggle: off
        resp = uc.execute(ToggleFavoriteRequest(actor_id="u1", card_id="c1"))
        assert resp.is_favorite is False

    def test_toggle_public_card_by_non_owner(self) -> None:
        card_repo = InMemoryCardRepository()
        fav_repo = InMemoryFavoritesRepository()
        card = _make_card("c1", owner_id="u1", visibility=Visibility.PUBLIC)
        card_repo.save(card)

        uc = ToggleFavorite(card_repo, fav_repo)
        resp = uc.execute(ToggleFavoriteRequest(actor_id="u2", card_id="c1"))
        assert resp.is_favorite is True


# =============================================================================
# ListFavorites USE CASE
# =============================================================================
class TestListFavoritesUseCase:
    """Integration: ListFavorites with repos."""

    def test_returns_favorite_card_ids(self) -> None:
        card_repo = InMemoryCardRepository()
        fav_repo = InMemoryFavoritesRepository()
        c1 = _make_card("c1", owner_id="u1")
        c2 = _make_card("c2", owner_id="u1", seed=200)
        card_repo.save(c1)
        card_repo.save(c2)
        fav_repo.set_favorite("u1", "c1", True)
        fav_repo.set_favorite("u1", "c2", True)

        uc = ListFavorites(card_repo, fav_repo)
        resp = uc.execute(ListFavoritesRequest(actor_id="u1"))

        assert isinstance(resp, ListFavoritesResponse)
        assert set(resp.card_ids) == {"c1", "c2"}

    def test_filters_deleted_cards(self) -> None:
        card_repo = InMemoryCardRepository()
        fav_repo = InMemoryFavoritesRepository()
        c1 = _make_card("c1", owner_id="u1")
        card_repo.save(c1)
        fav_repo.set_favorite("u1", "c1", True)
        fav_repo.set_favorite("u1", "c-deleted", True)  # card doesn't exist

        uc = ListFavorites(card_repo, fav_repo)
        resp = uc.execute(ListFavoritesRequest(actor_id="u1"))

        assert resp.card_ids == ["c1"]

    def test_filters_unreadable_cards(self) -> None:
        card_repo = InMemoryCardRepository()
        fav_repo = InMemoryFavoritesRepository()
        # Private card owned by u2 — u1 can't read it
        c_private = _make_card("c-priv", owner_id="u2", visibility=Visibility.PRIVATE)
        card_repo.save(c_private)
        fav_repo.set_favorite("u1", "c-priv", True)

        uc = ListFavorites(card_repo, fav_repo)
        resp = uc.execute(ListFavoritesRequest(actor_id="u1"))

        assert resp.card_ids == []

    def test_empty_favorites(self) -> None:
        card_repo = InMemoryCardRepository()
        fav_repo = InMemoryFavoritesRepository()

        uc = ListFavorites(card_repo, fav_repo)
        resp = uc.execute(ListFavoritesRequest(actor_id="u1"))
        assert resp.card_ids == []
