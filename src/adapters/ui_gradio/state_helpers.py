"""UI state helper functions for Gradio adapter.

Pure helpers for manipulating state, validating geometry and unit conversion.
No Gradio imports — only stdlib + typing.
"""

from __future__ import annotations

import math
import os
import uuid
from typing import Any

from adapters.ui_gradio.constants import (
    DEPLOYMENT_MAX_ZONES,
    DEPLOYMENT_ZONE_MAX_SIZE,
    DEPLOYMENT_ZONE_MIN_SIZE,
)


# =============================================================================
# Config helpers
# =============================================================================
def get_default_actor_id() -> str:
    """Get default actor ID from environment."""
    return os.environ.get("DEFAULT_ACTOR_ID", "demo-user")


# =============================================================================
# Special Rules helpers
# =============================================================================
def add_special_rule(
    current_state: list[dict[str, Any]],
    rule_type: str = "description",
) -> list[dict[str, Any]]:
    """Add a new empty rule to the state.

    Args:
        current_state: Current rules state.
        rule_type: Type of rule (description or source).

    Returns:
        Updated rules state.
    """
    new_rule = {
        "id": str(uuid.uuid4())[:8],
        "name": "New Rule",
        "rule_type": rule_type,
        "value": "",
    }
    return [*current_state, new_rule]


