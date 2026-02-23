"""Validate that all existing shapes fit within (possibly resized) table bounds.

Pure functions — no Gradio imports, no side effects.
"""

from __future__ import annotations

from typing import Any

# -- helpers ---------------------------------------------------------------


def _coord(point: Any, key: str) -> float:
    """Extract a coordinate from a point (dict or tuple/list)."""
    if isinstance(point, dict):
        return float(point.get(key, 0))
    if isinstance(point, (list, tuple)):
        idx = 0 if key == "x" else 1
        return float(point[idx]) if len(point) > idx else 0.0
    return 0.0


# -- per-shape validators --------------------------------------------------


def _rect_exceeds(data: dict[str, Any], table_w: int, table_h: int) -> bool:
    """Return *True* when a rect shape overflows the table."""
    x = float(data.get("x", 0))
    y = float(data.get("y", 0))
    w = float(data.get("width", 0))
    h = float(data.get("height", 0))
    return x + w > table_w or y + h > table_h


def _polygon_exceeds(data: dict[str, Any], table_w: int, table_h: int) -> bool:
    """Return *True* when any polygon vertex overflows the table."""
    for point in data.get("points", []):
        if _coord(point, "x") > table_w or _coord(point, "y") > table_h:
            return True
    return False


def _circle_exceeds(data: dict[str, Any], table_w: int, table_h: int) -> bool:
    """Return *True* when a circle shape overflows the table."""
    cx = float(data.get("cx", 0))
    cy = float(data.get("cy", 0))
    r = float(data.get("r", 0))
    return cx + r > table_w or cy + r > table_h or cx - r < 0 or cy - r < 0


def _overflow_msg(label: str, kind: str, table_w: int, table_h: int) -> str:
    """Build a human-readable overflow error message."""
    verb = "has points outside" if kind == "polygon" else "extends beyond"
    return f"{label} {verb} the new table size ({table_w}x{table_h} mm)"


# -- category checkers -----------------------------------------------------


def _check_deployment_zones(
    zones: list[dict[str, Any]],
    table_w: int,
    table_h: int,
) -> str | None:
    """Return an error message if any deployment zone exceeds the table."""
    for zone in zones:
        data: dict[str, Any] = zone.get("data", zone)
        zone_type = data.get("type", "rect")
        label = zone.get("label", "Deployment zone")

        overflows = (
            _polygon_exceeds(data, table_w, table_h)
            if zone_type == "polygon"
            else _rect_exceeds(data, table_w, table_h)
        )
        if overflows:
            return _overflow_msg(label, zone_type, table_w, table_h)
    return None


def _check_objective_points(
    points: list[dict[str, Any]],
    table_w: int,
    table_h: int,
) -> str | None:
    """Return an error message if any objective point is outside the table."""
    for pt in points:
        cx = float(pt.get("cx", 0))
        cy = float(pt.get("cy", 0))
        if cx > table_w or cy > table_h:
            desc = pt.get("description", "")
            label = f"Objective point '{desc}'" if desc else "An objective point"
            return (
                f"{label} at ({cx:.0f}, {cy:.0f}) is outside the new table size "
                f"({table_w}x{table_h} mm)"
            )
    return None


def _check_scenography(
    elements: list[dict[str, Any]],
    table_w: int,
    table_h: int,
) -> str | None:
    """Return an error message if any scenography element exceeds the table."""
    _CHECKER = {
        "circle": _circle_exceeds,
        "polygon": _polygon_exceeds,
        "rect": _rect_exceeds,
    }
    for elem in elements:
        data: dict[str, Any] = elem.get("data", elem)
        shape_type = data.get("type", "")
        label = elem.get("label", "Scenography element")

        checker = _CHECKER.get(shape_type)
        if checker and checker(data, table_w, table_h):
            return _overflow_msg(label, shape_type, table_w, table_h)
    return None


def check_all_shapes_fit_table(
    *,
    deployment_zones: list[dict[str, Any]],
    objective_points: list[dict[str, Any]],
    scenography: list[dict[str, Any]],
    table_width_mm: int,
    table_height_mm: int,
) -> str | None:
    """Check that every existing shape fits inside the given table dimensions.

    Returns the first error message found, or ``None`` if everything fits.
    """
    err = _check_deployment_zones(deployment_zones, table_width_mm, table_height_mm)
    if err:
        return err

    err = _check_objective_points(objective_points, table_width_mm, table_height_mm)
    if err:
        return err

    return _check_scenography(scenography, table_width_mm, table_height_mm)
