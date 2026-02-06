"""MapSpec validation helpers.

Kept in a separate module to keep the MapSpec model focused and reduce
complexity without changing behavior.
"""

from __future__ import annotations

from domain.errors import ValidationError
from domain.maps.map_spec_shape_validation import (
    _require_type_str,
    _validate_circle,
    _validate_polygon,
    _validate_rect,
    validate_objective_shapes,
)

__all__ = [
    "validate_objective_shapes",
    "_validate_shape",
    "_validate_shapes_count",
    "_validate_shapes_not_none",
]

_MAX_SHAPES = 100


def _validate_shapes_not_none(shapes: list[dict] | None) -> list[dict]:
    if shapes is None:
        raise ValidationError("shapes cannot be None")
    return shapes


def _validate_shapes_count(shapes: list[dict]) -> None:
    if len(shapes) > _MAX_SHAPES:
        raise ValidationError("too many shapes")


def _validate_shape(shape: dict, width_mm: int, height_mm: int) -> None:
    if not isinstance(shape, dict):
        raise ValidationError("shape must be dict")

    shape_type = _require_type_str(shape)

    if shape_type == "circle":
        _validate_circle(shape, width_mm, height_mm)
        return
    if shape_type == "rect":
        _validate_rect(shape, width_mm, height_mm)
        return
    if shape_type == "polygon":
        _validate_polygon(shape, width_mm, height_mm)
        return
