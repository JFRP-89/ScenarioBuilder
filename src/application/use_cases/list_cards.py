"""ListCards use case.

Lists cards visible to an actor based on filter criteria.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from domain.errors import ValidationError
from domain.security.authz import Visibility

# Legacy import for backward compatibility
from application.ports.repositories import CardRepository


# =============================================================================
# LEGACY API (kept for backward compatibility)
# =============================================================================
def execute(repo: CardRepository, owner_id: str):
    """Legacy functional API - kept for backward compatibility."""
    return list(repo.list_for_owner(owner_id))


# =============================================================================
# VALID FILTERS
# =============================================================================
_VALID_FILTERS = frozenset(["mine", "public", "shared_with_me"])


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


def _validate_filter(value: object) -> str:
    """Validate filter is a known value (case-sensitive, no normalization)."""
    if value is None:
        raise ValidationError("filter cannot be None")
    if not isinstance(value, str):
        raise ValidationError("filter must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValidationError("filter cannot be empty or whitespace-only")
    if stripped not in _VALID_FILTERS:
        raise ValidationError(
            f"unknown filter '{stripped}', "
            f"must be one of: {', '.join(sorted(_VALID_FILTERS))}"
        )
    return stripped


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass(frozen=True)
class ListCardsRequest:
    """Request DTO for ListCards use case."""

    actor_id: Optional[str]
    filter: Optional[str]


@dataclass(frozen=True)
class ListCardsResponse:
    """Response DTO for ListCards use case."""

    cards: List[Any]  # List of card snapshots


# =============================================================================
# USE CASE
# =============================================================================
class ListCards:
    """Use case for listing cards visible to an actor."""

    def __init__(self, repository: Any) -> None:
        self._repository = repository

    def execute(self, request: ListCardsRequest) -> ListCardsResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor_id and filter.

        Returns:
            Response DTO with list of visible cards.

        Raises:
            ValidationError: If actor_id or filter is invalid.
        """
        # 1) Validate inputs
        actor_id = _validate_actor_id(request.actor_id)
        filter_value = _validate_filter(request.filter)

        # 2) Get all cards from repository
        all_cards = self._repository.list_all()

        # 3) Apply filter
        if filter_value == "mine":
            filtered = [c for c in all_cards if c.owner_id == actor_id]
        elif filter_value == "public":
            filtered = [c for c in all_cards if c.visibility == Visibility.PUBLIC]
        elif filter_value == "shared_with_me":
            filtered = [
                c for c in all_cards
                if c.visibility == Visibility.SHARED
                and c.shared_with is not None
                and actor_id in c.shared_with
            ]
        else:
            filtered = []

        # 4) Apply security filter (anti-IDOR): only cards user can read
        visible = [c for c in filtered if c.can_user_read(actor_id)]

        # 5) Build response snapshots
        items = [
            _CardSnapshot(
                card_id=c.card_id,
                owner_id=c.owner_id,
                visibility=c.visibility.value,
            )
            for c in visible
        ]

        return ListCardsResponse(cards=items)


@dataclass(frozen=True)
class _CardSnapshot:
    """Snapshot of a card for list response."""

    card_id: str
    owner_id: str
    visibility: str
