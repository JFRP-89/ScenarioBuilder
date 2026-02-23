"""Table configuration helpers for payload construction.

Pure functions — no side effects, no UI dependencies.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.units import convert_to_cm

# Table size limits (from domain)
TABLE_MIN_CM = 60
TABLE_MAX_CM = 300

# Unit limits
UNIT_LIMITS: dict[str, dict[str, float]] = {
    "cm": {"min": TABLE_MIN_CM, "max": TABLE_MAX_CM},
    "in": {"min": 24, "max": 120},
    "ft": {"min": 2, "max": 10},
}


def apply_table_config(
    payload: dict[str, Any],
    preset: str,
    width: float,
    height: float,
    unit: str,
) -> tuple[dict[str, float] | None, dict[str, Any] | None]:
    """Apply table configuration to payload (preset or custom dimensions).

    Args:
        payload: Request payload (modified in-place)
        preset: Table preset ("standard", "massive", or "custom")
        width: Table width value
        height: Table height value
        unit: Unit of measurement ("cm", "in", or "ft")

    Returns:
        Tuple of (custom_table_dict, error_dict)
        - custom_table_dict: Non-None if custom table was built
        - error_dict: Non-None if validation error occurred
    """
    if preset == "custom":
        width_cm = convert_to_cm(width, unit)
        height_cm = convert_to_cm(height, unit)

        if (
            width_cm < TABLE_MIN_CM
            or width_cm > TABLE_MAX_CM
            or height_cm < TABLE_MIN_CM
            or height_cm > TABLE_MAX_CM
        ):
            limits = UNIT_LIMITS.get(unit, UNIT_LIMITS["cm"])
            return None, {
                "status": "error",
                "message": (
                    f"Invalid table dimensions. "
                    f"Check limits ({limits['min']}-{limits['max']} {unit})."
                ),
            }

        custom_table = {"width_cm": width_cm, "height_cm": height_cm}
        payload["table_preset"] = "custom"  # Send preset as "custom"
        payload["table_cm"] = custom_table
        return custom_table, None

    payload["table_preset"] = preset
    return None, None
