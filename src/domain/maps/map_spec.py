"""MapSpec domain model for table shape validation (MVP)."""

from __future__ import annotations

from dataclasses import dataclass

from domain.maps.map_spec_validation import (
    _validate_shape,
    _validate_shapes_count,
    _validate_shapes_not_none,
    validate_deployment_shapes,
    validate_objective_shapes,
)
from domain.maps.table_size import TableSize


@dataclass(frozen=True)
class MapSpec:
    """Map specification with validated shapes for a table."""

    table: TableSize
    shapes: list[dict]
    objective_shapes: list[dict] | None = None
    deployment_shapes: list[dict] | None = None

    def __post_init__(self) -> None:
        shapes = _validate_shapes_not_none(self.shapes)
        _validate_shapes_count(shapes)

        width_mm = self.table.width_mm
        height_mm = self.table.height_mm

        for shape in shapes:
            _validate_shape(shape, width_mm, height_mm)

        # Validate objective_shapes (optional)
        validate_objective_shapes(self.objective_shapes, width_mm, height_mm)

        # Validate deployment_shapes (optional, max 4, border XOR corner)
        validate_deployment_shapes(self.deployment_shapes, width_mm, height_mm)
