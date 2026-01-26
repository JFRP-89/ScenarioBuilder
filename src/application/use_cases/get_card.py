"""GetCard use case.

Retrieves a Card by ID, enforcing visibility/authz rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from domain.errors import ValidationError


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class GetCardRequest:
    """Request DTO for GetCard use case."""

    actor_id: Optional[str]
    card_id: Optional[str]


@dataclass
class GetCardResponse:
    """Response DTO for GetCard use case."""

    card_id: str
    owner_id: str
    seed: int
    mode: str
    visibility: str


# =============================================================================
# USE CASE
# =============================================================================
class GetCard:
    """Use case for retrieving a card by ID."""

    def __init__(self, repository: Any) -> None:
        self._repository = repository

    def execute(self, request: GetCardRequest) -> GetCardResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor and card IDs.

        Returns:
            Response DTO with card data.

        Raises:
            ValidationError: If actor_id or card_id is invalid.
            Exception: If card not found or access forbidden.
        """
        # 1) Validate actor_id
        actor_id = self._validate_actor_id(request.actor_id)

        # 2) Validate card_id
        card_id = self._validate_card_id(request.card_id)

        # 3) Fetch card from repository
        card = self._repository.get_by_id(card_id)
        if card is None:
            raise Exception(f"Card not found: {card_id}")

        # 4) Enforce read access
        if not card.can_user_read(actor_id):
            raise Exception("Forbidden: user does not have read access")

        # 5) Build response
        return GetCardResponse(
            card_id=card.card_id,
            owner_id=card.owner_id,
            seed=card.seed,
            mode=card.mode.value,
            visibility=card.visibility.value,
        )

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

    def _validate_card_id(self, card_id: Optional[str]) -> str:
        """Validate card_id is non-empty string."""
        if card_id is None:
            raise ValidationError("card_id cannot be None")
        if not isinstance(card_id, str):
            raise ValidationError("card_id must be a string")
        stripped = card_id.strip()
        if not stripped:
            raise ValidationError("card_id cannot be empty or whitespace-only")
        return stripped
