"""Unit conversion and table-dimension helpers.

Pure functions — no Gradio imports, no side effects.
"""

from __future__ import annotations

from adapters.ui_gradio.constants import (
    CM_PER_FOOT,
    CM_PER_INCH,
    TABLE_MAX_CM,
    TABLE_MIN_CM,
)


# =============================================================================
# Unit conversion helpers
# =============================================================================
def convert_to_cm(value: float, unit: str) -> float:
    """Convert dimension to centimeters based on unit."""
    if unit == "in":
        return float(value * CM_PER_INCH)
    if unit == "ft":
        return float(value * CM_PER_FOOT)
    return value


def convert_from_cm(value_cm: float, target_unit: str) -> float:
    """Convert from centimeters to target unit."""
    if target_unit == "in":
        return float(value_cm / CM_PER_INCH)
    if target_unit == "ft":
        return float(value_cm / CM_PER_FOOT)
    return value_cm


def convert_unit_to_unit(value: float, from_unit: str, to_unit: str) -> float:
    """Convert value from one unit to another.

    Returns:
        Converted value rounded to 2 decimals.
    """
    if from_unit == to_unit:
        return value
    value_cm = convert_to_cm(value, from_unit)
    result = convert_from_cm(value_cm, to_unit)
    return round(result, 2)


def build_custom_table_payload(
    width: float, height: float, unit: str
) -> dict[str, float] | None:
    """Build custom table dimensions in cm.

    Returns:
        dict with width_cm and height_cm, or None if invalid.
    """
    if width <= 0 or height <= 0:
        return None

    width_cm = convert_to_cm(width, unit)
    height_cm = convert_to_cm(height, unit)

    if (
        width_cm < TABLE_MIN_CM
        or width_cm > TABLE_MAX_CM
        or height_cm < TABLE_MIN_CM
        or height_cm > TABLE_MAX_CM
    ):
        return None

    return {"width_cm": width_cm, "height_cm": height_cm}


def to_mm(value: float, unit: str) -> int:
    """Convert a user-unit value to integer millimetres."""
    return int(convert_to_cm(value, unit) * 10)
