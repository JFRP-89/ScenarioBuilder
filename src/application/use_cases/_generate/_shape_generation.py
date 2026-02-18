"""Deterministic shape generation from seeds."""

from __future__ import annotations

import random
from typing import Any

from application.use_cases._generate._themes import (
    DEPLOYMENT_DESCRIPTIONS as _DEPLOYMENT_DESCRIPTIONS,
)
from application.use_cases._generate._themes import (
    OBJECTIVE_DESCRIPTIONS as _OBJECTIVE_DESCRIPTIONS,
)
from application.use_cases._generate._themes import (
    SCENOGRAPHY_DESCRIPTIONS_OVERLAP as _SCENOGRAPHY_DESCRIPTIONS_OVERLAP,
)
from application.use_cases._generate._themes import (
    SCENOGRAPHY_DESCRIPTIONS_SOLID as _SCENOGRAPHY_DESCRIPTIONS_SOLID,
)


def _generate_random_scenography(
    rng: random.Random,
    width: int,
    height: int,
    allow_overlap: bool,
    index: int,
) -> dict[str, Any]:
    """Generate a single random scenography shape within table bounds."""
    descriptions = (
        _SCENOGRAPHY_DESCRIPTIONS_OVERLAP
        if allow_overlap
        else _SCENOGRAPHY_DESCRIPTIONS_SOLID
    )
    desc = rng.choice(descriptions)
    margin = 50
    shape_type = rng.choice(["circle", "rect", "polygon"])

    if shape_type == "circle":
        max_r = min(width, height) // 8
        r = rng.randint(50, max(51, max_r))
        cx = rng.randint(margin + r, width - margin - r)
        cy = rng.randint(margin + r, height - margin - r)
        return {
            "type": "circle",
            "description": desc,
            "cx": cx,
            "cy": cy,
            "r": r,
            "allow_overlap": allow_overlap,
        }

    if shape_type == "rect":
        max_w = width // 4
        max_h = height // 4
        sw = rng.randint(100, max(101, max_w))
        sh = rng.randint(100, max(101, max_h))
        x = rng.randint(margin, max(margin + 1, width - margin - sw))
        y = rng.randint(margin, max(margin + 1, height - margin - sh))
        return {
            "type": "rect",
            "description": desc,
            "x": x,
            "y": y,
            "width": sw,
            "height": sh,
            "allow_overlap": allow_overlap,
        }

    # polygon (triangle)
    cx = rng.randint(width // 4, 3 * width // 4)
    cy = rng.randint(height // 4, 3 * height // 4)
    size = rng.randint(80, min(width, height) // 5)
    points = [
        {"x": min(width, max(0, cx)), "y": max(0, cy - size)},
        {"x": min(width, cx + size), "y": min(height, cy + size)},
        {"x": max(0, cx - size), "y": min(height, cy + size)},
    ]
    return {
        "type": "polygon",
        "description": desc,
        "points": points,
        "allow_overlap": allow_overlap,
    }


def _build_non_overlapping_deployments(
    selected_edges: list[str],
    dep_depth: int,
    table_width: int,
    table_height: int,
) -> list[dict[str, Any]]:
    """Build deployment zone rectangles that never overlap each other.

    East/West zones are placed first at full height, then North/South
    zones are inset horizontally to avoid colliding with any E/W zones.
    This guarantees zero pixel overlap between any two deployment rects.
    """
    has_east = "east" in selected_edges
    has_west = "west" in selected_edges

    # Horizontal inset for N/S zones: shrink to avoid E/W columns
    ns_x = dep_depth if has_west else 0
    ns_w = table_width - (dep_depth if has_west else 0) - (dep_depth if has_east else 0)

    # Vertical inset for E/W zones: shrink to avoid N/S rows
    has_north = "north" in selected_edges
    has_south = "south" in selected_edges
    ew_y = dep_depth if has_north else 0
    ew_h = (
        table_height - (dep_depth if has_north else 0) - (dep_depth if has_south else 0)
    )

    result: list[dict[str, Any]] = []
    for i, edge in enumerate(selected_edges):
        desc = _DEPLOYMENT_DESCRIPTIONS[i]
        if edge == "north":
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": ns_x,
                    "y": 0,
                    "width": ns_w,
                    "height": dep_depth,
                    "border": "north",
                }
            )
        elif edge == "south":
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": ns_x,
                    "y": table_height - dep_depth,
                    "width": ns_w,
                    "height": dep_depth,
                    "border": "south",
                }
            )
        elif edge == "east":
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": table_width - dep_depth,
                    "y": ew_y,
                    "width": dep_depth,
                    "height": ew_h,
                    "border": "east",
                }
            )
        else:  # west
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": 0,
                    "y": ew_y,
                    "width": dep_depth,
                    "height": ew_h,
                    "border": "west",
                }
            )
    return result


def _generate_seeded_shapes(
    seed: int,
    table_width: int,
    table_height: int,
) -> dict[str, list[dict[str, Any]]]:
    """Generate deterministic shapes from a seed and table dimensions.

    Uses a separate RNG (seeded from ``f"shapes-{seed}"``) so that shape
    generation is completely independent of text-field auto-fill order.

    Produces:
    - 0-4 deployment_shapes (border rectangles)
    - 0-10 objective_shapes (objective_point markers)
    - 0-3 scenography with allow_overlap=False (solid terrain)
    - 0-3 scenography with allow_overlap=True (passable terrain)
    """
    rng = random.Random(f"shapes-{seed}")  # nosec B311

    # ── Deployment zones (0-4 border rectangles, non-overlapping) ──────
    n_deployment = rng.randint(0, 4)
    dep_depth = min(table_width, table_height) // 6
    edges = ["north", "south", "east", "west"]
    rng.shuffle(edges)
    selected_edges = edges[:n_deployment]
    deployment_shapes = _build_non_overlapping_deployments(
        selected_edges, dep_depth, table_width, table_height
    )

    # ── Objective points (0-10) ──────────────────────────────────────────
    n_objectives = rng.randint(0, 10)
    objective_shapes: list[dict[str, Any]] = []
    for i in range(n_objectives):
        cx = rng.randint(dep_depth, table_width - dep_depth)
        cy = rng.randint(dep_depth, table_height - dep_depth)
        desc = _OBJECTIVE_DESCRIPTIONS[i % len(_OBJECTIVE_DESCRIPTIONS)]
        objective_shapes.append(
            {
                "type": "objective_point",
                "cx": cx,
                "cy": cy,
                "description": desc,
            }
        )

    # ── Scenography (0-3 solid + 0-3 passable) ──────────────────────────
    n_solid = rng.randint(0, 3)
    n_passable = rng.randint(0, 3)
    scenography_specs: list[dict[str, Any]] = []
    for i in range(n_solid):
        scenography_specs.append(
            _generate_random_scenography(
                rng, table_width, table_height, allow_overlap=False, index=i
            )
        )
    for i in range(n_passable):
        scenography_specs.append(
            _generate_random_scenography(
                rng, table_width, table_height, allow_overlap=True, index=i
            )
        )

    return {
        "deployment_shapes": deployment_shapes,
        "objective_shapes": objective_shapes,
        "scenography_specs": scenography_specs,
    }
