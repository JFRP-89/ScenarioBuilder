"""ListCards use case.

Lists cards visible to an actor based on filter criteria.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

# Legacy import for backward compatibility
from application.ports.repositories import CardRepository
from application.use_cases._validation import validate_actor_id
from domain.errors import ValidationError
from domain.security.authz import Visibility


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
        actor_id = validate_actor_id(request.actor_id)
        filter_value = _validate_filter(request.filter)

        # 2) Get all cards from repository
        all_cards = self._repository.list_all()

        # 3) Apply filter
        filtered = self._apply_filter(all_cards, filter_value, actor_id)

        # 4) Apply security filter (anti-IDOR): only cards user can read
        visible = [c for c in filtered if c.can_user_read(actor_id)]

        # 5) Build response snapshots
        items = [self._to_snapshot(c) for c in visible]

        return ListCardsResponse(cards=items)

    def _apply_filter(
        self, cards: List[Any], filter_value: str, actor_id: str
    ) -> List[Any]:
        """Apply filter to cards based on filter type."""
        if filter_value == "mine":
            return [c for c in cards if c.owner_id == actor_id]

        if filter_value == "public":
            return [c for c in cards if c.visibility == Visibility.PUBLIC]

        if filter_value == "shared_with_me":
            return [
                c
                for c in cards
                if c.visibility == Visibility.SHARED
                and c.shared_with is not None
                and actor_id in c.shared_with
            ]

        return []

    def _to_snapshot(self, card: Any) -> "_CardSnapshot":
        """Convert card to snapshot DTO."""
        # Extract table_mm from card.table (TableSize object)
        table_mm = None
        table_preset = None
        if hasattr(card, "table") and card.table:
            table_mm = {
                "width_mm": card.table.width_mm,
                "height_mm": card.table.height_mm,
            }
            # Detect preset based on dimensions
            table_preset = self._detect_table_preset(card.table)

        return _CardSnapshot(
            card_id=card.card_id,
            owner_id=card.owner_id,
            visibility=card.visibility.value,
            mode=card.mode.value,
            seed=card.seed,
            name=card.name or "",  # Now from Card domain model
            table_preset=table_preset,
            table_mm=table_mm,
        )

    def _detect_table_preset(self, table: Any) -> str:
        """Detect table preset based on dimensions.

        Args:
            table: TableSize instance

        Returns:
            "standard", "massive", or "custom"
        """
        # Standard is 1200x1200 mm
        if table.width_mm == 1200 and table.height_mm == 1200:
            return "standard"
        # Massive is 1800x1200 mm
        if table.width_mm == 1800 and table.height_mm == 1200:
            return "massive"
        # Everything else is custom
        return "custom"


@dataclass(frozen=True)
class _CardSnapshot:
    """Snapshot of a card for list response."""

    card_id: str
    owner_id: str
    visibility: str
    mode: str
    seed: int
    name: str
    table_preset: Optional[str]
    table_mm: Optional[dict[str, int]]
