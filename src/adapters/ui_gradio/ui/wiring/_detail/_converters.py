"""API → UI state format converters for the detail / edit flow.

Each function converts a raw API dict (as returned by the Flask backend)
into the internal state format expected by Gradio form components.
Pure functions — no Gradio, no API calls.
"""

from __future__ import annotations

import uuid
from typing import Any


def _short_id() -> str:
    """Generate a short (8-char) unique identifier."""
    return str(uuid.uuid4())[:8]


# ============================================================================
# Objectives
# ============================================================================


def _extract_objectives_text_for_form(
    objectives: Any,
) -> tuple[str, bool, list[dict[str, Any]]]:
    """Extract form values from objectives data.

    Returns (objectives_text, vp_enabled, vp_state_list).
    The vp_state_list uses the UI state format: {id, description}.
    """
    if isinstance(objectives, dict):
        obj_text = str(objectives.get("objective", ""))
        vp_items = objectives.get("victory_points", [])
        vp_enabled = bool(vp_items)
        vp_list = (
            [{"id": _short_id(), "description": str(vp)} for vp in vp_items]
            if isinstance(vp_items, list) and vp_items
            else []
        )
        return obj_text, vp_enabled, vp_list
    if isinstance(objectives, str):
        return objectives, False, []
    return "", False, []


# ============================================================================
# Special rules
# ============================================================================


def _api_special_rules_to_state(
    api_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API special rules to UI state format.

    API format: {"name": "...", "description": "..."} or {"name": "...", "source": "..."}
    State format: {"id": "xxx", "name": "...", "rule_type": "description|source", "value": "..."}
    """
    result: list[dict[str, Any]] = []
    for rule in api_rules:
        if not isinstance(rule, dict):
            continue
        sid = _short_id()
        name = rule.get("name", "")
        # Determine rule_type and value from API format
        if "source" in rule:
            rule_type = "source"
            value = rule.get("source", "")
        else:
            rule_type = "description"
            value = rule.get("description", "")
        result.append(
            {
                "id": sid,
                "name": name,
                "rule_type": rule_type,
                "value": value,
            }
        )
    return result


# ============================================================================
# Deployment zones
# ============================================================================


def _api_deployment_to_state(api_shapes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert API deployment shapes to UI state format.

    API: {"type": "rect", "description": "D", "x": 0, ...}
    State: {"id": "xxx", "label": "D (Zone xxx)", "data": {...}, "form_type": "rectangle"}
    """
    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        if not isinstance(shape, dict):
            continue
        sid = _short_id()
        desc = shape.get("description", "") or ""
        shape_type = shape.get("type", "rect")

        # Determine form_type from shape type
        if shape_type == "rect":
            form_type = "rectangle"
        elif shape_type == "polygon":
            # Could be triangle or circle — guess from point count
            points = shape.get("points", [])
            form_type = "triangle" if len(points) <= 4 else "circle"
        else:
            form_type = "rectangle"

        label = f"{desc} (Zone {sid})" if desc else f"Zone {sid}"
        entry: dict[str, Any] = {
            "id": sid,
            "label": label,
            "data": dict(shape),  # copy the full API shape as data
            "form_type": form_type,
        }
        result.append(entry)
    return result


# ============================================================================
# Scenography
# ============================================================================


def _api_scenography_to_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API scenography shapes to UI state format.

    API: {"type": "circle", "cx": 300, "cy": 400, "r": 150, ...}
    State: {"id": "xxx", "type": "circle", "label": "desc (Circle xxx)",
            "data": {...}, "allow_overlap": false}
    """
    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        if not isinstance(shape, dict):
            continue
        sid = _short_id()
        shape_type = shape.get("type", "rect")
        desc = shape.get("description", "") or ""
        allow_overlap = shape.get("allow_overlap", False)

        type_label = shape_type.capitalize()
        label = f"{desc} ({type_label} {sid})" if desc else f"{type_label} {sid}"

        # Build data without the allow_overlap key (it lives on the outer entry)
        data = {k: v for k, v in shape.items() if k != "allow_overlap"}

        entry: dict[str, Any] = {
            "id": sid,
            "type": shape_type,
            "label": label,
            "data": data,
            "allow_overlap": allow_overlap,
        }
        result.append(entry)
    return result


# ============================================================================
# Objective points
# ============================================================================


def _api_objectives_to_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API objective shapes to UI state format.

    API: {"type": "objective_point", "cx": 600, "cy": 600, "description": "T"}
    State: {"id": "xxx", "cx": 600, "cy": 600, "description": "T"}
    """
    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        if not isinstance(shape, dict):
            continue
        sid = _short_id()
        entry: dict[str, Any] = {
            "id": sid,
            "cx": shape.get("cx", 0),
            "cy": shape.get("cy", 0),
        }
        desc = shape.get("description", "")
        if desc:
            entry["description"] = desc
        result.append(entry)
    return result