def remove_last_special_rule(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove the last rule from the state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_special_rule(
    current_state: list[dict[str, Any]], rule_id: str
) -> list[dict[str, Any]]:
    """Remove selected rule from state."""
    return [rule for rule in current_state if rule.get("id") != rule_id]


def get_special_rules_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from special rules state."""
    if not state:
        return []
    return [(f"{rule['name']} ({rule['rule_type']})", rule["id"]) for rule in state]


# =============================================================================
# Victory Points helpers
# =============================================================================
def add_victory_point(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add a new empty victory point to the state."""
    new_vp = {
        "id": str(uuid.uuid4())[:8],
        "description": "",
    }
    return [*current_state, new_vp]


def remove_last_victory_point(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove the last victory point from the state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_victory_point(
    current_state: list[dict[str, Any]], vp_id: str
) -> list[dict[str, Any]]:
    """Remove selected victory point from state."""
    return [vp for vp in current_state if vp.get("id") != vp_id]


def get_victory_points_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from victory points state."""
    if not state:
        return []
    return [
        (vp["description"][:50] if vp["description"] else "Empty", vp["id"])
        for vp in state
    ]


# =============================================================================
# Geometry helpers (bounds)
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


# =============================================================================
# Scenography state manipulation
# =============================================================================
def add_scenography_element(
    current_state: list[dict[str, Any]],
    element_type: str,
    form_data: dict[str, Any],
    allow_overlap: bool,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Add new scenography element to state."""
    elem_id = str(uuid.uuid4())[:8]
    data: dict[str, Any] = {"type": element_type}

    description = description.strip() if description else ""
    if description:
        data["description"] = description

    if element_type == "circle":
        data["cx"] = int(form_data.get("cx", 0))
        data["cy"] = int(form_data.get("cy", 0))
        data["r"] = int(form_data.get("r", 0))
        label = (
            f"{description} (Circle {elem_id})" if description else f"Circle {elem_id}"
        )

    elif element_type == "rect":
        data["x"] = int(form_data.get("x", 0))
        data["y"] = int(form_data.get("y", 0))
        data["width"] = int(form_data.get("width", 0))
        data["height"] = int(form_data.get("height", 0))
        label = f"{description} (Rect {elem_id})" if description else f"Rect {elem_id}"

    elif element_type == "polygon":
        points = form_data.get("points", [])
        data["points"] = points
        label = (
            f"{description} (Polygon {elem_id} - {len(points)} pts)"
            if description
            else f"Polygon {elem_id} ({len(points)} pts)"
        )

    else:
        return current_state, f"Unknown element type: {element_type}"

    error = validate_shape_within_table(data, table_width_mm, table_height_mm)
    if error:
        return current_state, error

    if not allow_overlap:
        for existing in current_state:
            if not existing.get("allow_overlap", False) and shapes_overlap(
                data, existing["data"]
            ):
                return current_state, f"Shape overlaps with {existing['label']}"

    new_element = {
        "id": elem_id,
        "type": element_type,
        "label": label,
        "data": data,
        "allow_overlap": allow_overlap,
    }

    return [*current_state, new_element], None


def remove_last_scenography_element(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove last element from scenography state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_scenography_element(
    current_state: list[dict[str, Any]], selected_id: str
) -> list[dict[str, Any]]:
    """Remove selected element from scenography state."""
    return [elem for elem in current_state if elem["id"] != selected_id]


def get_scenography_choices(state: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Get dropdown choices from scenography state."""
    if not state:
        return [("No elements", "")]
    return [(elem["label"], elem["id"]) for elem in state]


# =============================================================================
# Deployment Zones helpers
# =============================================================================
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
    """Check if two deployment zones overlap (using AABB for rectangles and bounding boxes for polygons)."""

    def get_bounding_box(zone: dict[str, Any]) -> tuple[float, float, float, float]:
        """Get bounding box (x, y, width, height) for any zone type."""
        zone_type = zone.get("type", "rect")

        if zone_type == "polygon":
            points = zone.get("points", [])
            if not points:
                return (0, 0, 0, 0)

            # Support both dict format {"x": ..., "y": ...} and tuple/list format
            xs = []
            ys = []
            for p in points:
                if isinstance(p, dict):
                    xs.append(p.get("x", 0))
                    ys.append(p.get("y", 0))
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    xs.append(p[0])
                    ys.append(p[1])

            if not xs or not ys:
                return (0, 0, 0, 0)

            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            return (min_x, min_y, max_x - min_x, max_y - min_y)
        else:
            # Rectangle
            x = float(zone.get("x", 0))
            y = float(zone.get("y", 0))
            w = float(zone.get("width", 0))
            h = float(zone.get("height", 0))
            return (x, y, w, h)

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


# =============================================================================
# Objective Points helpers
# =============================================================================
def add_objective_point(
    current_state: list[dict[str, Any]],
    cx: float,
    cy: float,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Add a new objective point to state.

    Returns:
        Tuple of (updated_state, error_message).
    """
    # Check max 10 limit
    if len(current_state) >= 10:
        return current_state, "Maximum 10 objective points allowed per board"

    # Validate bounds
    if cx < 0 or cx > table_width_mm:
        return (
            current_state,
            f"Objective point X coordinate {cx} out of bounds (0-{table_width_mm})",
        )
    if cy < 0 or cy > table_height_mm:
        return (
            current_state,
            f"Objective point Y coordinate {cy} out of bounds (0-{table_height_mm})",
        )

    # Check for duplicate coordinates
    for existing_point in current_state:
        if existing_point["cx"] == cx and existing_point["cy"] == cy:
            return (
                current_state,
                f"Objective point already exists at coordinates ({cx:.0f}, {cy:.0f})",
            )

    description = description.strip() if description else ""
    new_point: dict[str, Any] = {
        "id": str(uuid.uuid4())[:8],
        "cx": cx,
        "cy": cy,
    }
    if description:
        new_point["description"] = description

    return [*current_state, new_point], None


def remove_last_objective_point(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove the last objective point from the state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_objective_point(
    current_state: list[dict[str, Any]], point_id: str
) -> list[dict[str, Any]]:
    """Remove selected objective point from state."""
    return [point for point in current_state if point.get("id") != point_id]


def get_objective_points_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from objective points state."""
    if not state:
        return [("No points", "")]
    return [
        (
            (
                f"{point.get('description', '')} ({point['cx']:.0f}, {point['cy']:.0f})"
                if point.get("description")
                else f"Point ({point['cx']:.0f}, {point['cy']:.0f})"
            ),
            point["id"],
        )
        for point in state
    ]


# =============================================================================
# Update helpers (for inline editing of existing elements)
# =============================================================================


def update_special_rule(
    current_state: list[dict[str, Any]],
    rule_id: str,
    name: str,
    rule_type: str,
    value: str,
) -> list[dict[str, Any]]:
    """Update an existing special rule in place."""
    return [
        (
            {**rule, "name": name, "rule_type": rule_type, "value": value}
            if rule["id"] == rule_id
            else rule
        )
        for rule in current_state
    ]


def update_victory_point(
    current_state: list[dict[str, Any]],
    vp_id: str,
    description: str,
) -> list[dict[str, Any]]:
    """Update an existing victory point in place."""
    return [
        {**vp, "description": description} if vp["id"] == vp_id else vp
        for vp in current_state
    ]


def update_objective_point(
    current_state: list[dict[str, Any]],
    point_id: str,
    cx: float,
    cy: float,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Update an existing objective point in place.

    Validates bounds and duplicate coords, excluding the point being edited.
    """
    if cx < 0 or cx > table_width_mm:
        return (
            current_state,
            f"Objective point X coordinate {cx} out of bounds (0-{table_width_mm})",
        )
    if cy < 0 or cy > table_height_mm:
        return (
            current_state,
            f"Objective point Y coordinate {cy} out of bounds (0-{table_height_mm})",
        )

    for existing_point in current_state:
        if existing_point["id"] == point_id:
            continue
        if existing_point["cx"] == cx and existing_point["cy"] == cy:
            return (
                current_state,
                f"Objective point already exists at coordinates ({cx:.0f}, {cy:.0f})",
            )

    description = description.strip() if description else ""
    updated: list[dict[str, Any]] = []
    for point in current_state:
        if point["id"] == point_id:
            new_point: dict[str, Any] = {**point, "cx": cx, "cy": cy}
            if description:
                new_point["description"] = description
            elif "description" in new_point:
                del new_point["description"]
            updated.append(new_point)
        else:
            updated.append(point)
    return updated, None


def update_scenography_element(  # noqa: C901
    current_state: list[dict[str, Any]],
    elem_id: str,
    element_type: str,
    form_data: dict[str, Any],
    allow_overlap: bool,
    table_width_mm: int,
    table_height_mm: int,
    description: str = "",
) -> tuple[list[dict[str, Any]], str | None]:
    """Update an existing scenography element in place.

    Validates bounds and overlap with other elements (excluding self).
    """
    data: dict[str, Any] = {"type": element_type}

    description = description.strip() if description else ""
    if description:
        data["description"] = description

    if element_type == "circle":
        data["cx"] = int(form_data.get("cx", 0))
        data["cy"] = int(form_data.get("cy", 0))
        data["r"] = int(form_data.get("r", 0))
        label = (
            f"{description} (Circle {elem_id})" if description else f"Circle {elem_id}"
        )
    elif element_type == "rect":
        data["x"] = int(form_data.get("x", 0))
        data["y"] = int(form_data.get("y", 0))
        data["width"] = int(form_data.get("width", 0))
        data["height"] = int(form_data.get("height", 0))
        label = f"{description} (Rect {elem_id})" if description else f"Rect {elem_id}"
    elif element_type == "polygon":
        points = form_data.get("points", [])
        data["points"] = points
        label = (
            f"{description} (Polygon {elem_id} - {len(points)} pts)"
            if description
            else f"Polygon {elem_id} ({len(points)} pts)"
        )
    else:
        return current_state, f"Unknown element type: {element_type}"

    error = validate_shape_within_table(data, table_width_mm, table_height_mm)
    if error:
        return current_state, error

    if not allow_overlap:
        for existing in current_state:
            if existing["id"] == elem_id:
                continue
            if not existing.get("allow_overlap", False) and shapes_overlap(
                data, existing["data"]
            ):
                return current_state, f"Shape overlaps with {existing['label']}"

    updated_state: list[dict[str, Any]] = []
    for elem in current_state:
        if elem["id"] == elem_id:
            updated_state.append(
                {
                    "id": elem_id,
                    "type": element_type,
                    "label": label,
                    "data": data,
                    "allow_overlap": allow_overlap,
                }
            )
        else:
            updated_state.append(elem)
    return updated_state, None


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
