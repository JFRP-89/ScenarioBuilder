"""Polygon point parsing, validation and unit conversion.

Pure functions — no Gradio, no side effects.
"""

from __future__ import annotations

import math
from typing import Any

from adapters.ui_gradio.units import convert_to_cm, convert_unit_to_unit


def parse_polygon_points(  # noqa: C901
    points_data: Any,
    scenography_unit_val: str,
) -> tuple[list[dict[str, int]], str | None]:
    """Parse polygon points from dataframe / list into mm dicts.

    Returns:
        ``(points_list, error_message)`` — *error_message* is ``None``
        on success.
    """
    if points_data is None:
        return [], "No polygon points provided"

    # Handle pandas DataFrame
    if hasattr(points_data, "values"):
        try:
            points_data = points_data.values.tolist()
        except Exception:
            points_data = []

    if not hasattr(points_data, "__iter__"):
        points_data = []

    points_list: list[dict[str, int]] = []
    for row in points_data:
        if row is None or (isinstance(row, (list, tuple)) and len(row) == 0):
            continue
        if isinstance(row, (list, tuple)):
            if len(row) < 2:
                continue
            x_raw, y_raw = row[0], row[1]
        else:
            continue

        if x_raw is None or y_raw is None:
            continue

        try:
            x_val = (
                float(str(x_raw).strip()) if isinstance(x_raw, str) else float(x_raw)
            )
            y_val = (
                float(str(y_raw).strip()) if isinstance(y_raw, str) else float(y_raw)
            )
            if (
                math.isnan(x_val)
                or math.isnan(y_val)
                or math.isinf(x_val)
                or math.isinf(y_val)
            ):
                continue
            x_mm = int(convert_to_cm(x_val, scenography_unit_val) * 10)
            y_mm = int(convert_to_cm(y_val, scenography_unit_val) * 10)
            points_list.append({"x": x_mm, "y": y_mm})
        except (ValueError, TypeError, AttributeError):
            continue

    if len(points_list) < 3:
        return points_list, (
            f"Polygon needs at least 3 valid points. " f"Found: {len(points_list)}"
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
    if polygon_data is None:
        return polygon_data

    try:
        if hasattr(polygon_data, "values"):
            points_list = polygon_data.values.tolist()
        elif isinstance(polygon_data, list):
            points_list = polygon_data
        else:
            return polygon_data

        converted: list[list[float]] = []
        for row in points_list:
            if row is not None and isinstance(row, (list, tuple)) and len(row) >= 2:
                try:
                    x_val = float(row[0])
                    y_val = float(row[1])
                    converted.append(
                        [
                            convert_unit_to_unit(x_val, prev_unit, new_unit),
                            convert_unit_to_unit(y_val, prev_unit, new_unit),
                        ]
                    )
                except (ValueError, TypeError):
                    pass

        return converted if converted else polygon_data
    except Exception:
        return polygon_data
