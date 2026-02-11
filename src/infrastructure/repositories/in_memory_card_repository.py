"""InMemoryCardRepository - Modern in-memory card storage.

A simple in-memory implementation of the CardRepository port.
Each instance maintains its own isolated storage (no shared state).
Last-write-wins semantics for duplicate card_ids.
"""

from __future__ import annotations

from typing import Optional

from domain.cards.card import Card


class InMemoryCardRepository:
    """In-memory card repository for testing and development.

    Stores cards by card_id with last-write-wins semantics.
    Maintains insertion order for list_all().
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._cards: dict[str, Card] = {}

    def save(self, card: Card) -> None:
        """Save a card to the repository.

        If card_id already exists, overwrites (last write wins).

        Args:
            card: The card to save.
        """
        self._cards[card.card_id] = card

    def get_by_id(self, card_id: str) -> Optional[Card]:
        """Retrieve a card by its id.

        Args:
            card_id: The card id to look up.

        Returns:
            The card if found, None otherwise.
        """
        return self._cards.get(card_id)

    def delete(self, card_id: str) -> bool:
        """Delete a card by its id.

        Args:
            card_id: The card id to delete.

        Returns:
            True if the card was deleted, False if not found.
        """
        if card_id in self._cards:
            del self._cards[card_id]
            return True
        return False

    def list_all(self) -> list[Card]:
        """List all cards in the repository.

        Returns:
            List of all cards in insertion order.
        """
        return list(self._cards.values())
