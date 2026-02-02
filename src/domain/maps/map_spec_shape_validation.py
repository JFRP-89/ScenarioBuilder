"""Shape-specific validation helpers for MapSpec."""

from __future__ import annotations

from typing import Any, cast

from domain.errors import ValidationError

_MAX_POLYGON_POINTS = 200
_ALLOWED_TYPES = {"circle", "rect", "polygon"}


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
