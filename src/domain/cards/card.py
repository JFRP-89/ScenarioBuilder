"""Card domain model for scenario cards (MVP).

Card represents a generated scenario that combines table, map shapes,
game mode, and ownership/visibility rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Collection, Optional

from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility, can_read, can_write


class GameMode(Enum):
    """Game mode for scenario cards."""

    CASUAL = "casual"
    NARRATIVE = "narrative"
    MATCHED = "matched"


_VALID_GAME_MODES = frozenset(m.value for m in GameMode)


def parse_game_mode(value: object) -> GameMode:
    """Parse a game mode string into a GameMode enum.

    Args:
        value: String value to parse (case-insensitive, whitespace-trimmed).

    Returns:
        GameMode enum member.

    Raises:
        ValidationError: If value is None, not a string, empty, or unknown.
    """
    if value is None:
        raise ValidationError("mode cannot be None")
    if not isinstance(value, str):
        raise ValidationError("mode must be a string")

    normalized = value.strip().lower()

    if not normalized:
        raise ValidationError("mode cannot be empty or whitespace-only")

    if normalized not in _VALID_GAME_MODES:
        raise ValidationError(
            f"unknown mode '{normalized}', "
            f"must be one of: {', '.join(sorted(_VALID_GAME_MODES))}"
        )

    return GameMode(normalized)


def _validate_non_empty_str(name: str, value: Any) -> str:
    """Validate that value is a non-empty string after strip."""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValidationError(f"{name} cannot be empty or whitespace-only")
    return stripped


def _validate_seed(value: Any) -> int:
    """Validate seed is int >= 0, rejecting bool."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("seed must be int")
    if value < 0:
        raise ValidationError("seed must be >= 0")
    return value


@dataclass(frozen=True)
class Card:
    """Scenario card with ownership and visibility rules.

    Attributes:
        card_id: Unique identifier for the card.
        owner_id: User ID of the card owner.
        visibility: Visibility level (PRIVATE/SHARED/PUBLIC).
        shared_with: Collection of user IDs for SHARED visibility.
        mode: Game mode (CASUAL/NARRATIVE/MATCHED).
        seed: Deterministic seed for reproducibility.
        table: Table dimensions.
        map_spec: Map specification with shapes.
    """

    card_id: str
    owner_id: str
    visibility: Visibility
    shared_with: Optional[Collection[str]]
    mode: GameMode
    seed: int
    table: TableSize
    map_spec: MapSpec

    def __post_init__(self) -> None:
        """Validate all fields after initialization."""
        # Validate IDs
        _validate_non_empty_str("card_id", self.card_id)
        _validate_non_empty_str("owner_id", self.owner_id)

        # Validate seed
        _validate_seed(self.seed)

        # Validate types
        if not isinstance(self.table, TableSize):
            raise ValidationError("table must be TableSize")
        if not isinstance(self.map_spec, MapSpec):
            raise ValidationError("map_spec must be MapSpec")
        if not isinstance(self.visibility, Visibility):
            raise ValidationError("visibility must be Visibility")
        if not isinstance(self.mode, GameMode):
            raise ValidationError("mode must be GameMode")

        # Validate table coherence
        if (
            self.map_spec.table.width_mm != self.table.width_mm
            or self.map_spec.table.height_mm != self.table.height_mm
        ):
            raise ValidationError("map_spec.table dimensions must match table")

    def can_user_read(self, user_id: str) -> bool:
        """Check if user can read this card."""
        return can_read(
            owner_id=self.owner_id,
            visibility=self.visibility,
            current_user_id=user_id,
            shared_with=self.shared_with,
        )

    def can_user_write(self, user_id: str) -> bool:
        """Check if user can write this card."""
        return can_write(owner_id=self.owner_id, current_user_id=user_id)
