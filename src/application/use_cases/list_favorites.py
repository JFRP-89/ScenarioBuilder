"""ListFavorites use case.

Returns card_ids that actor has marked as favorite,
filtered to only include cards the actor can still read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from application.use_cases._validation import validate_actor_id


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class ListFavoritesRequest:
    """Request DTO for ListFavorites use case."""

    actor_id: Optional[str]


@dataclass
class ListFavoritesResponse:
    """Response DTO for ListFavorites use case."""

    card_ids: List[str]


# =============================================================================
# USE CASE
# =============================================================================
class ListFavorites:
    """Use case for listing favorite cards."""

    def __init__(
        self,
        card_repository: Any,
        favorites_repository: Any,
    ) -> None:
        self._card_repository = card_repository
        self._favorites_repository = favorites_repository

    def execute(self, request: ListFavoritesRequest) -> ListFavoritesResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor_id.

        Returns:
            Response DTO with list of favorite card_ids.

        Raises:
            ValidationError: If actor_id is invalid.
        """
        # 1) Validate inputs
        actor_id = validate_actor_id(request.actor_id)

        # 2) Get favorite card_ids from repository
        favorite_ids = self._favorites_repository.list_favorites(actor_id)

        # 3) Filter: only existing cards that actor can read
        visible_ids = []
        for card_id in favorite_ids:
            card = self._card_repository.get_by_id(card_id)
            # Skip if card doesn't exist
            if card is None:
                continue
            # Skip if actor can't read it (security filter)
            if not card.can_user_read(actor_id):
                continue
            visible_ids.append(card_id)

        # 4) Return response
        return ListFavoritesResponse(card_ids=visible_ids)
