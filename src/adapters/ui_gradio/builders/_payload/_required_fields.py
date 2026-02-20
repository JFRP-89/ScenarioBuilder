"""Required-fields validation for scenario card generation.

Pure functions — no side effects, no UI dependencies.

The main entry point ``validate_required_fields`` delegates to small,
focused validators that each handle one logical domain (text fields,
table dimensions, special rules, etc.).  This keeps cyclomatic
complexity of every single function well below the C threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.ui_gradio.builders._payload._table import (
    TABLE_MAX_CM,
    TABLE_MIN_CM,
    UNIT_LIMITS,
)


@dataclass(frozen=True)
class ValidationInput:
    """Parameter object for ``validate_required_fields``.

    Groups the many UI fields into a single immutable snapshot
    so the public entry point has a clean one-parameter signature.
    """

    actor: str
    name: str
    mode: str
    armies: str
    preset: str
    width: float
    height: float
    unit: str
    deployment: str
    layout: str
    objectives: str
    initial_priority: str
    rules_state: list[dict[str, Any]]
    vp_state: list[dict[str, Any]]
    deployment_zones: list[dict[str, Any]]
    objective_points: list[dict[str, Any]]
    scenography: list[dict[str, Any]]
    default_actor_id: str


# ── Primitive-field validators ──────────────────────────────────────────


def _validate_text_fields(
    actor: str,
    name: str,
    m: str,
    armies_val: str,
    preset: str,
    depl: str,
    lay: str,
    obj: str,
    init_priority: str,
    default_actor_id: str,
) -> list[str]:
    """Validate simple required text fields (non-blank check)."""
    errors: list[str] = []

    actor_id = (actor or "").strip() or default_actor_id
    if not actor_id:
        errors.append("Actor ID")

    field_checks: list[tuple[str, str]] = [
        (name, "Scenario Name"),
        (m, "Game Mode"),
        (armies_val, "Armies"),
        (preset, "Table Preset"),
        (depl, "Deployment"),
        (lay, "Layout"),
        (obj, "Objectives"),
        (init_priority, "Initial Priority"),
    ]

    for value, label in field_checks:
        if not (value or "").strip():
            errors.append(label)

    return errors


def _validate_table_dimensions(
    preset: str,
    width: float,
    height: float,
    unit: str,
) -> list[str]:
    """Validate custom table dimensions when preset is ``custom``."""
    if preset != "custom":
        return []

    if not width or not height or width <= 0 or height <= 0:
        return ["Table dimensions (Width and Height must be > 0)"]

    limits = UNIT_LIMITS.get(unit, {})
    min_val = limits.get("min", TABLE_MIN_CM)
    max_val = limits.get("max", TABLE_MAX_CM)
    if width < min_val or width > max_val or height < min_val or height > max_val:
        return [f"Table dimensions must be {min_val}-{max_val} {unit}"]

    return []


# ── Collection validators ──────────────────────────────────────────────


def _validate_special_rules(rules_state: list[dict[str, Any]]) -> list[str]:
    """Validate that each special rule has both name and value."""
    errors: list[str] = []
    for idx, rule in enumerate(rules_state, 1):
        rule_name = (rule.get("name") or "").strip()
        rule_value = (rule.get("value") or "").strip()
        if not rule_name or not rule_value:
            errors.append(f"Special Rule #{idx}: both Name and Value are required")
    return errors


def _validate_victory_points(vp_state: list[dict[str, Any]]) -> list[str]:
    """Validate that each victory point has a description."""
    errors: list[str] = []
    for idx, vp in enumerate(vp_state, 1):
        vp_desc = (vp.get("description") or "").strip()
        if not vp_desc:
            errors.append(f"Victory Point #{idx}: Description is required")
    return errors


def _validate_zone_polygon(idx: int, zone_data: dict[str, Any]) -> list[str]:
    """Validate a polygon/triangle deployment zone."""
    errors: list[str] = []
    zone_points = zone_data.get("points", [])
    zone_corner = (zone_data.get("corner") or "").strip()

    if not zone_points:
        errors.append(f"Deployment Zone #{idx}: Points are required")
    elif len(zone_points) < 3:
        errors.append(f"Deployment Zone #{idx}: At least 3 points required for polygon")
    if not zone_corner:
        errors.append(f"Deployment Zone #{idx}: Corner is required")
    return errors


def _validate_zone_rect(idx: int, zone_data: dict[str, Any]) -> list[str]:
    """Validate a rectangle deployment zone."""
    errors: list[str] = []
    zone_border = (zone_data.get("border") or "").strip()
    zone_x = zone_data.get("x")
    zone_y = zone_data.get("y")
    zone_width = zone_data.get("width")
    zone_height = zone_data.get("height")

    if not zone_border:
        errors.append(f"Deployment Zone #{idx}: Border is required")
    if zone_x is None or zone_x < 0:
        errors.append(
            f"Deployment Zone #{idx}: Separation X (mm) is required" " and must be >= 0"
        )
    if zone_y is None or zone_y < 0:
        errors.append(
            f"Deployment Zone #{idx}: Separation Y (mm) is required" " and must be >= 0"
        )
    if not zone_width or zone_width <= 0:
        errors.append(f"Deployment Zone #{idx}: Width (mm) is required and must be > 0")
    if not zone_height or zone_height <= 0:
        errors.append(
            f"Deployment Zone #{idx}: Height (mm) is required and must be > 0"
        )
    return errors


def _validate_deployment_zones(
    zones: list[dict[str, Any]],
) -> list[str]:
    """Validate deployment zone entries."""
    errors: list[str] = []
    for idx, zone in enumerate(zones, 1):
        zone_label = (zone.get("label") or "").strip()
        zone_data = zone.get("data", {})

        if not zone_label:
            errors.append(f"Deployment Zone #{idx}: Description is required")

        zone_type = zone_data.get("type", "rect")
        if zone_type == "polygon":
            errors.extend(_validate_zone_polygon(idx, zone_data))
        else:
            errors.extend(_validate_zone_rect(idx, zone_data))
    return errors


def _validate_objective_points(
    points: list[dict[str, Any]],
) -> list[str]:
    """Validate objective point entries."""
    errors: list[str] = []
    for idx, point in enumerate(points, 1):
        point_desc = (point.get("description") or "").strip()
        point_cx = point.get("cx")
        point_cy = point.get("cy")

        if not point_desc:
            errors.append(f"Objective Point #{idx}: Description is required")
        if point_cx is None or point_cx < 0:
            errors.append(
                f"Objective Point #{idx}: X Coordinate (mm) is required"
                " and must be >= 0"
            )
        if point_cy is None or point_cy < 0:
            errors.append(
                f"Objective Point #{idx}: Y Coordinate (mm) is required"
                " and must be >= 0"
            )
    return errors


def _validate_scenography_circle(idx: int, data: dict[str, Any]) -> list[str]:
    """Validate a circle scenography element."""
    errors: list[str] = []
    if data.get("cx") is None or data.get("cx", -1) < 0:
        errors.append(
            f"Scenography Circle #{idx}: Center X (cx) is required and must be >= 0"
        )
    if data.get("cy") is None or data.get("cy", -1) < 0:
        errors.append(
            f"Scenography Circle #{idx}: Center Y (cy) is required and must be >= 0"
        )
    if data.get("r") is None or data.get("r", 0) <= 0:
        errors.append(f"Scenography Circle #{idx}: Radius must be > 0")
    return errors


def _validate_scenography_rect(idx: int, data: dict[str, Any]) -> list[str]:
    """Validate a rect scenography element."""
    errors: list[str] = []
    if data.get("x") is None or data.get("x", -1) < 0:
        errors.append(
            f"Scenography Rect #{idx}: X Position is required and must be >= 0"
        )
    if data.get("y") is None or data.get("y", -1) < 0:
        errors.append(
            f"Scenography Rect #{idx}: Y Position is required and must be >= 0"
        )
    if data.get("width") is None or data.get("width", 0) <= 0:
        errors.append(f"Scenography Rect #{idx}: Width must be > 0")
    if data.get("height") is None or data.get("height", 0) <= 0:
        errors.append(f"Scenography Rect #{idx}: Height must be > 0")
    return errors


def _validate_scenography_polygon(idx: int, data: dict[str, Any]) -> list[str]:
    """Validate a polygon scenography element."""
    points = data.get("points", [])
    if not points or len(points) < 3:
        return [f"Scenography Polygon #{idx}: Must have at least 3 points"]
    return []


def _validate_scenography_elements(
    elements: list[dict[str, Any]],
) -> list[str]:
    """Validate scenography element entries."""
    errors: list[str] = []
    _type_validators = {
        "circle": _validate_scenography_circle,
        "rect": _validate_scenography_rect,
        "polygon": _validate_scenography_polygon,
    }

    for idx, elem in enumerate(elements, 1):
        elem_label = (elem.get("label") or "").strip()
        elem_type = (elem.get("type") or "").strip()
        elem_data = elem.get("data", {})

        if not elem_label:
            errors.append(f"Scenography Element #{idx}: Description is required")
        if not elem_type:
            errors.append(f"Scenography Element #{idx}: Element Type is required")

        validator = _type_validators.get(elem_type)
        if validator:
            errors.extend(validator(idx, elem_data))
    return errors


# ── Public entry point ─────────────────────────────────────────────────


def validate_required_fields(
    fields: ValidationInput,
) -> str | None:
    """Validate all required fields for scenario card generation.

    Returns:
        Error message if validation fails, None if all valid.
    """
    missing: list[str] = []

    missing.extend(
        _validate_text_fields(
            fields.actor,
            fields.name,
            fields.mode,
            fields.armies,
            fields.preset,
            fields.deployment,
            fields.layout,
            fields.objectives,
            fields.initial_priority,
            fields.default_actor_id,
        )
    )
    missing.extend(
        _validate_table_dimensions(
            fields.preset, fields.width, fields.height, fields.unit
        )
    )

    if fields.rules_state:
        missing.extend(_validate_special_rules(fields.rules_state))
    if fields.vp_state:
        missing.extend(_validate_victory_points(fields.vp_state))
    if fields.deployment_zones:
        missing.extend(_validate_deployment_zones(fields.deployment_zones))
    if fields.objective_points:
        missing.extend(_validate_objective_points(fields.objective_points))
    if fields.scenography:
        missing.extend(_validate_scenography_elements(fields.scenography))

    if missing:
        error_msg = "Missing or invalid required fields:\n\n" + "\n".join(
            f"\u2022 {m}" for m in missing
        )
        return error_msg

    return None
