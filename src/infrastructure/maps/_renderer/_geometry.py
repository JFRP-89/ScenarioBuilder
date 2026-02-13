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
# Label positioning
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
    offset_distance = 50
    extra_horizontal_offset = 50
    space_up = cy
    space_down = table_height_mm - cy
    space_left = cx
    space_right = table_width_mm - cx

    near_threshold = offset_distance + 30

    near_left = space_left < near_threshold
    near_right = space_right < near_threshold
    near_top = space_up < near_threshold
    near_bottom = space_down < near_threshold

    positions: list[tuple[int, int, str]] = []

    if near_top and near_left:
        positions.extend(
            [
                (cx, cy + offset_distance, "down"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                (cx, cy - offset_distance, "up"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
            ]
        )
    elif near_top and near_right:
        positions.extend(
            [
                (cx, cy + offset_distance, "down"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                (cx, cy - offset_distance, "up"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
            ]
        )
    elif near_bottom and near_left:
        positions.extend(
            [
                (cx, cy - offset_distance, "up"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                (cx, cy + offset_distance, "down"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
            ]
        )
    elif near_bottom and near_right:
        positions.extend(
            [
                (cx, cy - offset_distance, "up"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                (cx, cy + offset_distance, "down"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
            ]
        )
    elif near_left and not near_right:
        positions.extend(
            [
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                (cx, cy - offset_distance, "up"),
                (cx, cy + offset_distance, "down"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
            ]
        )
    elif near_right and not near_left:
        positions.extend(
            [
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                (cx, cy - offset_distance, "up"),
                (cx, cy + offset_distance, "down"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
            ]
        )
    elif near_top and not near_bottom:
        positions.extend(
            [
                (cx, cy + offset_distance, "down"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                (cx, cy - offset_distance, "up"),
            ]
        )
    elif near_bottom and not near_top:
        positions.extend(
            [
                (cx, cy - offset_distance, "up"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
                (cx, cy + offset_distance, "down"),
            ]
        )
    else:
        positions.extend(
            [
                (cx, cy - offset_distance, "up"),
                (cx, cy + offset_distance, "down"),
                (cx + offset_distance + extra_horizontal_offset, cy, "right"),
                (cx - offset_distance - extra_horizontal_offset, cy, "left"),
            ]
        )

    return positions


def find_best_objective_position(  # noqa: C901
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

    space_up = cy
    space_down = table_height_mm - cy
    space_left = cx
    space_right = table_width_mm - cx

    candidates: list[tuple[int, int, int, str]] = []

    # UP
    text_x_up = cx
    text_y_up = cy - offset
    if text_x_up - text_width // 2 < 0:
        text_x_up = text_width // 2
    elif text_x_up + text_width // 2 > table_width_mm:
        text_x_up = table_width_mm - text_width // 2
    if text_y_up - text_height // 2 >= 0:
        candidates.append((space_up, text_x_up, text_y_up, "up"))

    # DOWN
    text_x_down = cx
    text_y_down = cy + offset
    if text_x_down - text_width // 2 < 0:
        text_x_down = text_width // 2
    elif text_x_down + text_width // 2 > table_width_mm:
        text_x_down = table_width_mm - text_width // 2
    if text_y_down + text_height // 2 <= table_height_mm:
        candidates.append((space_down, text_x_down, text_y_down, "down"))

    # RIGHT
    text_x_right = cx + offset
    text_y_right = cy
    if text_y_right - text_width // 2 < 0:
        text_y_right = text_width // 2
    elif text_y_right + text_width // 2 > table_height_mm:
        text_y_right = table_height_mm - text_width // 2
    if text_x_right + text_height // 2 <= table_width_mm:
        candidates.append((space_right, text_x_right, text_y_right, "right"))

    # LEFT
    text_x_left = cx - offset
    text_y_left = cy
    if text_y_left - text_width // 2 < 0:
        text_y_left = text_width // 2
    elif text_y_left + text_width // 2 > table_height_mm:
        text_y_left = table_height_mm - text_width // 2
    if text_x_left - text_height // 2 >= 0:
        candidates.append((space_left, text_x_left, text_y_left, "left"))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)

        min_edge_dist = min(space_up, space_down, space_left, space_right)
        if min_edge_dist >= 200:
            preference_order = ["up", "down", "right", "left"]
            for preferred_dir in preference_order:
                for _space, x, y, direction in candidates:
                    if direction == preferred_dir:
                        return x, y, direction

        _, best_x, best_y, best_dir = candidates[0]
        return best_x, best_y, best_dir

    return cx, cy, "up"
