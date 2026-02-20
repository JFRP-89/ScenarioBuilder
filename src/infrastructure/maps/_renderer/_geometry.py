"""Geometry helpers for SVG label positioning (stateless, no I/O)."""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Centroid calculation
# ---------------------------------------------------------------------------


def calculate_rect_center(shape: dict) -> tuple[int, int]:
    """Calculate center coordinates of a rectangle."""
    x = int(shape["x"])
    y = int(shape["y"])
    w = int(shape["width"])
    h = int(shape["height"])
    return x + w // 2, y + h // 2


def calculate_circle_center(shape: dict) -> tuple[int, int]:
    """Calculate center coordinates of a circle."""
    return int(shape["cx"]), int(shape["cy"])


def calculate_polygon_center(shape: dict) -> tuple[int, int]:
    """Calculate approximate center of a polygon (centroid).

    For quarter-circles (identified by 'corner' field), calculates the true
    centroid using the formula: distance from corner = 4R/(3π).
    For other polygons, uses the average of all vertices.
    """
    points = shape.get("points", [])
    if not points:
        return 0, 0

    # Check if this is a quarter-circle (has corner attribute)
    corner = shape.get("corner")
    if corner and len(points) > 3:  # Quarter-circles have many points
        x_coords = [int(p.get("x", 0)) for p in points]
        y_coords = [int(p.get("y", 0)) for p in points]

        corner_x = x_coords[0]
        corner_y = y_coords[0]

        arc_points_x = x_coords[1:]
        arc_points_y = y_coords[1:]

        max_dist_x = max(abs(x - corner_x) for x in arc_points_x)
        max_dist_y = max(abs(y - corner_y) for y in arc_points_y)
        radius = max(max_dist_x, max_dist_y)

        centroid_distance = (4 * radius) / (3 * math.pi)

        if corner == "north-west":
            cx = int(corner_x + centroid_distance)
            cy = int(corner_y + centroid_distance)
        elif corner == "north-east":
            cx = int(corner_x - centroid_distance)
            cy = int(corner_y + centroid_distance)
        elif corner == "south-west":
            cx = int(corner_x + centroid_distance)
            cy = int(corner_y - centroid_distance)
        elif corner == "south-east":
            cx = int(corner_x - centroid_distance)
            cy = int(corner_y - centroid_distance)
        else:
            cx = sum(x_coords) // len(x_coords)
            cy = sum(y_coords) // len(y_coords)

        return cx, cy

    # For regular polygons (triangles, etc.), use average of vertices
    x_coords = [int(p.get("x", 0)) for p in points]
    y_coords = [int(p.get("y", 0)) for p in points]
    return sum(x_coords) // len(x_coords), sum(y_coords) // len(y_coords)


# ---------------------------------------------------------------------------
# Text measurement
# ---------------------------------------------------------------------------


def estimate_text_width(text: str, font_size_px: int = 14) -> int:
    """Estimate text width in mm for a given font size.

    For Arial Bold, each character is ~0.7 * font_size wide.
    """
    char_width_mm = font_size_px * 0.7
    total_width_mm = int(len(text) * char_width_mm)
    return max(total_width_mm, 10)  # Minimum 10mm


def text_fits_in_bounds(
    text: str,
    center_x: int,
    center_y: int,
    table_width_mm: int,
    table_height_mm: int,
    offset: int = 0,
    direction: str = "up",
) -> bool:
    """Check if text fits within table bounds at a given position."""
    text_width = estimate_text_width(text)
    text_height = 20  # Approximate text height at 14px

    if direction == "up":
        text_y = center_y - offset
        return text_y - text_height // 2 >= 0
    elif direction == "down":
        text_y = center_y + offset
        return text_y + text_height // 2 <= table_height_mm
    elif direction == "left":
        text_x = center_x - offset
        return text_x - text_width // 2 >= 0
    elif direction == "right":
        text_x = center_x + offset
        return text_x + text_width // 2 <= table_width_mm

    return True


# ---------------------------------------------------------------------------
# Label positioning — helpers
# ---------------------------------------------------------------------------

_OFFSET_DISTANCE = 50
_EXTRA_HORIZONTAL_OFFSET = 50
_NEAR_THRESHOLD = _OFFSET_DISTANCE + 30

_PRIORITY_ORDER: dict[str, tuple[str, ...]] = {
    "top-left": ("down", "right", "up", "left"),
    "top-right": ("down", "left", "up", "right"),
    "bottom-left": ("up", "right", "down", "left"),
    "bottom-right": ("up", "left", "down", "right"),
    "left": ("right", "up", "down", "left"),
    "right": ("left", "up", "down", "right"),
    "top": ("down", "right", "left", "up"),
    "bottom": ("up", "right", "left", "down"),
    "center": ("up", "down", "right", "left"),
}


