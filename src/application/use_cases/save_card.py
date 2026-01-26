"""SaveCard use case.

Persists a Card entity to the repository.
Only the card owner can save their own card.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from domain.cards.card import Card
from domain.errors import ValidationError


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class SaveCardRequest:
    """Request DTO for SaveCard use case."""

    actor_id: Optional[str]
    card: Card


@dataclass
class SaveCardResponse:
    """Response DTO for SaveCard use case."""

    card_id: str


# =============================================================================
# USE CASE
# =============================================================================
class SaveCard:
    """Use case for saving a card to the repository."""

    def __init__(self, repository: Any) -> None:
        self._repository = repository

    def execute(self, request: SaveCardRequest) -> SaveCardResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor and card.

        Returns:
            Response DTO with saved card_id.

        Raises:
            ValidationError: If actor_id is invalid.
            Exception: If actor is not the owner (forbidden).
        """
        # 1) Validate actor_id
        actor_id = self._validate_actor_id(request.actor_id)

        # 2) Enforce write access: actor must be owner
        if request.card.owner_id != actor_id:
            raise Exception("Forbidden: only the owner can save this card")

        # 3) Save to repository
        self._repository.save(request.card)

        # 4) Return response
        return SaveCardResponse(card_id=request.card.card_id)

    def _validate_actor_id(self, actor_id: Optional[str]) -> str:
        """Validate actor_id is non-empty string."""
        if actor_id is None:
            raise ValidationError("actor_id cannot be None")
        if not isinstance(actor_id, str):
            raise ValidationError("actor_id must be a string")
        stripped = actor_id.strip()
        if not stripped:
            raise ValidationError("actor_id cannot be empty or whitespace-only")
        return stripped
