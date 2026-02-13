"""Geometry helpers: bounds, overlap, shape validation."""

from __future__ import annotations

import math
from typing import Any


# =============================================================================
# Bounding box helpers
# =============================================================================
def get_circle_bounds(circle: dict[str, Any]) -> tuple[float, float, float, float]:
    """Get bounding box for circle (x_min, y_min, x_max, y_max)."""
    cx = float(circle.get("cx", 0))
    cy = float(circle.get("cy", 0))
    r = float(circle.get("r", 0))
    return (cx - r, cy - r, cx + r, cy + r)


def get_rect_bounds(rect: dict[str, Any]) -> tuple[float, float, float, float]:
    """Get bounding box for rect (x_min, y_min, x_max, y_max)."""
    x = float(rect.get("x", 0))
    y = float(rect.get("y", 0))
    width = float(rect.get("width", 0))
    height = float(rect.get("height", 0))
    return (x, y, x + width, y + height)


def get_polygon_bounds(polygon: dict[str, Any]) -> tuple[float, float, float, float]:
    """Get bounding box for polygon (x_min, y_min, x_max, y_max).

    Handles both point formats:
    - Dict format: [{"x": ..., "y": ...}, ...]
    - List format: [[x, y], [x, y], ...]
    """
    points = polygon.get("points", [])
    if not points:
        return (0, 0, 0, 0)

    xs: list[float] = []
    ys: list[float] = []
    for p in points:
        if isinstance(p, dict):
            xs.append(float(p.get("x", 0)))
            ys.append(float(p.get("y", 0)))
        elif isinstance(p, (list, tuple)) and len(p) >= 2:
            xs.append(float(p[0]))
            ys.append(float(p[1]))

    if not xs or not ys:
        return (0, 0, 0, 0)

    return (min(xs), min(ys), max(xs), max(ys))


# =============================================================================
# Overlap detection
# =============================================================================
def circles_overlap(c1: dict[str, Any], c2: dict[str, Any]) -> bool:
    """Check if two circles overlap."""
    cx1 = float(c1.get("cx", 0))
    cy1 = float(c1.get("cy", 0))
    r1 = float(c1.get("r", 0))

    cx2 = float(c2.get("cx", 0))
    cy2 = float(c2.get("cy", 0))
    r2 = float(c2.get("r", 0))

    distance = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
    return distance < (r1 + r2)


def rects_overlap(r1: dict[str, Any], r2: dict[str, Any]) -> bool:
    """Check if two rectangles overlap (AABB)."""
    x1_min, y1_min, x1_max, y1_max = get_rect_bounds(r1)
    x2_min, y2_min, x2_max, y2_max = get_rect_bounds(r2)

    return not (
        x1_max <= x2_min or x2_max <= x1_min or y1_max <= y2_min or y2_max <= y1_min
    )


def bounding_boxes_overlap(
    b1: tuple[float, float, float, float], b2: tuple[float, float, float, float]
) -> bool:
    """Check if two bounding boxes overlap."""
    x1_min, y1_min, x1_max, y1_max = b1
    x2_min, y2_min, x2_max, y2_max = b2

    return not (
        x1_max <= x2_min or x2_max <= x1_min or y1_max <= y2_min or y2_max <= y1_min
    )


def shapes_overlap(shape1: dict[str, Any], shape2: dict[str, Any]) -> bool:
    """Check if two shapes overlap (approximate using bounding boxes)."""
    type1 = shape1.get("type", "")
    type2 = shape2.get("type", "")

    # Circle-circle: exact test
    if type1 == "circle" and type2 == "circle":
        return circles_overlap(shape1, shape2)

    # Rect-rect: exact test
    if type1 == "rect" and type2 == "rect":
        return rects_overlap(shape1, shape2)

    # All other combinations: use bounding box approximation
    bounds1 = (
        get_circle_bounds(shape1)
        if type1 == "circle"
        else (
            get_rect_bounds(shape1) if type1 == "rect" else get_polygon_bounds(shape1)
        )
    )

    bounds2 = (
        get_circle_bounds(shape2)
        if type2 == "circle"
        else (
            get_rect_bounds(shape2) if type2 == "rect" else get_polygon_bounds(shape2)
        )
    )

    return bounding_boxes_overlap(bounds1, bounds2)


# =============================================================================
# Shape validation
# =============================================================================
def validate_circle_within_bounds(
    cx: float, cy: float, r: float, table_w: int, table_h: int
) -> str | None:
    """Validate circle is within table bounds."""
    if cx - r < 0 or cx + r > table_w:
        return "Circle extends beyond table width"
    if cy - r < 0 or cy + r > table_h:
        return "Circle extends beyond table height"
    return None


def validate_rect_within_bounds(
    x: float, y: float, width: float, height: float, table_w: int, table_h: int
) -> str | None:
    """Validate rectangle is within table bounds."""
    if x < 0 or x + width > table_w:
        return "Rectangle extends beyond table width"
    if y < 0 or y + height > table_h:
        return "Rectangle extends beyond table height"
    return None


def validate_polygon_within_bounds(
    points: list[Any], table_w: int, table_h: int
) -> str | None:
    """Validate polygon points are within table bounds."""
    for i, point in enumerate(points, 1):
        px = float(point[0] if isinstance(point, (list, tuple)) else point.get("x", 0))
        py = float(point[1] if isinstance(point, (list, tuple)) else point.get("y", 0))
        if px < 0 or px > table_w:
            return f"Polygon point {i} extends beyond table width"
        if py < 0 or py > table_h:
            return f"Polygon point {i} extends beyond table height"
    return None


def delete_polygon_row(
    polygon_dataframe_rows: list[list[float]],
) -> tuple[list[list[float]], str | None]:
    """Delete last row from polygon points, respecting minimum 3 points."""
    if len(polygon_dataframe_rows) <= 3:
        return (
            polygon_dataframe_rows,
            "Cannot delete - polygons require minimum 3 points",
        )
    return polygon_dataframe_rows[:-1], None


def validate_shape_within_table(
    shape: dict[str, Any], table_width_mm: int, table_height_mm: int
) -> str | None:
    """Validate shape fits within table bounds (in mm)."""
    shape_type = shape.get("type", "")

    if shape_type == "circle":
        cx = float(shape.get("cx", 0))
        cy = float(shape.get("cy", 0))
        r = float(shape.get("r", 0))
        return validate_circle_within_bounds(cx, cy, r, table_width_mm, table_height_mm)

    if shape_type == "rect":
        x = float(shape.get("x", 0))
        y = float(shape.get("y", 0))
        width = float(shape.get("width", 0))
        height = float(shape.get("height", 0))
        return validate_rect_within_bounds(
            x, y, width, height, table_width_mm, table_height_mm
        )

    if shape_type == "polygon":
        points = shape.get("points", [])
        return validate_polygon_within_bounds(points, table_width_mm, table_height_mm)

    return None
