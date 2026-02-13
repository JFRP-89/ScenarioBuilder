"""DeleteCard use case.

Deletes a card by ID, enforcing ownership (anti-IDOR).
Only the card owner may delete their own card.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from application.ports.repositories import CardRepository
from application.use_cases._validation import (
    load_card_for_write,
    validate_actor_id,
    validate_card_id,
)


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class DeleteCardRequest:
    """Request DTO for DeleteCard use case."""

    actor_id: Optional[str]
    card_id: Optional[str]


@dataclass
class DeleteCardResponse:
    """Response DTO for DeleteCard use case."""

    card_id: str
    deleted: bool


# =============================================================================
# USE CASE
# =============================================================================
class DeleteCard:
    """Use case for deleting a card by ID.

    Enforces ownership: only the card owner may delete.
    """

    def __init__(self, repository: CardRepository) -> None:
        self._repository = repository

    def execute(self, request: DeleteCardRequest) -> DeleteCardResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor and card IDs.

        Returns:
            Response DTO confirming deletion.

        Raises:
            ValidationError: If actor_id or card_id is invalid.
            Exception: If card not found or actor is not the owner.
        """
        # 1) Validate inputs
        actor_id = validate_actor_id(request.actor_id)
        card_id = validate_card_id(request.card_id)

        # 2) Fetch card + enforce ownership (anti-IDOR)
        load_card_for_write(self._repository, card_id, actor_id)

        # 3) Delete
        self._repository.delete(card_id)

        return DeleteCardResponse(card_id=card_id, deleted=True)
