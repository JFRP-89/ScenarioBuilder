"""Table resolution logic for scenario card generation."""

from __future__ import annotations

from typing import Optional

from domain.errors import ValidationError
from domain.maps.table_size import TableSize

_TABLE_PRESETS = frozenset(["standard", "massive", "custom"])


def _resolve_table(
    preset: str,
    width_mm: Optional[int] = None,
    height_mm: Optional[int] = None,
) -> TableSize:
    """Resolve table preset to TableSize.

    Args:
        preset: Table preset ("standard", "massive", or "custom")
        width_mm: Width in mm (required if preset is "custom")
        height_mm: Height in mm (required if preset is "custom")

    Returns:
        TableSize instance

    Raises:
        ValidationError: If preset is unknown or custom dimensions are invalid
    """
    if preset == "standard":
        return TableSize.standard()
    elif preset == "massive":
        return TableSize.massive()
    elif preset == "custom":
        if width_mm is None or height_mm is None:
            raise ValidationError(
                "Custom table preset requires table_width_mm and table_height_mm"
            )
        # TableSize constructor validates dimensions
        return TableSize(width_mm=width_mm, height_mm=height_mm)
    else:
        raise ValidationError(
            f"unknown table preset '{preset}', "
            f"must be one of: {', '.join(sorted(_TABLE_PRESETS))}"
        )
