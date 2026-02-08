"""Shape-specific validation helpers for MapSpec."""

from __future__ import annotations

from typing import Any, cast

from domain.errors import ValidationError

_MAX_POLYGON_POINTS = 200
_MAX_OBJECTIVE_POINTS = 10
_MAX_DEPLOYMENT_SHAPES = 4
_OBJECTIVE_POINT_RADIUS = 25
_ALLOWED_TYPES = {"circle", "rect", "polygon"}
_OBJECTIVE_POINT_TYPE = "objective_point"
_ALLOWED_BORDERS = frozenset({"north", "south", "east", "west"})
_ALLOWED_CORNERS = frozenset({"north-east", "north-west", "south-east", "south-west"})


def _require_int(field_name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field_name} must be int")
    return cast(int, value)


def _require_type_str(shape: dict) -> str:
    shape_type = shape.get("type")
    if not isinstance(shape_type, str):
        raise ValidationError("shape type must be string")
    if shape_type not in _ALLOWED_TYPES:
        raise ValidationError(f"unknown shape type: {shape_type}")
    return shape_type


def _validate_circle(shape: dict, width_mm: int, height_mm: int) -> None:
    if "cx" not in shape or "cy" not in shape or "r" not in shape:
        raise ValidationError("circle requires cx, cy, r")

    cx = _require_int("cx", shape["cx"])
    cy = _require_int("cy", shape["cy"])
    r = _require_int("r", shape["r"])

    if r <= 0:
        raise ValidationError("circle radius must be positive")

    if cx - r < 0 or cy - r < 0:
        raise ValidationError("circle out of bounds")
    if cx + r > width_mm or cy + r > height_mm:
        raise ValidationError("circle out of bounds")


def _validate_rect(shape: dict, width_mm: int, height_mm: int) -> None:
    if (
        "x" not in shape
        or "y" not in shape
        or "width" not in shape
        or "height" not in shape
    ):
        raise ValidationError("rect requires x, y, width, height")

    x = _require_int("x", shape["x"])
    y = _require_int("y", shape["y"])
    width = _require_int("width", shape["width"])
    height = _require_int("height", shape["height"])

    if width <= 0 or height <= 0:
        raise ValidationError("rect width/height must be positive")

    if x < 0 or y < 0:
        raise ValidationError("rect out of bounds")
    if x + width > width_mm or y + height > height_mm:
        raise ValidationError("rect out of bounds")


def _require_points_list(shape: dict) -> list:
    points = shape.get("points")
    if points is None:
        raise ValidationError("polygon requires points")
    if not isinstance(points, list):
        raise ValidationError("polygon points must be list")
    return points


def _validate_polygon_point(point: dict, width_mm: int, height_mm: int) -> None:
    if not isinstance(point, dict):
        raise ValidationError("polygon point must be dict")
    if "x" not in point or "y" not in point:
        raise ValidationError("polygon point requires x and y")
    x = _require_int("x", point["x"])
    y = _require_int("y", point["y"])
    if x < 0 or y < 0 or x > width_mm or y > height_mm:
        raise ValidationError("polygon point out of bounds")


def _validate_polygon(shape: dict, width_mm: int, height_mm: int) -> None:
    points = _require_points_list(shape)

    if len(points) < 3:
        raise ValidationError("polygon requires at least 3 points")
    if len(points) > _MAX_POLYGON_POINTS:
        raise ValidationError("polygon has too many points")

    for point in points:
        _validate_polygon_point(point, width_mm, height_mm)


def _validate_objective_point(shape: dict, width_mm: int, height_mm: int) -> None:
    """Validate an objective_point shape.

    Objective points are special circular markers with fixed radius of 25mm.
    They require only cx and cy coordinates.
    """
    if "cx" not in shape or "cy" not in shape:
        raise ValidationError("objective_point requires cx, cy")

    cx = _require_int("cx", shape["cx"])
    cy = _require_int("cy", shape["cy"])

    # Check bounds: objective_point has fixed radius of 25mm, so they can
    # extend slightly beyond bounds but center must be within table
    if cx < 0 or cy < 0 or cx > width_mm or cy > height_mm:
        raise ValidationError("objective_point center out of bounds")


