"""Defensive tests for DeleteCard use case (Broken Access Control — A01).

DeleteCard deletes a card by ID, enforcing ownership (anti-IDOR).
Only the card owner may delete their own card.

Coverage targets:
- Happy path: owner deletes own card
- Forbidden: non-owner cannot delete (PRIVATE, SHARED, PUBLIC)
- Not found: card does not exist
- Validation: invalid actor_id / card_id
- Repository interaction: delete is called only on success
"""

from __future__ import annotations

from typing import Optional

import pytest
from domain.cards.card import Card, GameMode, Visibility
from domain.errors import ForbiddenError, ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize


# =============================================================================
# TEST HELPERS
# =============================================================================
def make_valid_shapes() -> list[dict]:
    """Return shapes valid for TableSize.standard()."""
    return [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]


def make_valid_card(
    card_id: str = "card-001",
    owner_id: str = "u1",
    visibility: Visibility = Visibility.PRIVATE,
    shared_with: Optional[frozenset[str]] = None,
    mode: GameMode = GameMode.MATCHED,
    seed: int = 42,
) -> Card:
    """Create a valid Card for testing."""
    table = TableSize.standard()
    shapes = make_valid_shapes()
    map_spec = MapSpec(table=table, shapes=shapes)
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=visibility,
        shared_with=shared_with or frozenset(),
        mode=mode,
        seed=seed,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# FAKE REPOSITORY
# =============================================================================
class FakeCardRepository:
    """In-memory card repository for testing."""

    def __init__(self) -> None:
        self._cards: dict[str, Card] = {}
        self.delete_calls: list[str] = []

    def add(self, card: Card) -> None:
        """Pre-populate repository with a card."""
        self._cards[card.card_id] = card

    def get_by_id(self, card_id: str) -> Optional[Card]:
        """Get card by id."""
        return self._cards.get(card_id)

    def delete(self, card_id: str) -> bool:
        """Delete card from repository."""
        self.delete_calls.append(card_id)
        return self._cards.pop(card_id, None) is not None

    def save(self, card: Card) -> None:
        self._cards[card.card_id] = card

    def find_by_seed(self, seed: int) -> Optional[Card]:
        return next((c for c in self._cards.values() if c.seed == seed), None)

    def list_all(self) -> list[Card]:
        return list(self._cards.values())

    def list_for_owner(self, owner_id: str) -> list[Card]:
        return [c for c in self._cards.values() if c.owner_id == owner_id]


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def repo() -> FakeCardRepository:
    """Provide empty card repository."""
    return FakeCardRepository()


