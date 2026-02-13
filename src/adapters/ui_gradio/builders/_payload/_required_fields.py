"""Required-fields validation for scenario card generation.

Pure functions — no side effects, no UI dependencies.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.builders._payload._table import (
    TABLE_MAX_CM,
    TABLE_MIN_CM,
    UNIT_LIMITS,
)


def validate_required_fields(  # noqa: C901
    actor: str,
    name: str,
    m: str,
    armies_val: str,
    preset: str,
    width: float,
    height: float,
    unit: str,
    depl: str,
    lay: str,
    obj: str,
    init_priority: str,
    rules_state: list[dict[str, Any]],
    vp_state: list[dict[str, Any]],
    deployment_zones_state_val: list[dict[str, Any]],
    objective_points_state_val: list[dict[str, Any]],
    scenography_state_val: list[dict[str, Any]],
    default_actor_id: str,
) -> str | None:
    """Validate all required fields for scenario card generation.

    Args:
        All the form fields and state variables

    Returns:
        Error message if validation fails, None if all valid
    """
    missing = []

    # 1. Actor ID (required)
    actor_id = (actor or "").strip()
    if not actor_id:
        actor_id = default_actor_id
    if not actor_id:
        missing.append("Actor ID")

    # 2. Scenario Name (required)
    if not (name or "").strip():
        missing.append("Scenario Name")

    # 3. Game Mode (required)
    if not (m or "").strip():
        missing.append("Game Mode")

    # 4. Armies (required)
    if not (armies_val or "").strip():
        missing.append("Armies")

    # 5. Table Preset (required)
    if not (preset or "").strip():
        missing.append("Table Preset")

    # 6. Table dimensions validation if Custom
    if preset == "custom":
        if not width or not height or width <= 0 or height <= 0:
            missing.append("Table dimensions (Width and Height must be > 0)")
        else:
            limits = UNIT_LIMITS.get(unit, {})
            min_val = limits.get("min", TABLE_MIN_CM)
            max_val = limits.get("max", TABLE_MAX_CM)
            if (
                width < min_val
                or width > max_val
                or height < min_val
                or height > max_val
            ):
                missing.append(f"Table dimensions must be {min_val}-{max_val} {unit}")

    # 7. Deployment (required)
    if not (depl or "").strip():
        missing.append("Deployment")

    # 8. Layout (required)
    if not (lay or "").strip():
        missing.append("Layout")

    # 9. Objectives (required)
    if not (obj or "").strip():
        missing.append("Objectives")

    # 10. Initial Priority (required)
    if not (init_priority or "").strip():
        missing.append("Initial Priority")

    # 11. Special Rules validation: if any rule, both name and value required
    if rules_state:
        for idx, rule in enumerate(rules_state, 1):
            rule_name = (rule.get("name") or "").strip()
            rule_value = (rule.get("value") or "").strip()
            if not rule_name or not rule_value:
                missing.append(f"Special Rule #{idx}: both Name and Value are required")

    # 12. Victory Points validation: if any VP, description required
    if vp_state:
        for idx, vp in enumerate(vp_state, 1):
            vp_desc = (vp.get("description") or "").strip()
            if not vp_desc:
                missing.append(f"Victory Point #{idx}: Description is required")

    # 13. Deployment Zones validation: if any zone, all fields required
    if deployment_zones_state_val:
        for idx, zone in enumerate(deployment_zones_state_val, 1):
            zone_label = (zone.get("label") or "").strip()
            zone_data = zone.get("data", {})

            if not zone_label:
                missing.append(f"Deployment Zone #{idx}: Description is required")

            zone_type = zone_data.get("type", "rect")

            if zone_type == "polygon":
                # Triangle/polygon validation
                zone_points = zone_data.get("points", [])
                zone_corner = (zone_data.get("corner") or "").strip()

                if not zone_points:
                    missing.append(f"Deployment Zone #{idx}: Points are required")
                elif len(zone_points) < 3:
                    missing.append(
                        f"Deployment Zone #{idx}: At least 3 points required"
                        " for polygon"
                    )

                if not zone_corner:
                    missing.append(f"Deployment Zone #{idx}: Corner is required")

            else:
                # Rectangle validation
                zone_border = (zone_data.get("border") or "").strip()
                zone_x = zone_data.get("x")
                zone_y = zone_data.get("y")
                zone_width = zone_data.get("width")
                zone_height = zone_data.get("height")

                if not zone_border:
                    missing.append(f"Deployment Zone #{idx}: Border is required")
                if zone_x is None or zone_x < 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Separation X (mm) is required"
                        " and must be >= 0"
                    )
                if zone_y is None or zone_y < 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Separation Y (mm) is required"
                        " and must be >= 0"
                    )
                if not zone_width or zone_width <= 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Width (mm) is required"
                        " and must be > 0"
                    )
                if not zone_height or zone_height <= 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Height (mm) is required"
                        " and must be > 0"
                    )

    # 14. Objective Points validation: if any point, description and coordinates
    if objective_points_state_val:
        for idx, point in enumerate(objective_points_state_val, 1):
            point_desc = (point.get("description") or "").strip()
            point_cx = point.get("cx")
            point_cy = point.get("cy")

            if not point_desc:
                missing.append(f"Objective Point #{idx}: Description is required")
            if point_cx is None or point_cx < 0:
                missing.append(
                    f"Objective Point #{idx}: X Coordinate (mm) is required"
                    " and must be >= 0"
                )
            if point_cy is None or point_cy < 0:
                missing.append(
                    f"Objective Point #{idx}: Y Coordinate (mm) is required"
                    " and must be >= 0"
                )

    # 15. Scenography validation: if any element, description and type required
    # + type-specific fields
    if scenography_state_val:
        for idx, elem in enumerate(scenography_state_val, 1):
            elem_label = (elem.get("label") or "").strip()
            elem_type = (elem.get("type") or "").strip()
            elem_data = elem.get("data", {})

            if not elem_label:
                missing.append(f"Scenography Element #{idx}: Description is required")
            if not elem_type:
                missing.append(f"Scenography Element #{idx}: Element Type is required")

            if elem_type == "circle":
                cx = elem_data.get("cx")
                cy = elem_data.get("cy")
                r = elem_data.get("r")
                if cx is None or cx < 0:
                    missing.append(
                        f"Scenography Circle #{idx}: Center X (cx) is required"
                        " and must be >= 0"
                    )
                if cy is None or cy < 0:
                    missing.append(
                        f"Scenography Circle #{idx}: Center Y (cy) is required"
                        " and must be >= 0"
                    )
                if r is None or r <= 0:
                    missing.append(f"Scenography Circle #{idx}: Radius must be > 0")

            elif elem_type == "rect":
                x = elem_data.get("x")
                y = elem_data.get("y")
                width = elem_data.get("width")
                height = elem_data.get("height")
                if x is None or x < 0:
                    missing.append(
                        f"Scenography Rect #{idx}: X Position is required"
                        " and must be >= 0"
                    )
                if y is None or y < 0:
                    missing.append(
                        f"Scenography Rect #{idx}: Y Position is required"
                        " and must be >= 0"
                    )
                if width is None or width <= 0:
                    missing.append(f"Scenography Rect #{idx}: Width must be > 0")
                if height is None or height <= 0:
                    missing.append(f"Scenography Rect #{idx}: Height must be > 0")

            elif elem_type == "polygon":
                points = elem_data.get("points", [])
                if not points or len(points) < 3:
                    missing.append(
                        f"Scenography Polygon #{idx}: Must have at least 3 points"
                    )

    if missing:
        error_msg = "Missing or invalid required fields:\n\n" + "\n".join(
            f"\u2022 {m}" for m in missing
        )
        return error_msg

    return None
