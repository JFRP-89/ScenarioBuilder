"""RED tests for InMemoryCardRepository.

Tests the in-memory implementation of CardRepository for the modern API.
This repository stores cards by card_id with last-write-wins semantics.
"""

from __future__ import annotations

import pytest

from domain.cards.card import Card, GameMode
from domain.security.authz import Visibility
from domain.maps.table_size import TableSize
from domain.maps.map_spec import MapSpec


# =============================================================================
# TEST HELPERS
# =============================================================================
def make_card(
    card_id: str,
    owner_id: str = "u1",
    seed: int = 123,
) -> Card:
    """Create a valid Card for testing."""
    table = TableSize.standard()
    shapes = [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]
    map_spec = MapSpec(table=table, shapes=shapes)
    return Card(
        card_id=card_id,
        owner_id=owner_id,
        visibility=Visibility.PRIVATE,
        shared_with=frozenset(),
        mode=GameMode.MATCHED,
        seed=seed,
        table=table,
        map_spec=map_spec,
    )


# =============================================================================
# SAVE + GET TESTS
# =============================================================================
class TestInMemoryCardRepositorySaveAndGet:
    """Tests for save and get_by_id operations."""

    def test_save_and_get_by_id_happy_path(self) -> None:
        """Save a card and retrieve it by id."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo = InMemoryCardRepository()
        card = make_card(card_id="c1", owner_id="u1")

        # Act
        repo.save(card)
        result = repo.get_by_id("c1")

        # Assert
        assert result is not None
        assert result.card_id == "c1"
        assert result.owner_id == "u1"

    def test_get_by_id_returns_none_if_not_exists(self) -> None:
        """get_by_id returns None when card does not exist."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo = InMemoryCardRepository()

        # Act
        result = repo.get_by_id("missing")

        # Assert
        assert result is None

    def test_save_overwrites_by_card_id(self) -> None:
        """Saving with same card_id overwrites (last write wins)."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo = InMemoryCardRepository()
        card_v1 = make_card(card_id="c1", owner_id="u1")
        card_v2 = make_card(card_id="c1", owner_id="u2")

        # Act
        repo.save(card_v1)
        repo.save(card_v2)
        result = repo.get_by_id("c1")

        # Assert
        assert result is not None
        assert result.owner_id == "u2"

        # Also verify only one card exists
        all_cards = repo.list_all()
        assert len(all_cards) == 1


# =============================================================================
# LIST_ALL TESTS
# =============================================================================
class TestInMemoryCardRepositoryListAll:
    """Tests for list_all operation."""

    def test_list_all_returns_all_saved_cards(self) -> None:
        """list_all returns all cards that have been saved."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo = InMemoryCardRepository()
        card1 = make_card(card_id="c1", owner_id="u1")
        card2 = make_card(card_id="c2", owner_id="u2")

        # Act
        repo.save(card1)
        repo.save(card2)
        all_cards = repo.list_all()

        # Assert
        assert len(all_cards) == 2
        ids = {c.card_id for c in all_cards}
        assert ids == {"c1", "c2"}

    def test_list_all_empty_repository(self) -> None:
        """list_all returns empty list when repository is empty."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo = InMemoryCardRepository()

        # Act
        all_cards = repo.list_all()

        # Assert
        assert all_cards == []

    def test_list_all_deterministic_insertion_order(self) -> None:
        """list_all returns cards in insertion order (optional but useful)."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo = InMemoryCardRepository()
        card1 = make_card(card_id="c1")
        card2 = make_card(card_id="c2")
        card3 = make_card(card_id="c3")

        # Act
        repo.save(card1)
        repo.save(card2)
        repo.save(card3)
        all_cards = repo.list_all()

        # Assert
        ids = [c.card_id for c in all_cards]
        assert ids == ["c1", "c2", "c3"]


# =============================================================================
# ISOLATION TESTS
# =============================================================================
class TestInMemoryCardRepositoryIsolation:
    """Tests for repository isolation and independence."""

    def test_separate_instances_are_isolated(self) -> None:
        """Different repository instances do not share state."""
        from infrastructure.repositories.in_memory_card_repository import (
            InMemoryCardRepository,
        )

        # Arrange
        repo1 = InMemoryCardRepository()
        repo2 = InMemoryCardRepository()
        card = make_card(card_id="c1")

        # Act
        repo1.save(card)

        # Assert
        assert repo1.get_by_id("c1") is not None
        assert repo2.get_by_id("c1") is None