# =============================================================================
# HAPPY PATH TESTS
# =============================================================================
class TestDeleteCardHappyPath:
    """Tests for successful card deletion."""

    def test_owner_deletes_own_card(self, repo: FakeCardRepository) -> None:
        """Owner can delete their own card."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        # Arrange
        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        request = DeleteCardRequest(actor_id="u1", card_id="c1")
        use_case = DeleteCard(repository=repo)

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.card_id == "c1"
        assert response.deleted is True
        assert "c1" in repo.delete_calls

    def test_owner_deletes_public_card(self, repo: FakeCardRepository) -> None:
        """Owner can delete their own PUBLIC card."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(
            card_id="c1", owner_id="u1", visibility=Visibility.PUBLIC
        )
        repo.add(card)

        request = DeleteCardRequest(actor_id="u1", card_id="c1")
        use_case = DeleteCard(repository=repo)
        response = use_case.execute(request)

        assert response.deleted is True
        assert len(repo.delete_calls) == 1

    def test_owner_deletes_shared_card(self, repo: FakeCardRepository) -> None:
        """Owner can delete their own SHARED card."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u2"}),
        )
        repo.add(card)

        request = DeleteCardRequest(actor_id="u1", card_id="c1")
        use_case = DeleteCard(repository=repo)
        response = use_case.execute(request)

        assert response.deleted is True


# =============================================================================
# SECURITY / FORBIDDEN TESTS
# =============================================================================
class TestDeleteCardForbidden:
    """Tests for authorization failures — non-owner cannot delete."""

    def test_non_owner_cannot_delete_private_card(
        self, repo: FakeCardRepository
    ) -> None:
        """Non-owner is forbidden from deleting a PRIVATE card."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(
            card_id="c1", owner_id="u1", visibility=Visibility.PRIVATE
        )
        repo.add(card)

        request = DeleteCardRequest(actor_id="u2", card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        # Assert delete was NOT called
        assert len(repo.delete_calls) == 0

    def test_non_owner_cannot_delete_public_card(
        self, repo: FakeCardRepository
    ) -> None:
        """Non-owner is forbidden from deleting a PUBLIC card (read != write)."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(
            card_id="c1", owner_id="u1", visibility=Visibility.PUBLIC
        )
        repo.add(card)

        request = DeleteCardRequest(actor_id="u2", card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        assert len(repo.delete_calls) == 0

    def test_shared_user_cannot_delete_shared_card(
        self, repo: FakeCardRepository
    ) -> None:
        """User in shared_with list can read but NOT delete (read != write)."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u2"}),
        )
        repo.add(card)

        # u2 is in shared_with — can read, but must NOT delete
        request = DeleteCardRequest(actor_id="u2", card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        assert len(repo.delete_calls) == 0

    def test_random_user_cannot_delete_shared_card(
        self, repo: FakeCardRepository
    ) -> None:
        """User NOT in shared_with list cannot delete SHARED card."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(
            card_id="c1",
            owner_id="u1",
            visibility=Visibility.SHARED,
            shared_with=frozenset({"u3"}),
        )
        repo.add(card)

        request = DeleteCardRequest(actor_id="u2", card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner|write"):
            use_case.execute(request)

        assert len(repo.delete_calls) == 0


# =============================================================================
# FAKE FAVORITES REPOSITORY
# =============================================================================
class FakeFavoritesRepository:
    """In-memory fake favorites repository for testing."""

    def __init__(self) -> None:
        self._favorites: set[tuple[str, str]] = set()
        self.remove_all_calls: list[str] = []

    def is_favorite(self, actor_id: str, card_id: str) -> bool:
        return (actor_id, card_id) in self._favorites

    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None:
        key = (actor_id, card_id)
        if value:
            self._favorites.add(key)
        else:
            self._favorites.discard(key)

    def list_favorites(self, actor_id: str) -> list[str]:
        return [c for a, c in self._favorites if a == actor_id]

    def remove_all_for_card(self, card_id: str) -> None:
        self.remove_all_calls.append(card_id)
        self._favorites = {(a, c) for a, c in self._favorites if c != card_id}


# =============================================================================
# FAVORITES CLEANUP ON DELETE TESTS
# =============================================================================
class TestDeleteCardCleansFavorites:
    """DeleteCard cleans up all favorites referencing the deleted card."""

    def test_delete_removes_favorites_for_card(self, repo: FakeCardRepository) -> None:
        """Deleting a card removes all favorites referencing it."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        fav_repo = FakeFavoritesRepository()
        fav_repo.set_favorite("u2", "c1", True)
        fav_repo.set_favorite("u3", "c1", True)

        use_case = DeleteCard(repository=repo, favorites_repository=fav_repo)
        use_case.execute(DeleteCardRequest(actor_id="u1", card_id="c1"))

        # Assert: remove_all_for_card was called
        assert fav_repo.remove_all_calls == ["c1"]
        # Assert: favorites are gone
        assert not fav_repo.is_favorite("u2", "c1")
        assert not fav_repo.is_favorite("u3", "c1")

    def test_delete_without_favorites_repo_still_works(
        self, repo: FakeCardRepository
    ) -> None:
        """DeleteCard works without favorites_repository (backward compat)."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        use_case = DeleteCard(repository=repo)
        response = use_case.execute(DeleteCardRequest(actor_id="u1", card_id="c1"))

        assert response.deleted is True

    def test_delete_preserves_other_cards_favorites(
        self, repo: FakeCardRepository
    ) -> None:
        """Deleting c1 does not remove favorites for c2."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card1 = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card1)

        fav_repo = FakeFavoritesRepository()
        fav_repo.set_favorite("u2", "c1", True)
        fav_repo.set_favorite("u2", "c2", True)

        use_case = DeleteCard(repository=repo, favorites_repository=fav_repo)
        use_case.execute(DeleteCardRequest(actor_id="u1", card_id="c1"))

        # c2 favorite untouched
        assert fav_repo.is_favorite("u2", "c2")
        assert not fav_repo.is_favorite("u2", "c1")

    def test_forbidden_delete_does_not_clean_favorites(
        self, repo: FakeCardRepository
    ) -> None:
        """If delete is forbidden, favorites must NOT be cleaned."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        fav_repo = FakeFavoritesRepository()
        fav_repo.set_favorite("u2", "c1", True)

        use_case = DeleteCard(repository=repo, favorites_repository=fav_repo)

        with pytest.raises(ForbiddenError):
            use_case.execute(DeleteCardRequest(actor_id="u2", card_id="c1"))

        # Favorites still intact
        assert fav_repo.is_favorite("u2", "c1")
        assert fav_repo.remove_all_calls == []


class TestDeleteCardNotFound:
    """Tests for card not found."""

    def test_delete_nonexistent_card_raises_error(
        self, repo: FakeCardRepository
    ) -> None:
        """Deleting a card that does not exist raises an error."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        # Arrange: repo is empty
        request = DeleteCardRequest(actor_id="u1", card_id="nonexistent")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match=r"(?i)not found|does not exist"):
            use_case.execute(request)

        assert len(repo.delete_calls) == 0

    def test_error_message_contains_card_id(self, repo: FakeCardRepository) -> None:
        """Error message includes the missing card_id for debugging."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        request = DeleteCardRequest(actor_id="u1", card_id="missing-card-xyz")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match="missing-card-xyz"):
            use_case.execute(request)


# =============================================================================
# VALIDATION ERROR TESTS
# =============================================================================
class TestDeleteCardInvalidActorId:
    """Tests for invalid actor_id validation."""

    @pytest.mark.parametrize("invalid_actor_id", [None, "", "   "])
    def test_invalid_actor_id_raises_validation_error(
        self,
        invalid_actor_id,
        repo: FakeCardRepository,
    ) -> None:
        """Invalid actor_id raises ValidationError before any repo access."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        request = DeleteCardRequest(actor_id=invalid_actor_id, card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(ValidationError, match=r"(?i)actor"):
            use_case.execute(request)

        # Assert delete was NOT called (validation failed before repo)
        assert len(repo.delete_calls) == 0


