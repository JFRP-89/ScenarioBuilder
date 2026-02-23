"""Collision detection for map shapes.

Supports RectxRect, CirclexCircle, RectxCircle, and polygon
overlap tests (via AABB bounding box) with a configurable
clearance margin (MIN_CLEARANCE_MM).
"""

from __future__ import annotations

# Minimum gap between any two shapes (mm)
MIN_CLEARANCE_MM: int = 10


# ---------------------------------------------------------------------------
# Bounding-box helpers
# ---------------------------------------------------------------------------


def _rect_bounds(shape: dict) -> tuple[int, int, int, int]:
    """Return (x_min, y_min, x_max, y_max) for a rect shape."""
    x = shape["x"]
    y = shape["y"]
    return (x, y, x + shape["width"], y + shape["height"])


def _circle_bounds(shape: dict) -> tuple[int, int, int, int]:
    """Return axis-aligned bounding box for a circle shape."""
    cx, cy, r = shape["cx"], shape["cy"], shape["r"]
    return (cx - r, cy - r, cx + r, cy + r)


def _polygon_bounds(shape: dict) -> tuple[int, int, int, int]:
    """Return axis-aligned bounding box for a polygon shape."""
    points = shape["points"]
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _shape_bounds(shape: dict) -> tuple[int, int, int, int] | None:
    """Return AABB for any supported shape type, or None."""
    t = shape.get("type", "")
    if t == "rect":
        return _rect_bounds(shape)
    if t == "circle":
        return _circle_bounds(shape)
    if t == "polygon":
        return _polygon_bounds(shape)
    return None


def _aabb_overlap(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
    clearance: int,
) -> bool:
    """Check if two AABBs overlap (including clearance margin)."""
    return not (
        a[2] + clearance <= b[0]
        or b[2] + clearance <= a[0]
        or a[3] + clearance <= b[1]
        or b[3] + clearance <= a[1]
    )


# ---------------------------------------------------------------------------
# Pairwise overlap tests
# ---------------------------------------------------------------------------


def _rects_overlap(a: dict, b: dict, clearance: int) -> bool:
    """Check if two rects overlap (including clearance margin)."""
    ax0, ay0, ax1, ay1 = _rect_bounds(a)
    bx0, by0, bx1, by1 = _rect_bounds(b)
    return not (
        ax1 + clearance <= bx0
        or bx1 + clearance <= ax0
        or ay1 + clearance <= by0
        or by1 + clearance <= ay0
    )


def _circles_overlap(a: dict, b: dict, clearance: int) -> bool:
    """Check if two circles overlap (including clearance margin)."""
    dx = a["cx"] - b["cx"]
    dy = a["cy"] - b["cy"]
    dist_sq = dx * dx + dy * dy
    min_dist = a["r"] + b["r"] + clearance
    return bool(dist_sq < min_dist * min_dist)


def _rect_circle_overlap(rect: dict, circle: dict, clearance: int) -> bool:
    """Check if a rect and a circle overlap (including clearance margin).

    Uses closest-point-on-rect to circle-center distance test.
    """
    rx0, ry0, rx1, ry1 = _rect_bounds(rect)
    cx, cy, r = circle["cx"], circle["cy"], circle["r"]

    # Find closest point on rect to circle center
    closest_x = max(rx0, min(cx, rx1))
    closest_y = max(ry0, min(cy, ry1))

    dx = cx - closest_x
    dy = cy - closest_y
    dist_sq = dx * dx + dy * dy
    threshold = r + clearance
    return bool(dist_sq < threshold * threshold)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _allows_overlap(shape: dict) -> bool:
    """Return True if a shape opts out of collision checks."""
    return bool(shape.get("allow_overlap", False))


def shapes_overlap(a: dict, b: dict, clearance: int = MIN_CLEARANCE_MM) -> bool:
    """Check if two shapes overlap with a given clearance.

    Supports: rect, circle, polygon (polygon uses AABB bounding box).
    If either shape sets allow_overlap=True, collisions are ignored.

    Args:
        a: First shape dict (must have 'type').
        b: Second shape dict (must have 'type').
        clearance: Minimum gap in mm between shape edges.

    Returns:
        True if shapes overlap or are closer than clearance.
    """
    if _allows_overlap(a) or _allows_overlap(b):
        return False
    ta = a.get("type", "")
    tb = b.get("type", "")

    if ta == "rect" and tb == "rect":
        return _rects_overlap(a, b, clearance)

    if ta == "circle" and tb == "circle":
        return _circles_overlap(a, b, clearance)

    if ta == "rect" and tb == "circle":
        return _rect_circle_overlap(a, b, clearance)

    if ta == "circle" and tb == "rect":
        return _rect_circle_overlap(b, a, clearance)

    # Polygon involved — use AABB (bounding-box) overlap
    bounds_a = _shape_bounds(a)
    bounds_b = _shape_bounds(b)
    if bounds_a is not None and bounds_b is not None:
        return _aabb_overlap(bounds_a, bounds_b, clearance)

    # Unknown type — conservatively assume no overlap
    return False


def find_first_collision(
    shapes: list[dict], clearance: int = MIN_CLEARANCE_MM
) -> tuple[int, int] | None:
    """Find first pair of overlapping shapes.

    Args:
        shapes: List of shape dicts.
        clearance: Minimum gap in mm.

    Returns:
        Tuple (i, j) of first colliding pair indices, or None if no collision.
    """
    n = len(shapes)
    for i in range(n):
        for j in range(i + 1, n):
            if shapes_overlap(shapes[i], shapes[j], clearance):
                return (i, j)
    return None


def shape_in_bounds(shape: dict, width_mm: int, height_mm: int) -> bool:
    """Check if a shape fits entirely within the table bounds.

    Args:
        shape: Shape dict with 'type' and position/dimension fields.
        width_mm: Table width in mm.
        height_mm: Table height in mm.

    Returns:
        True if shape is fully within [0, width_mm] x [0, height_mm].
    """
    t = shape.get("type", "")

    if t == "rect":
        x0, y0, x1, y1 = _rect_bounds(shape)
        return x0 >= 0 and y0 >= 0 and x1 <= width_mm and y1 <= height_mm

    if t == "circle":
        x0, y0, x1, y1 = _circle_bounds(shape)
        return x0 >= 0 and y0 >= 0 and x1 <= width_mm and y1 <= height_mm

    if t == "polygon":
        points = shape.get("points", [])
        return all(
            0 <= p.get("x", -1) <= width_mm and 0 <= p.get("y", -1) <= height_mm
            for p in points
        )

    return False


def has_no_collisions(shapes: list[dict], clearance: int = MIN_CLEARANCE_MM) -> bool:
    """Return True if no pair of shapes overlaps.

    Convenience wrapper around find_first_collision.
    """
    return find_first_collision(shapes, clearance) is None