def validate_objective_shapes(
    shapes: list[dict] | None, width_mm: int, height_mm: int
) -> None:
    """Validate objective_shapes array.

    Args:
        shapes: List of objective_point dictionaries or None.
        width_mm: Table width in mm.
        height_mm: Table height in mm.

    Raises:
        ValidationError: If validation fails.
    """
    if shapes is None:
        return  # objective_shapes are optional

    if not isinstance(shapes, list):
        raise ValidationError("objective_shapes must be list")

    if len(shapes) > _MAX_OBJECTIVE_POINTS:
        raise ValidationError(
            f"too many objective points (max {_MAX_OBJECTIVE_POINTS})"
        )

    for shape in shapes:
        if not isinstance(shape, dict):
            raise ValidationError("objective_shape must be dict")
        _validate_objective_point(shape, width_mm, height_mm)


def _validate_border_deployment(shape: dict, width_mm: int, height_mm: int) -> None:
    """Validate a border-based deployment shape (type='rect')."""
    border = shape["border"]
    if not isinstance(border, str):
        raise ValidationError("border must be a string")
    if border not in _ALLOWED_BORDERS:
        raise ValidationError(
            f"unknown border '{border}', must be one of: "
            f"{', '.join(sorted(_ALLOWED_BORDERS))}"
        )
    shape_type = shape.get("type")
    if shape_type != "rect":
        raise ValidationError("border deployment_shape must be type 'rect'")
    _validate_rect(shape, width_mm, height_mm)


def _validate_corner_deployment(shape: dict, width_mm: int, height_mm: int) -> None:
    """Validate a corner-based deployment shape (type='polygon')."""
    corner = shape["corner"]
    if not isinstance(corner, str):
        raise ValidationError("corner must be a string")
    if corner not in _ALLOWED_CORNERS:
        raise ValidationError(
            f"unknown corner '{corner}', must be one of: "
            f"{', '.join(sorted(_ALLOWED_CORNERS))}"
        )
    shape_type = shape.get("type")
    if shape_type != "polygon":
        raise ValidationError("corner deployment_shape must be type 'polygon'")
    _validate_polygon(shape, width_mm, height_mm)


def _validate_deployment_shape(shape: dict, width_mm: int, height_mm: int) -> None:
    """Validate a single deployment shape.

    A deployment shape must have either 'border' or 'corner' (not both).
    - border-based: type='rect' with border in {north, south, east, west}
    - corner-based: type='polygon' with corner in {north-east, ..., south-west}
    """
    if not isinstance(shape, dict):
        raise ValidationError("deployment_shape must be dict")

    has_border = "border" in shape
    has_corner = "corner" in shape

    if has_border and has_corner:
        raise ValidationError(
            "deployment_shape must have either 'border' or 'corner', not both"
        )
    if not has_border and not has_corner:
        raise ValidationError("deployment_shape must have either 'border' or 'corner'")

    if has_border:
        _validate_border_deployment(shape, width_mm, height_mm)
    else:
        _validate_corner_deployment(shape, width_mm, height_mm)


def validate_deployment_shapes(
    shapes: list[dict] | None, width_mm: int, height_mm: int
) -> None:
    """Validate deployment_shapes array.

    Args:
        shapes: List of deployment shape dicts or None.
        width_mm: Table width in mm.
        height_mm: Table height in mm.

    Raises:
        ValidationError: If validation fails.
    """
    if shapes is None:
        return

    if not isinstance(shapes, list):
        raise ValidationError("deployment_shapes must be list")

    if len(shapes) > _MAX_DEPLOYMENT_SHAPES:
        raise ValidationError(
            f"too many deployment shapes (max {_MAX_DEPLOYMENT_SHAPES})"
        )

    for shape in shapes:
        _validate_deployment_shape(shape, width_mm, height_mm)
