"""ListFavorites use case.

Returns card_ids that actor has marked as favorite,
filtered to only include cards the actor can still read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from application.ports.repositories import CardRepository, FavoritesRepository
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
        card_repository: CardRepository,
        favorites_repository: FavoritesRepository,
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
        #    Prune stale entries (deleted / no longer accessible) to keep DB clean.
        visible_ids = []
        for card_id in favorite_ids:
            card = self._card_repository.get_by_id(card_id)
            # Card deleted → remove stale favorite
            if card is None:
                self._favorites_repository.set_favorite(actor_id, card_id, False)
                continue
            # Card no longer readable → remove stale favorite
            if not card.can_user_read(actor_id):
                self._favorites_repository.set_favorite(actor_id, card_id, False)
                continue
            visible_ids.append(card_id)

        # 4) Return response
        return ListFavoritesResponse(card_ids=visible_ids)
