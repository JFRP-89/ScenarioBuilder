"""Polygon point parsing, validation and unit conversion.

Pure functions — no Gradio, no side effects.
"""

from __future__ import annotations

import math
from typing import Any

from adapters.ui_gradio.units import convert_unit_to_unit, to_mm

# ── Helpers (extracted to reduce cognitive complexity) ──────────────────


def _coerce_to_list(points_data: Any) -> list[Any]:
    """Normalise *points_data* into a plain Python list.

    Accepts pandas DataFrames, regular lists, and other iterables.
    Returns ``[]`` for unsupported types.
    """
    if points_data is None:
        return []
    if hasattr(points_data, "values"):
        try:
            return list(points_data.values.tolist())
        except (AttributeError, TypeError, ValueError):
            return []
    if hasattr(points_data, "__iter__"):
        return list(points_data)
    return []


def _parse_row_xy(row: Any) -> tuple[float, float] | None:
    """Return ``(x, y)`` floats from *row*, or ``None`` if invalid."""
    if row is None:
        return None
    if not isinstance(row, (list, tuple)) or len(row) < 2:
        return None
    x_raw, y_raw = row[0], row[1]
    if x_raw is None or y_raw is None:
        return None
    try:
        x = float(str(x_raw).strip()) if isinstance(x_raw, str) else float(x_raw)
        y = float(str(y_raw).strip()) if isinstance(y_raw, str) else float(y_raw)
    except (ValueError, TypeError):
        return None
    if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
        return None
    return x, y


# ── Public entry points ────────────────────────────────────────────────


def parse_polygon_points(
    points_data: Any,
    scenography_unit_val: str,
) -> tuple[list[dict[str, int]], str | None]:
    """Parse polygon points from dataframe / list into mm dicts.

    Returns:
        ``(points_list, error_message)`` — *error_message* is ``None``
        on success.
    """
    rows = _coerce_to_list(points_data)
    if not rows:
        return [], "No polygon points provided"

    points_list: list[dict[str, int]] = []
    for row in rows:
        xy = _parse_row_xy(row)
        if xy is None:
            continue
        x_mm = to_mm(xy[0], scenography_unit_val)
        y_mm = to_mm(xy[1], scenography_unit_val)
        points_list.append({"x": x_mm, "y": y_mm})

    if len(points_list) < 3:
        return points_list, (
            f"Polygon needs at least 3 valid points. Found: {len(points_list)}"
        )

    return points_list, None


def convert_polygon_points(
    polygon_data: Any,
    prev_unit: str,
    new_unit: str,
) -> Any:
    """Convert polygon point coordinates between units.

    Returns the converted points list, or *polygon_data* unchanged
    on failure.
    """
    rows = _coerce_to_list(polygon_data)
    if not rows:
        return polygon_data

    converted: list[list[float]] = []
    for row in rows:
        xy = _parse_row_xy(row)
        if xy is not None:
            converted.append(
                [
                    convert_unit_to_unit(xy[0], prev_unit, new_unit),
                    convert_unit_to_unit(xy[1], prev_unit, new_unit),
                ]
            )

    return converted if converted else polygon_data
