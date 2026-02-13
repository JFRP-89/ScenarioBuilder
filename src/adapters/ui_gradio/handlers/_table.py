"""Table configuration and zone dimension handlers."""

from __future__ import annotations

from typing import Any, Callable

import gradio as gr


# =============================================================================
# Table configuration handlers
# =============================================================================
def on_table_preset_change(
    preset: str,
    current_unit: str,
    table_standard_cm: tuple[float, float],
    table_massive_cm: tuple[float, float],
    convert_from_cm: Callable[[float, str], float],
) -> tuple[dict[str, Any], float, float]:
    """Handle table preset change, auto-filling width/height in current unit.

    Args:
        preset: Selected preset ("standard", "massive", "custom")
        current_unit: Current unit selection
        table_standard_cm: Standard table dimensions (w, h) in cm
        table_massive_cm: Massive table dimensions (w, h) in cm
        convert_from_cm: Function to convert from cm to target unit

    Returns:
        Tuple of (visibility_update, width, height)
    """
    if preset == "custom":
        return gr.update(visible=True), 120.0, 120.0

    # Auto-fill based on preset
    if preset == "standard":
        w_cm, h_cm = table_standard_cm
    else:  # massive
        w_cm, h_cm = table_massive_cm

    # Convert to current unit
    width = convert_from_cm(w_cm, current_unit)
    height = convert_from_cm(h_cm, current_unit)

    return gr.update(visible=False), round(width, 2), round(height, 2)


def on_table_unit_change(
    new_unit: str,
    width: float,
    height: float,
    prev_unit: str,
    unit_limits: dict[str, dict[str, float]],
    convert_unit_to_unit: Callable[[float, str, str], float],
) -> tuple[float, float, str]:
    """Handle table unit change, converting width/height values.

    Args:
        new_unit: New unit selection
        width: Current width value
        height: Current height value
        prev_unit: Previous unit
        unit_limits: Dict of unit limits {unit: {min, max}}
        convert_unit_to_unit: Function to convert between units

    Returns:
        Tuple of (new_width, new_height, new_prev_unit)
    """
    if not width or not height or prev_unit == new_unit:
        return width, height, new_unit

    # Convert values
    new_width = convert_unit_to_unit(width, prev_unit, new_unit)
    new_height = convert_unit_to_unit(height, prev_unit, new_unit)

    # Validate against limits for new unit
    limits = unit_limits[new_unit]
    new_width = max(limits["min"], min(limits["max"], new_width))
    new_height = max(limits["min"], min(limits["max"], new_height))

    return round(new_width, 2), round(new_height, 2), new_unit


def update_objective_defaults(
    table_width: float,
    table_height: float,
    table_unit: str,
    convert_to_cm: Callable[[float, str], float],
) -> tuple[float, float]:
    """Calculate center point of table in mm.

    Args:
        table_width: Table width value
        table_height: Table height value
        table_unit: Table unit
        convert_to_cm: Function to convert to cm

    Returns:
        Tuple of (center_x_mm, center_y_mm)
    """
    table_w_mm = convert_to_cm(table_width, table_unit) * 10
    table_h_mm = convert_to_cm(table_height, table_unit) * 10
    return table_w_mm / 2, table_h_mm / 2


# =============================================================================
# Deployment zone handlers
# =============================================================================
def on_zone_border_or_fill_change(
    border: str,
    fill_side: bool,
    table_width_mm: int = 1200,
    table_height_mm: int = 1200,
) -> tuple[float, float]:
    """Update zone dimensions when border or fill side changes.

    Args:
        border: Border position (north, south, east, west)
        fill_side: Whether to fill full side
        table_width_mm: Table width in mm
        table_height_mm: Table height in mm

    Returns:
        Tuple of (width, height)
    """
    if border in ("north", "south"):
        if fill_side:
            return float(table_width_mm), 200.0
        else:
            return 1200.0, 200.0
    else:  # east or west
        if fill_side:
            return 200.0, float(table_height_mm)
        else:
            return 200.0, 1200.0
