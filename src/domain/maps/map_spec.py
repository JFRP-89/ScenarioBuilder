"""MapSpec domain model for table shape validation (MVP)."""

from __future__ import annotations

from dataclasses import dataclass

from domain.maps.map_spec_validation import (
    _validate_shape,
    _validate_shapes_count,
    _validate_shapes_not_none,
)
from domain.maps.table_size import TableSize


@dataclass(frozen=True)
class MapSpec:
    """Map specification with validated shapes for a table."""

    table: TableSize
    shapes: list[dict]

    def __post_init__(self) -> None:
        shapes = _validate_shapes_not_none(self.shapes)
        _validate_shapes_count(shapes)

        width_mm = self.table.width_mm
        height_mm = self.table.height_mm

        for shape in shapes:
            _validate_shape(shape, width_mm, height_mm)
