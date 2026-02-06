"""Shape normalization helpers for use case responses.

This module provides utilities to normalize shapes from use case responses
into formats compatible with domain entities (MapSpec).

Context:
--------
Use cases return shapes as dict with structure:
    {"deployment_shapes": [...], "objective_shapes": [...], "scenography_specs": [...]}

Domain (MapSpec) expects:
    - shapes: list[dict] (flat list for validation)
    - objective_shapes: list[dict] | None (separate parameter)

These helpers bridge the gap between use case response structure and domain requirements.
"""

from __future__ import annotations


def flatten_map_shapes(shapes_response: dict | list[dict]) -> list[dict]:
    """Flatten shapes response into flat list for MapSpec.

    Combines deployment_shapes and scenography_specs from structured response
    into a single flat list that MapSpec can validate.

    Args:
        shapes_response: Either a dict with deployment_shapes/scenography_specs keys,
                        or already a flat list[dict] (legacy/fallback).

    Returns:
        Flat list of shape dicts suitable for MapSpec(shapes=...).

    Examples:
        >>> shapes = {
        ...     "deployment_shapes": [{"type": "rect", ...}],
        ...     "scenography_specs": [{"type": "circle", ...}],
        ... }
        >>> flatten_map_shapes(shapes)
        [{"type": "rect", ...}, {"type": "circle", ...}]

        >>> shapes = [{"type": "rect", ...}]  # Legacy format
        >>> flatten_map_shapes(shapes)
        [{"type": "rect", ...}]
    """
    if isinstance(shapes_response, dict):
        result = []
        result.extend(shapes_response.get("deployment_shapes", []))
        result.extend(shapes_response.get("scenography_specs", []))
        return result
    else:
        # Legacy fallback: already a list
        return shapes_response


def extract_objective_shapes(shapes_response: dict | list[dict]) -> list[dict] | None:
    """Extract objective_shapes from use case response.

    Objective shapes are stored separately in MapSpec and need special handling.

    Args:
        shapes_response: Use case response shapes (dict or list).

    Returns:
        List of objective shape dicts, or None if not present.

    Examples:
        >>> shapes = {"objective_shapes": [{"type": "circle", "cx": 100, "cy": 100}]}
        >>> extract_objective_shapes(shapes)
        [{"type": "circle", "cx": 100, "cy": 100}]

        >>> shapes = [{"type": "rect", ...}]  # No objective_shapes key
        >>> extract_objective_shapes(shapes)
        None
    """
    if isinstance(shapes_response, dict):
        return shapes_response.get("objective_shapes")
    else:
        # Legacy format: no objective_shapes separation
        return None


def normalize_shapes_for_map_spec(
    shapes_response: dict | list[dict],
) -> tuple[list[dict], list[dict] | None]:
    """Normalize shapes response for MapSpec construction.

    Convenience function that combines flatten_map_shapes and extract_objective_shapes.

    Args:
        shapes_response: Use case response shapes.

    Returns:
        Tuple of (flat_shapes, objective_shapes) ready for MapSpec constructor.

    Examples:
        >>> shapes = {
        ...     "deployment_shapes": [{"type": "rect", ...}],
        ...     "scenography_specs": [{"type": "circle", ...}],
        ...     "objective_shapes": [{"type": "circle", "cx": 100, "cy": 100}]
        ... }
        >>> flat_shapes, objective_shapes = normalize_shapes_for_map_spec(shapes)
        >>> # flat_shapes = [{"type": "rect", ...}, {"type": "circle", ...}]
        >>> # objective_shapes = [{"type": "circle", "cx": 100, "cy": 100}]
    """
    flat_shapes = flatten_map_shapes(shapes_response)
    objective_shapes = extract_objective_shapes(shapes_response)
    return flat_shapes, objective_shapes
