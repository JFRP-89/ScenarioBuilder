"""InMemoryFavoritesRepository - Modern in-memory favorites storage.

A simple in-memory implementation of the FavoritesRepository port.
Each instance maintains its own isolated storage (no shared state).
"""

from __future__ import annotations


class InMemoryFavoritesRepository:
    """In-memory favorites repository for testing and development.

    Stores favorite (actor_id, card_id) pairs.
    list_favorites returns sorted card_ids for deterministic output.
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._favorites: set[tuple[str, str]] = set()

    def _get_actor_favorites(self, actor_id: str) -> list[str]:
        """Extract all favorite card_ids for an actor, sorted.

        Args:
            actor_id: The actor id.

        Returns:
            List of card_ids sorted lexicographically.
        """
        return sorted(
            [card_id for stored_actor_id, card_id in self._favorites if stored_actor_id == actor_id]
        )

    def is_favorite(self, actor_id: str, card_id: str) -> bool:
        """Check if a card is favorited by an actor.

        Args:
            actor_id: The actor id.
            card_id: The card id.

        Returns:
            True if the card is a favorite, False otherwise.
        """
        key = (actor_id, card_id)
        return key in self._favorites

    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None:
        """Set or unset a card as favorite for an actor.

        Args:
            actor_id: The actor id.
            card_id: The card id.
            value: True to add favorite, False to remove.
        """
        key = (actor_id, card_id)

        if not value:
            self._favorites.discard(key)
            return

        self._favorites.add(key)

    def list_favorites(self, actor_id: str) -> list[str]:
        """List all favorite card_ids for an actor.

        Args:
            actor_id: The actor id.

        Returns:
            List of card_ids sorted lexicographically.
        """
        return self._get_actor_favorites(actor_id)
