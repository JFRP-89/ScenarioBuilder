"""ToggleFavorite use case.

Marks or unmarks a card as favorite for an actor.
Security: actor can only favorite cards they can read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from application.ports.repositories import CardRepository, FavoritesRepository
from application.use_cases._validation import (
    load_card_for_read,
    validate_actor_id,
    validate_card_id,
)


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class ToggleFavoriteRequest:
    """Request DTO for ToggleFavorite use case."""

    actor_id: Optional[str]
    card_id: Optional[str]


@dataclass
class ToggleFavoriteResponse:
    """Response DTO for ToggleFavorite use case."""

    card_id: str
    is_favorite: bool


# =============================================================================
# USE CASE
# =============================================================================
class ToggleFavorite:
    """Use case for toggling a card as favorite."""

    def __init__(
        self,
        card_repository: CardRepository,
        favorites_repository: FavoritesRepository,
    ) -> None:
        self._card_repository = card_repository
        self._favorites_repository = favorites_repository

    def execute(self, request: ToggleFavoriteRequest) -> ToggleFavoriteResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor_id and card_id.

        Returns:
            Response DTO with new favorite state.

        Raises:
            ValidationError: If actor_id or card_id is invalid.
            Exception: If card not found or access forbidden.
        """
        # 1) Validate inputs
        actor_id = validate_actor_id(request.actor_id)
        card_id = validate_card_id(request.card_id)

        # 2) Fetch card + enforce read access (anti-IDOR)
        load_card_for_read(self._card_repository, card_id, actor_id)

        # 3) Toggle favorite state
        current = self._favorites_repository.is_favorite(actor_id, card_id)
        new_value = not current
        self._favorites_repository.set_favorite(actor_id, card_id, new_value)

        # 5) Return response
        return ToggleFavoriteResponse(card_id=card_id, is_favorite=new_value)