class TestDeleteCardInvalidCardId:
    """Tests for invalid card_id validation."""

    @pytest.mark.parametrize("invalid_card_id", [None, "", "   "])
    def test_invalid_card_id_raises_validation_error(
        self,
        invalid_card_id,
        repo: FakeCardRepository,
    ) -> None:
        """Invalid card_id raises ValidationError before any repo access."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        request = DeleteCardRequest(actor_id="u1", card_id=invalid_card_id)
        use_case = DeleteCard(repository=repo)

        with pytest.raises(ValidationError, match=r"(?i)card"):
            use_case.execute(request)

        assert len(repo.delete_calls) == 0


# =============================================================================
# ANTI-IDOR HARDENING TESTS
# =============================================================================
class TestDeleteCardAntiIdor:
    """Ensure consistent behavior that prevents IDOR attacks."""

    def test_forbidden_before_delete_not_leak_existence(
        self, repo: FakeCardRepository
    ) -> None:
        """Non-owner gets 'forbidden' (not 'not found') — no info leak."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        request = DeleteCardRequest(actor_id="attacker", card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(Exception, match=r"(?i)forbidden|permission|owner"):
            use_case.execute(request)

        # Card still exists — not deleted
        assert repo.get_by_id("c1") is not None

    def test_delete_is_called_only_once_per_request(
        self, repo: FakeCardRepository
    ) -> None:
        """Repository.delete is called exactly once on success."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        card = make_valid_card(card_id="c1", owner_id="u1")
        repo.add(card)

        request = DeleteCardRequest(actor_id="u1", card_id="c1")
        use_case = DeleteCard(repository=repo)
        use_case.execute(request)

        assert repo.delete_calls == ["c1"]

    def test_order_of_operations_validate_then_authz_then_delete(
        self, repo: FakeCardRepository
    ) -> None:
        """Validation must happen before authz, authz before delete."""
        from application.use_cases.delete_card import DeleteCard, DeleteCardRequest

        # Empty actor_id should fail at validation, not at authz or delete
        request = DeleteCardRequest(actor_id="", card_id="c1")
        use_case = DeleteCard(repository=repo)

        with pytest.raises(ValidationError):
            use_case.execute(request)

        assert len(repo.delete_calls) == 0
