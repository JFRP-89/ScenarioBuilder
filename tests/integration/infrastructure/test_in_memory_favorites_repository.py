"""RED tests for InMemoryFavoritesRepository.

Tests the in-memory implementation of FavoritesRepository for the modern API.
This repository stores favorite (actor_id, card_id) pairs.
"""

from __future__ import annotations

import pytest


# =============================================================================
# SET_FAVORITE + IS_FAVORITE TESTS
# =============================================================================
class TestInMemoryFavoritesRepositorySetAndIs:
    """Tests for set_favorite and is_favorite operations."""

    def test_set_favorite_true_adds_favorite(self) -> None:
        """set_favorite True adds the favorite."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()

        # Act
        repo.set_favorite("u1", "c1", True)

        # Assert
        assert repo.is_favorite("u1", "c1") is True

    def test_set_favorite_false_removes_favorite(self) -> None:
        """set_favorite False removes the favorite."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()
        repo.set_favorite("u1", "c1", True)
        assert repo.is_favorite("u1", "c1") is True  # precondition

        # Act
        repo.set_favorite("u1", "c1", False)

        # Assert
        assert repo.is_favorite("u1", "c1") is False

    def test_is_favorite_returns_false_when_not_set(self) -> None:
        """is_favorite returns False for non-existent favorite."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()

        # Act & Assert
        assert repo.is_favorite("u1", "c1") is False

    def test_set_favorite_true_twice_is_idempotent(self) -> None:
        """Setting favorite True twice does not duplicate."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()

        # Act
        repo.set_favorite("u1", "c1", True)
        repo.set_favorite("u1", "c1", True)

        # Assert
        assert repo.is_favorite("u1", "c1") is True
        assert repo.list_favorites("u1") == ["c1"]  # only one entry

    def test_set_favorite_false_on_nonexistent_is_noop(self) -> None:
        """Setting favorite False when not set is a no-op."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()

        # Act (should not raise)
        repo.set_favorite("u1", "c1", False)

        # Assert
        assert repo.is_favorite("u1", "c1") is False


# =============================================================================
# LIST_FAVORITES TESTS
# =============================================================================
class TestInMemoryFavoritesRepositoryListFavorites:
    """Tests for list_favorites operation."""

    def test_list_favorites_returns_sorted_card_ids(self) -> None:
        """list_favorites returns card_ids sorted lexicographically."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()
        # Add in mixed order
        repo.set_favorite("u1", "c2", True)
        repo.set_favorite("u1", "c1", True)
        repo.set_favorite("u1", "c10", True)

        # Act
        result = repo.list_favorites("u1")

        # Assert - sorted lexicographically
        assert result == ["c1", "c10", "c2"]

    def test_list_favorites_filters_by_actor(self) -> None:
        """list_favorites returns only favorites for the given actor."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()
        repo.set_favorite("u1", "c1", True)
        repo.set_favorite("u1", "c2", True)
        repo.set_favorite("u2", "c999", True)

        # Act & Assert
        assert repo.list_favorites("u1") == ["c1", "c2"]
        assert repo.list_favorites("u2") == ["c999"]

    def test_list_favorites_empty_repository(self) -> None:
        """list_favorites returns empty list when repository is empty."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()

        # Act & Assert
        assert repo.list_favorites("u1") == []

    def test_list_favorites_actor_with_no_favorites(self) -> None:
        """list_favorites returns empty list for actor with no favorites."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo = InMemoryFavoritesRepository()
        repo.set_favorite("u2", "c1", True)  # different actor

        # Act & Assert
        assert repo.list_favorites("u1") == []


# =============================================================================
# ISOLATION TESTS
# =============================================================================
class TestInMemoryFavoritesRepositoryIsolation:
    """Tests for repository isolation and independence."""

    def test_separate_instances_are_isolated(self) -> None:
        """Different repository instances do not share state."""
        from infrastructure.repositories.in_memory_favorites_repository import (
            InMemoryFavoritesRepository,
        )

        # Arrange
        repo1 = InMemoryFavoritesRepository()
        repo2 = InMemoryFavoritesRepository()

        # Act
        repo1.set_favorite("u1", "c1", True)

        # Assert
        assert repo1.is_favorite("u1", "c1") is True
        assert repo2.is_favorite("u1", "c1") is False
