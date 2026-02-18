"""Integration tests for PostgresFavoritesRepository (real PostgreSQL).

Requires a running PostgreSQL instance — see .env / DATABASE_URL.
The ``repo_db_url`` / ``session_factory`` fixtures (in conftest.py)
create a disposable test database and run Alembic migrations.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.db

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_repo(session_factory):
    """Build a PostgresFavoritesRepository from the test session_factory."""
    from infrastructure.repositories.postgres_favorites_repository import (
        PostgresFavoritesRepository,
    )

    return PostgresFavoritesRepository(session_factory=session_factory)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestPostgresFavoritesRepository:
    """Integration test suite for PostgresFavoritesRepository."""

    def test_set_and_is_favorite(self, session_factory) -> None:
        """set_favorite(True) makes is_favorite return True."""
        repo = _make_repo(session_factory)

        assert repo.is_favorite("actor-1", "card-a") is False

        repo.set_favorite("actor-1", "card-a", True)
        assert repo.is_favorite("actor-1", "card-a") is True

    def test_unset_favorite(self, session_factory) -> None:
        """set_favorite(False) removes the favorite."""
        repo = _make_repo(session_factory)
        repo.set_favorite("actor-1", "card-a", True)

        repo.set_favorite("actor-1", "card-a", False)
        assert repo.is_favorite("actor-1", "card-a") is False

    def test_list_favorites_sorted(self, session_factory) -> None:
        """list_favorites returns card_ids sorted lexicographically."""
        repo = _make_repo(session_factory)
        repo.set_favorite("actor-1", "card-c", True)
        repo.set_favorite("actor-1", "card-a", True)
        repo.set_favorite("actor-1", "card-b", True)

        result = repo.list_favorites("actor-1")
        assert result == ["card-a", "card-b", "card-c"]

    def test_list_favorites_empty(self, session_factory) -> None:
        """list_favorites returns [] for an actor with no favorites."""
        repo = _make_repo(session_factory)
        assert repo.list_favorites("unknown-actor") == []

    def test_set_favorite_idempotent(self, session_factory) -> None:
        """Setting the same favorite twice does not raise or duplicate."""
        repo = _make_repo(session_factory)
        repo.set_favorite("actor-1", "card-a", True)
        repo.set_favorite("actor-1", "card-a", True)  # idempotent

        assert repo.is_favorite("actor-1", "card-a") is True
        assert repo.list_favorites("actor-1") == ["card-a"]

    def test_unset_favorite_idempotent(self, session_factory) -> None:
        """Unsetting a non-existent favorite does not raise."""
        repo = _make_repo(session_factory)
        repo.set_favorite("actor-1", "card-z", False)  # noop
        assert repo.is_favorite("actor-1", "card-z") is False

    def test_actor_isolation(self, session_factory) -> None:
        """Favorites are isolated per actor — one actor's favs don't leak."""
        repo = _make_repo(session_factory)
        repo.set_favorite("alice", "card-1", True)
        repo.set_favorite("bob", "card-2", True)

        assert repo.list_favorites("alice") == ["card-1"]
        assert repo.list_favorites("bob") == ["card-2"]
        assert repo.is_favorite("alice", "card-2") is False
        assert repo.is_favorite("bob", "card-1") is False
