"""ToggleFavorite use case.

Marks or unmarks a card as favorite for an actor.
Security: actor can only favorite cards they can read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from domain.errors import ValidationError


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
# VALIDATION HELPERS
# =============================================================================
def _validate_actor_id(actor_id: object) -> str:
    """Validate actor_id is non-empty string."""
    if actor_id is None:
        raise ValidationError("actor_id cannot be None")
    if not isinstance(actor_id, str):
        raise ValidationError("actor_id must be a string")
    stripped = actor_id.strip()
    if not stripped:
        raise ValidationError("actor_id cannot be empty or whitespace-only")
    return stripped


def _validate_card_id(card_id: object) -> str:
    """Validate card_id is non-empty string."""
    if card_id is None:
        raise ValidationError("card_id cannot be None")
    if not isinstance(card_id, str):
        raise ValidationError("card_id must be a string")
    stripped = card_id.strip()
    if not stripped:
        raise ValidationError("card_id cannot be empty or whitespace-only")
    return stripped


# =============================================================================
# USE CASE
# =============================================================================
class ToggleFavorite:
    """Use case for toggling a card as favorite."""

    def __init__(
        self,
        card_repository: Any,
        favorites_repository: Any,
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
        actor_id = _validate_actor_id(request.actor_id)
        card_id = _validate_card_id(request.card_id)

        # 2) Get card from repository
        card = self._card_repository.get_by_id(card_id)
        if card is None:
            raise Exception(f"Card not found: {card_id}")

        # 3) Check read access (anti-IDOR)
        if not card.can_user_read(actor_id):
            raise Exception("Forbidden: user does not have access to this card")

        # 4) Toggle favorite state
        current = self._favorites_repository.is_favorite(actor_id, card_id)
        new_value = not current
        self._favorites_repository.set_favorite(actor_id, card_id, new_value)

        # 5) Return response
        return ToggleFavoriteResponse(card_id=card_id, is_favorite=new_value)
