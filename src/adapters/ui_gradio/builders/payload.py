"""Payload construction and validation for Gradio UI adapter.

Pure helpers that build HTTP request payloads from UI state.
No side effects, no HTTP calls, no UI dependencies.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.ui_types import ErrorDict, SpecialRuleItem

# Table size limits (from domain)
TABLE_MIN_CM = 60
TABLE_MAX_CM = 300

# Unit limits
UNIT_LIMITS: dict[str, dict[str, float]] = {
    "cm": {"min": TABLE_MIN_CM, "max": TABLE_MAX_CM},
    "in": {"min": 24, "max": 120},
    "ft": {"min": 2, "max": 10},
}


def build_generate_payload(mode: str, seed: int | None) -> dict[str, Any]:
    """Build base payload for generate card request.

    Args:
        mode: Game mode
        seed: Optional seed for generation

    Returns:
        Dict with mode and seed fields
    """
    return {
        "mode": mode,
        "seed": int(seed) if seed else None,
    }


def apply_table_config(
    payload: dict[str, Any],
    preset: str,
    width: float,
    height: float,
    unit: str,
) -> tuple[dict[str, float] | None, dict[str, Any] | None]:
    """Apply table configuration to payload (preset or custom dimensions).

    Args:
        payload: Request payload (modified in-place)
        preset: Table preset ("standard", "massive", or "custom")
        width: Table width value
        height: Table height value
        unit: Unit of measurement ("cm" or "inches")

    Returns:
        Tuple of (custom_table_dict, error_dict)
        - custom_table_dict: Non-None if custom table was built
        - error_dict: Non-None if validation error occurred
    """
    if preset == "custom":
        # Convert to cm
        if unit == "inches":
            width_cm = width * 2.54
            height_cm = height * 2.54
        else:
            width_cm = width
            height_cm = height

        if (
            width_cm < TABLE_MIN_CM
            or width_cm > TABLE_MAX_CM
            or height_cm < TABLE_MIN_CM
            or height_cm > TABLE_MAX_CM
        ):
            return None, {
                "status": "error",
                "message": "Invalid table dimensions. Check limits (60-300 cm).",
            }

        custom_table = {"width_cm": width_cm, "height_cm": height_cm}
        payload["table_preset"] = "custom"  # Send preset as "custom"
        payload["table_cm"] = custom_table
        return custom_table, None

    payload["table_preset"] = preset
    return None, None


def apply_optional_text_fields(
    payload: dict[str, Any],
    deployment: str | None = None,
    layout: str | None = None,
    objectives: str | None = None,
    initial_priority: str | None = None,
    armies: str | None = None,
    name: str | None = None,
) -> None:
    """Add optional text fields to payload if provided.

    Args:
        payload: Request payload (modified in-place)
        deployment: Deployment text
        layout: Layout text
        objectives: Objectives text
        initial_priority: Initial priority text
        armies: Armies text
        name: Scenario name
    """
    field_map = {
        "armies": armies,
        "deployment": deployment,
        "layout": layout,
        "objectives": objectives,
        "initial_priority": initial_priority,
        "name": name,
    }

    for key, value in field_map.items():
        if value and value.strip():
            payload[key] = value.strip()


def apply_special_rules(
    payload: dict[str, Any],
    rules_state: list[SpecialRuleItem],
) -> ErrorDict | None:
    """Validate and add special_rules to payload.

    Args:
        payload: Request payload (modified in-place)
        rules_state: Rules state list with name, rule_type, value

    Returns:
        Error dict if validation fails, None otherwise
    """
    if not rules_state:
        return None

    normalized = []
    for idx, rule in enumerate(rules_state, 1):
        name = str(rule.get("name", "")).strip()
        rule_type = str(rule.get("rule_type", "")).strip()
        value = str(rule.get("value", "")).strip()

        if not name:
            return {"status": "error", "message": f"Rule {idx}: Name is required"}
        if not rule_type or rule_type not in ("description", "source"):
            return {
                "status": "error",
                "message": f"Rule {idx}: Must specify description or source",
            }
        if not value:
            return {"status": "error", "message": f"Rule {idx}: Value cannot be empty"}

        normalized_rule: dict[str, str] = {"name": name}
        if rule_type == "description":
            normalized_rule["description"] = value
        else:
            normalized_rule["source"] = value

        normalized.append(normalized_rule)

    payload["special_rules"] = normalized
    return None


def apply_visibility(
    payload: dict[str, Any],
    visibility: str,
    shared_with_text: str | None = None,
) -> None:
    """Add visibility configuration to payload.

    Args:
        payload: Request payload (modified in-place)
        visibility: Visibility level ("private", "public", "shared")
        shared_with_text: Comma-separated user IDs (for shared visibility)
    """
    payload["visibility"] = visibility

    if visibility == "shared" and shared_with_text and shared_with_text.strip():
        users = [u.strip() for u in shared_with_text.split(",") if u.strip()]
        if users:
            payload["shared_with"] = users


def validate_victory_points(
    vp_state: list[dict[str, Any]],
) -> tuple[list[str] | None, str | None]:
    """Validate victory points from state.

    Args:
        vp_state: List of victory point dicts with description

    Returns:
        Tuple of (normalized_vps, error_message)
    """
    if not vp_state:
        return [], None

    normalized: list[str] = []
    for idx, vp in enumerate(vp_state, 1):
        description = str(vp.get("description", "")).strip()
        if not description:
            return None, f"Victory Point {idx}: Description cannot be empty"
        normalized.append(description)

    return normalized, None


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
                        f"Deployment Zone #{idx}: At least 3 points required for polygon"
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
                        f"Deployment Zone #{idx}: Separation X (mm) is required and must be >= 0"
                    )
                if zone_y is None or zone_y < 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Separation Y (mm) is required and must be >= 0"
                    )
                if not zone_width or zone_width <= 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Width (mm) is required and must be > 0"
                    )
                if not zone_height or zone_height <= 0:
                    missing.append(
                        f"Deployment Zone #{idx}: Height (mm) is required and must be > 0"
                    )

    # 14. Objective Points validation: if any point, description and coordinates required
    if objective_points_state_val:
        for idx, point in enumerate(objective_points_state_val, 1):
            point_desc = (point.get("description") or "").strip()
            point_cx = point.get("cx")
            point_cy = point.get("cy")

            if not point_desc:
                missing.append(f"Objective Point #{idx}: Description is required")
            if point_cx is None or point_cx < 0:
                missing.append(
                    f"Objective Point #{idx}: X Coordinate (mm) is required and must be >= 0"
                )
            if point_cy is None or point_cy < 0:
                missing.append(
                    f"Objective Point #{idx}: Y Coordinate (mm) is required and must be >= 0"
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
                        f"Scenography Circle #{idx}: Center X (cx) is required and must be >= 0"
                    )
                if cy is None or cy < 0:
                    missing.append(
                        f"Scenography Circle #{idx}: Center Y (cy) is required and must be >= 0"
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
                        f"Scenography Rect #{idx}: X Position is required and must be >= 0"
                    )
                if y is None or y < 0:
                    missing.append(
                        f"Scenography Rect #{idx}: Y Position is required and must be >= 0"
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
            f"• {m}" for m in missing
        )
        return error_msg

    return None
