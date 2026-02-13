"""Deployment zones state helpers."""

from __future__ import annotations

import uuid
from typing import Any

from adapters.ui_gradio.constants import (
    DEPLOYMENT_MAX_ZONES,
    DEPLOYMENT_ZONE_MAX_SIZE,
    DEPLOYMENT_ZONE_MIN_SIZE,
)


def validate_deployment_zone_within_table(  # noqa: C901
    zone: dict[str, Any], table_width_mm: int, table_height_mm: int
) -> str | None:
    """Validate deployment zone fits within table bounds (in mm)."""
    zone_type = zone.get("type", "rect")

    if zone_type == "polygon":
        # Validate polygon (triangle) points
        points = zone.get("points", [])
        if not points:
            return "Polygon zone must have points"

        for i, point in enumerate(points):
            # Support both dict format {"x": ..., "y": ...} and tuple/list format
            if isinstance(point, dict):
                if "x" not in point or "y" not in point:
                    return f"Invalid point format at index {i}: missing x or y"
                x = point["x"]
                y = point["y"]
            elif isinstance(point, (list, tuple)) and len(point) == 2:
                x, y = point
            else:
                return f"Invalid point format at index {i}"

            if x < 0 or x > table_width_mm:
                return f"Polygon point {i} extends beyond table width: ({x}, {y})"
            if y < 0 or y > table_height_mm:
                return f"Polygon point {i} extends beyond table height: ({x}, {y})"
        return None

    # Validate rectangle zone
    x = float(zone.get("x", 0))
    y = float(zone.get("y", 0))
    width = float(zone.get("width", 0))
    height = float(zone.get("height", 0))

    if x < 0 or x + width > table_width_mm:
        return "Deployment zone extends beyond table width"
    if y < 0 or y + height > table_height_mm:
        return "Deployment zone extends beyond table height"
    if width < DEPLOYMENT_ZONE_MIN_SIZE or width > DEPLOYMENT_ZONE_MAX_SIZE:
        return (
            f"Zone width must be between "
            f"{DEPLOYMENT_ZONE_MIN_SIZE} and {DEPLOYMENT_ZONE_MAX_SIZE} mm"
        )
    if height < DEPLOYMENT_ZONE_MIN_SIZE or height > DEPLOYMENT_ZONE_MAX_SIZE:
        return (
            f"Zone height must be between "
            f"{DEPLOYMENT_ZONE_MIN_SIZE} and {DEPLOYMENT_ZONE_MAX_SIZE} mm"
        )
    return None


def calculate_zone_coordinates(
    border: str,
    height_width: float,
    separation: float,
    table_width_mm: int,
    table_height_mm: int,
) -> tuple[float, float, float, float]:
    """Calculate zone coordinates based on border.

    Returns:
        Tuple of (x, y, width, height).
    """
    if border == "north":
        x = 0.0
        y = float(separation)
        width = float(table_width_mm)
        height = float(height_width)
    elif border == "south":
        x = 0.0
        y = float(table_height_mm - height_width - separation)
        width = float(table_width_mm)
        height = float(height_width)
    elif border == "east":
        x = float(table_width_mm - height_width - separation)
        y = 0.0
        width = float(height_width)
        height = float(table_height_mm)
    else:  # west
        x = float(separation)
        y = 0.0
        width = float(height_width)
        height = float(table_height_mm)

    return x, y, width, height


def validate_separation_coords(
    border: str,
    zone_width: int,
    zone_height: int,
    sep_x: float,
    sep_y: float,
    table_width_mm: int,
    table_height_mm: int,
) -> tuple[float, float]:
    """Calculate final zone coordinates based on border and separation.

    Coordinate logic:
        NORTH: x = sep_x, y = sep_y
        SOUTH: x = sep_x, y = (max_y - sep_y)
        WEST:  x = sep_x, y = sep_y
        EAST:  x = (max_x - sep_x), y = sep_y

    Returns:
        Tuple of (final_x, final_y) representing zone top-left corner.
    """
    max_x = max(0, table_width_mm - zone_width)
    max_y = max(0, table_height_mm - zone_height)
    clamped_x = max(0, min(sep_x, max_x))
    clamped_y = max(0, min(sep_y, max_y))

    if border == "north":
        x = clamped_x
        y = clamped_y

    elif border == "south":
        x = clamped_x
        y = max_y - clamped_y

    elif border == "west":
        x = clamped_x
        y = clamped_y

    else:  # east
        x = max_x - clamped_x
        y = clamped_y

    return x, y


