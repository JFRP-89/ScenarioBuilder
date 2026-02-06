"""Shape builders for Gradio UI adapter.

Pure helpers that convert UI state to API shape payloads.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.ui_types import (
    DeploymentZoneItem,
    ObjectivePointItem,
    ScenographyItem,
)


def build_map_specs_from_state(
    scenography_state: list[ScenographyItem],
) -> list[dict[str, Any]]:
    """Build map_specs payload from scenography state.

    Args:
        scenography_state: List of scenography elements with data and allow_overlap

    Returns:
        List of shape dicts sorted with allow_overlap=True first
    """
    sorted_state = sorted(
        scenography_state, key=lambda x: not x.get("allow_overlap", False)
    )

    result = []
    for elem in sorted_state:
        shape = dict(elem["data"])
        shape["allow_overlap"] = elem.get("allow_overlap", False)
        result.append(shape)

    return result


def build_deployment_shapes_from_state(
    deployment_zones_state: list[DeploymentZoneItem],
) -> list[dict[str, Any]]:
    """Build deployment_shapes payload from deployment zones state.

    Removes internal fields (depth, separation) not needed in API payload.

    Args:
        deployment_zones_state: List of zones with id, label, data

    Returns:
        List of zone dicts for payload (only: type, description, x, y, width, height, border)
    """
    result = []
    for zone in deployment_zones_state:
        shape = dict(zone["data"])
        shape.pop("depth", None)
        shape.pop("separation", None)
        result.append(shape)

    return result


def build_objective_shapes_from_state(
    objective_points_state: list[ObjectivePointItem],
) -> list[dict[str, Any]]:
    """Build objective_shapes payload from objective points state.

    Args:
        objective_points_state: List of points with cx, cy, optional description

    Returns:
        List of objective_point dicts for payload (type, cx, cy, optional description)
    """
    result = []
    for point in objective_points_state:
        shape = {
            "type": "objective_point",
            "cx": int(point["cx"]),
            "cy": int(point["cy"]),
        }
        if point.get("description"):
            shape["description"] = point["description"]
        result.append(shape)

    return result
