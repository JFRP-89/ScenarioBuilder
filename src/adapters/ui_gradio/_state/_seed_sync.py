"""Convert API-format shapes to Gradio UI state format.

When seed-generated shapes arrive from the use case layer, they are in
API/domain format (plain dicts).  The Gradio UI keeps shapes in a richer
state format with ``id``, ``label``, and ``data`` wrappers.  This module
bridges that gap so seed shapes can be injected into the editable
``gr.State`` components.
"""

from __future__ import annotations

import uuid
from typing import Any

# ── Deployment zones ──────────────────────────────────────────────────


def api_deployment_to_ui_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API deployment_shapes to deployment_zones UI state format.

    Each entry gets: ``{"id", "label", "data": <original shape dict>}``
    """
    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        zone_id = str(uuid.uuid4())[:8]
        desc = shape.get("description", "")
        label = f"{desc} (Zone {zone_id})" if desc else f"Zone {zone_id}"
        result.append(
            {
                "id": zone_id,
                "label": label,
                "data": dict(shape),  # shallow copy
            }
        )
    return result


# ── Objective points ─────────────────────────────────────────────────


def api_objectives_to_ui_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API objective_shapes to objective_points UI state format.

    Each entry gets: ``{"id", "cx", "cy"}`` plus optional ``"description"``.
    Note: objective state is flat — no ``"data"`` wrapper.
    """
    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        point_id = str(uuid.uuid4())[:8]
        entry: dict[str, Any] = {
            "id": point_id,
            "cx": shape.get("cx", 0),
            "cy": shape.get("cy", 0),
        }
        desc = shape.get("description", "")
        if desc:
            entry["description"] = desc
        result.append(entry)
    return result


# ── Scenography ──────────────────────────────────────────────────────


def _scenography_label(shape: dict[str, Any], elem_id: str) -> str:
    """Build a human-readable label for a scenography element."""
    desc = shape.get("description", "")
    stype = shape.get("type", "unknown")
    if stype == "circle":
        tag = f"Circle {elem_id}"
    elif stype == "rect":
        tag = f"Rect {elem_id}"
    elif stype == "polygon":
        pts = shape.get("points", [])
        tag = f"Polygon {elem_id} ({len(pts)} pts)"
    else:
        tag = f"{stype} {elem_id}"
    return f"{desc} ({tag})" if desc else tag


def api_scenography_to_ui_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API scenography_specs to scenography UI state format.

    Each entry gets:
    ``{"id", "type", "label", "data": <shape without allow_overlap>, "allow_overlap"}``
    """
    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        elem_id = str(uuid.uuid4())[:8]
        allow_overlap = shape.get("allow_overlap", False)
        # data dict: same as shape but without allow_overlap
        data = {k: v for k, v in shape.items() if k != "allow_overlap"}
        result.append(
            {
                "id": elem_id,
                "type": shape.get("type", "unknown"),
                "label": _scenography_label(shape, elem_id),
                "data": data,
                "allow_overlap": allow_overlap,
            }
        )
    return result