def deployment_zones_overlap(zone1: dict[str, Any], zone2: dict[str, Any]) -> bool:
    """Check if two deployment zones overlap."""

    def get_bounding_box(zone: dict[str, Any]) -> tuple[float, float, float, float]:
        """Get bounding box (x, y, width, height) for any zone type."""
        zone_type = zone.get("type", "rect")

        if zone_type == "polygon":
            points = zone.get("points", [])
            if not points:
                return (0, 0, 0, 0)

            xs: list[float] = []
            ys: list[float] = []
            for p in points:
                if isinstance(p, dict):
                    xs.append(p.get("x", 0))
                    ys.append(p.get("y", 0))
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    xs.append(p[0])
                    ys.append(p[1])

            if not xs or not ys:
                return (0, 0, 0, 0)

            min_x, max_x_val = min(xs), max(xs)
            min_y, max_y_val = min(ys), max(ys)
            return (min_x, min_y, max_x_val - min_x, max_y_val - min_y)
        else:
            # Rectangle
            rx = float(zone.get("x", 0))
            ry = float(zone.get("y", 0))
            w = float(zone.get("width", 0))
            h = float(zone.get("height", 0))
            return (rx, ry, w, h)

    x1, y1, w1, h1 = get_bounding_box(zone1)
    x2, y2, w2, h2 = get_bounding_box(zone2)

    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)


def calculate_zone_depth(table_dimension: float, percentage: float) -> float:
    """Calculate zone depth from percentage."""
    return table_dimension * (percentage / 100)


def calculate_zone_separation(table_dimension: float, percentage: float) -> float:
    """Calculate zone separation from percentage."""
    return table_dimension * (percentage / 100)


def add_deployment_zone(
    current_state: list[dict[str, Any]],
    zone_data: dict[str, Any],
    table_width_mm: int,
    table_height_mm: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """Add new deployment zone to state.

    Args:
        current_state: Current deployment zones state.
        zone_data: Zone data dict (type, description, x, y, width, height, border).
        table_width_mm: Table width in mm.
        table_height_mm: Table height in mm.

    Returns:
        Tuple of (updated_state, error_message).
    """
    if len(current_state) >= DEPLOYMENT_MAX_ZONES:
        return current_state, f"Maximum {DEPLOYMENT_MAX_ZONES} deployment zones allowed"

    # Validate within table bounds
    error = validate_deployment_zone_within_table(
        zone_data, table_width_mm, table_height_mm
    )
    if error:
        return current_state, error

    # Check overlap with existing zones
    for existing in current_state:
        if deployment_zones_overlap(zone_data, existing["data"]):
            return current_state, "Deployment zones cannot overlap"

    zone_id = str(uuid.uuid4())[:8]
    description = zone_data.get("description", "").strip()
    label = f"{description} (Zone {zone_id})" if description else f"Zone {zone_id}"

    new_state = [
        *current_state,
        {
            "id": zone_id,
            "label": label,
            "data": zone_data,
        },
    ]
    return new_state, None


def remove_last_deployment_zone(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove last deployment zone from state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_deployment_zone(
    current_state: list[dict[str, Any]], zone_id: str
) -> list[dict[str, Any]]:
    """Remove selected deployment zone from state."""
    return [zone for zone in current_state if zone["id"] != zone_id]


def get_deployment_zones_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from deployment zones state."""
    if not state:
        return [("No zones", "")]
    return [(zone["label"], zone["id"]) for zone in state]


def update_deployment_zone(
    current_state: list[dict[str, Any]],
    zone_id: str,
    zone_data: dict[str, Any],
    table_width_mm: int,
    table_height_mm: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """Update an existing deployment zone in place.

    Validates bounds and overlap with other zones (excluding self).
    """
    error = validate_deployment_zone_within_table(
        zone_data, table_width_mm, table_height_mm
    )
    if error:
        return current_state, error

    for existing in current_state:
        if existing["id"] == zone_id:
            continue
        if deployment_zones_overlap(zone_data, existing["data"]):
            return current_state, "Deployment zones cannot overlap"

    description = zone_data.get("description", "").strip()
    label = f"{description} (Zone {zone_id})" if description else f"Zone {zone_id}"

    updated_state: list[dict[str, Any]] = []
    for zone in current_state:
        if zone["id"] == zone_id:
            updated_state.append({**zone, "label": label, "data": zone_data})
        else:
            updated_state.append(zone)
    return updated_state, None