def _classify_edge_proximity(
    near_top: bool,
    near_bottom: bool,
    near_left: bool,
    near_right: bool,
) -> str:
    """Return a key describing which edges are nearby."""
    if near_top and near_left:
        return "top-left"
    if near_top and near_right:
        return "top-right"
    if near_bottom and near_left:
        return "bottom-left"
    if near_bottom and near_right:
        return "bottom-right"
    if near_left:
        return "left"
    if near_right:
        return "right"
    if near_top:
        return "top"
    if near_bottom:
        return "bottom"
    return "center"


def _clamp(value: int, lo: int, hi: int) -> int:
    """Clamp *value* between *lo* and *hi*."""
    return max(lo, min(value, hi))


def _select_best_candidate(
    candidates: list[tuple[int, int, int, str]],
    min_edge_dist: int,
) -> tuple[int, int, str]:
    """Pick the best label candidate, preferring default order far from edges."""
    candidates.sort(key=lambda c: c[0], reverse=True)
    if min_edge_dist >= 200:
        for preferred in ("up", "down", "right", "left"):
            for _space, x, y, direction in candidates:
                if direction == preferred:
                    return x, y, direction
    _, best_x, best_y, best_dir = candidates[0]
    return best_x, best_y, best_dir


# ---------------------------------------------------------------------------
# Label positioning — public API
# ---------------------------------------------------------------------------


def get_position_preference_order(
    cx: int,
    cy: int,
    table_width_mm: int,
    table_height_mm: int,
) -> list[tuple[int, int, str]]:
    """Determine position preference order based on proximity to edges.

    For edge cases, intelligently selects positions away from edges.
    For corners, combines both axis logic to find best readable position.
    Adds extra offset for horizontal positions to account for objective radius.
    """
    space_up = cy
    space_down = table_height_mm - cy
    space_left = cx
    space_right = table_width_mm - cx

    near_top = space_up < _NEAR_THRESHOLD
    near_bottom = space_down < _NEAR_THRESHOLD
    near_left = space_left < _NEAR_THRESHOLD
    near_right = space_right < _NEAR_THRESHOLD

    all_positions: dict[str, tuple[int, int, str]] = {
        "up": (cx, cy - _OFFSET_DISTANCE, "up"),
        "down": (cx, cy + _OFFSET_DISTANCE, "down"),
        "right": (cx + _OFFSET_DISTANCE + _EXTRA_HORIZONTAL_OFFSET, cy, "right"),
        "left": (cx - _OFFSET_DISTANCE - _EXTRA_HORIZONTAL_OFFSET, cy, "left"),
    }

    key = _classify_edge_proximity(near_top, near_bottom, near_left, near_right)
    return [all_positions[d] for d in _PRIORITY_ORDER[key]]


def find_best_objective_position(
    cx: int,
    cy: int,
    text: str,
    table_width_mm: int,
    table_height_mm: int,
) -> tuple[int, int, str]:
    """Find the best position to place objective label text.

    Places text adjacent to objective circle (radius 25mm) ensuring
    it stays completely within table bounds.
    """
    text_width = estimate_text_width(text)
    text_height = 20
    objective_radius = 25
    margin = 25
    offset = objective_radius + margin
    half_w = text_width // 2
    half_h = text_height // 2

    space_up = cy
    space_down = table_height_mm - cy
    space_left = cx
    space_right = table_width_mm - cx

    candidates: list[tuple[int, int, int, str]] = []

    # UP
    up_x = _clamp(cx, half_w, table_width_mm - half_w)
    up_y = cy - offset
    if up_y - half_h >= 0:
        candidates.append((space_up, up_x, up_y, "up"))

    # DOWN
    dn_x = _clamp(cx, half_w, table_width_mm - half_w)
    dn_y = cy + offset
    if dn_y + half_h <= table_height_mm:
        candidates.append((space_down, dn_x, dn_y, "down"))

    # RIGHT
    rt_x = cx + offset
    rt_y = _clamp(cy, half_w, table_height_mm - half_w)
    if rt_x + half_h <= table_width_mm:
        candidates.append((space_right, rt_x, rt_y, "right"))

    # LEFT
    lt_x = cx - offset
    lt_y = _clamp(cy, half_w, table_height_mm - half_w)
    if lt_x - half_h >= 0:
        candidates.append((space_left, lt_x, lt_y, "left"))

    if candidates:
        return _select_best_candidate(
            candidates, min(space_up, space_down, space_left, space_right)
        )

    return cx, cy, "up"
