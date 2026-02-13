"""Repository ports (DIP contracts for persistence).

These protocols define the interfaces that use cases depend on.
Infrastructure provides concrete implementations.
"""

from __future__ import annotations

from typing import Optional, Protocol

from domain.cards.card import Card


class CardRepository(Protocol):
    """Port for card persistence.

    All use-case interactions with card storage go through this protocol.
    """

    def save(self, card: Card) -> None: ...

    def get_by_id(self, card_id: str) -> Optional[Card]: ...

    def delete(self, card_id: str) -> bool: ...

    def list_all(self) -> list[Card]: ...


class FavoritesRepository(Protocol):
    """Port for favorites persistence."""

    def is_favorite(self, actor_id: str, card_id: str) -> bool: ...

    def set_favorite(self, actor_id: str, card_id: str, value: bool) -> None: ...

    def list_favorites(self, actor_id: str) -> list[str]: ...
