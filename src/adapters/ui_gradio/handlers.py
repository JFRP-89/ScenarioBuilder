"""Event handlers for Gradio UI.

Pure functions that respond to UI events (clicks, changes, etc).
These handlers don't capture closures - they only depend on their parameters.
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Callable

import gradio as gr
from adapters.ui_gradio.ui_types import (
    SpecialRuleItem,
    VictoryPointItem,
)


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
# Visibility toggle handlers
# =============================================================================
def toggle_vp_section(enabled: bool) -> dict[str, Any]:
    """Show/hide VP section when toggle changes.

    Args:
        enabled: Whether section is enabled

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=enabled)
    return update


def toggle_deployment_zones_section(enabled: bool) -> dict[str, Any]:
    """Show/hide Deployment Zones section when toggle changes.

    Args:
        enabled: Whether section is enabled

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=enabled)
    return update


def toggle_scenography_section(enabled: bool) -> dict[str, Any]:
    """Show/hide Scenography section when toggle changes.

    Args:
        enabled: Whether section is enabled

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=enabled)
    return update


def toggle_objective_points_section(enabled: bool) -> dict[str, Any]:
    """Show/hide Objective Points section when toggle changes.

    Args:
        enabled: Whether section is enabled

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=enabled)
    return update


def toggle_special_rules_section(enabled: bool) -> dict[str, Any]:
    """Show/hide Special Rules section when toggle changes.

    Args:
        enabled: Whether section is enabled

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=enabled)
    return update


def toggle_scenography_forms(elem_type: str) -> dict[str, dict[str, Any]]:
    """Show/hide forms based on selected element type.

    Args:
        elem_type: Element type (circle, rect, polygon)

    Returns:
        Dict with form visibility updates
    """
    return {
        "circle_form_row": gr.update(visible=(elem_type == "circle")),
        "rect_form_row": gr.update(visible=(elem_type == "rect")),
        "polygon_form_col": gr.update(visible=(elem_type == "polygon")),
    }


def update_shared_with_visibility(visibility: str) -> dict[str, Any]:
    """Show/hide shared_with row based on visibility selection.

    Args:
        visibility: Visibility mode (private, public, shared)

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=(visibility == "shared"))
    return update


# =============================================================================
# Special Rules handlers
# =============================================================================
def add_special_rule(
    current_state: list[SpecialRuleItem],
    rule_type: str,
    name_input: str,
    value_input: str,
    get_choices_fn: Callable[[list[SpecialRuleItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Add special rule with validation.

    Args:
        current_state: Current rules state
        rule_type: Rule type (description or source)
        name_input: Rule name
        value_input: Rule value
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and UI updates
    """
    name_stripped = (name_input or "").strip()
    value_stripped = (value_input or "").strip()

    if not name_stripped or not value_stripped:
        error_msg = "Special Rule requires both Name and Value to be filled."
        if not name_stripped and not value_stripped:
            error_msg = "Special Rule requires both Name and Value to be filled."
        elif not name_stripped:
            error_msg = "Special Rule requires Name to be filled."
        else:
            error_msg = "Special Rule requires Value to be filled."

        return {
            "special_rules_state": current_state,
            "rules_list": gr.update(),
            "rule_name_input": name_input,
            "rule_value_input": value_input,
            "output": {"status": "error", "message": error_msg},
        }

    # Create rule with current input values
    new_rule = {
        "id": str(uuid.uuid4())[:8],
        "name": name_stripped,
        "rule_type": rule_type,
        "value": value_stripped,
    }
    new_state = [*current_state, new_rule]
    choices = get_choices_fn(new_state)

    return {
        "special_rules_state": new_state,
        "rules_list": gr.update(choices=choices),
        "rule_name_input": "",
        "rule_value_input": "",
        "output": {"status": "success"},
    }


def remove_last_special_rule(
    current_state: list[SpecialRuleItem],
    remove_fn: Callable[[list[SpecialRuleItem]], list[SpecialRuleItem]],
    get_choices_fn: Callable[[list[SpecialRuleItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Remove last special rule.

    Args:
        current_state: Current rules state
        remove_fn: Function to remove last rule
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and choices
    """
    new_state = remove_fn(current_state)
    choices = get_choices_fn(new_state)
    return {
        "special_rules_state": new_state,
        "rules_list": gr.update(choices=choices),
    }


def remove_selected_special_rule(
    selected_id: str | None,
    current_state: list[SpecialRuleItem],
    remove_fn: Callable[[list[SpecialRuleItem], str], list[SpecialRuleItem]],
    get_choices_fn: Callable[[list[SpecialRuleItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Remove selected special rule.

    Args:
        selected_id: ID of rule to remove
        current_state: Current rules state
        remove_fn: Function to remove selected rule
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and choices
    """
    if not selected_id:
        return {
            "special_rules_state": current_state,
            "rules_list": gr.update(),
        }
    new_state = remove_fn(current_state, selected_id)
    choices = get_choices_fn(new_state)
    return {
        "special_rules_state": new_state,
        "rules_list": gr.update(choices=choices),
    }


# =============================================================================
# Victory Points handlers
# =============================================================================
def add_victory_point(
    current_state: list[VictoryPointItem],
    description: str,
    add_fn: Callable[[list[VictoryPointItem]], list[VictoryPointItem]],
    get_choices_fn: Callable[[list[VictoryPointItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Add victory point.

    Args:
        current_state: Current VP state
        description: VP description
        add_fn: Function to add VP
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and UI updates
    """
    desc = description.strip()
    if not desc:
        return {
            "vp_state": current_state,
            "vp_list": gr.update(),
            "vp_input": gr.update(value=""),
        }
    new_state = add_fn(current_state)
    new_state[-1]["description"] = desc
    choices = get_choices_fn(new_state)
    return {
        "vp_state": new_state,
        "vp_list": gr.update(choices=choices),
        "vp_input": gr.update(value=""),
    }


def remove_last_victory_point(
    current_state: list[VictoryPointItem],
    remove_fn: Callable[[list[VictoryPointItem]], list[VictoryPointItem]],
    get_choices_fn: Callable[[list[VictoryPointItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Remove last victory point.

    Args:
        current_state: Current VP state
        remove_fn: Function to remove last VP
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and choices
    """
    new_state = remove_fn(current_state)
    choices = get_choices_fn(new_state)
    return {
        "vp_state": new_state,
        "vp_list": gr.update(choices=choices),
    }


def remove_selected_victory_point(
    selected_id: str,
    current_state: list[VictoryPointItem],
    remove_fn: Callable[[list[VictoryPointItem], str], list[VictoryPointItem]],
    get_choices_fn: Callable[[list[VictoryPointItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Remove selected victory point.

    Args:
        selected_id: ID of VP to remove
        current_state: Current VP state
        remove_fn: Function to remove selected VP
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and choices
    """
    if not selected_id:
        return {
            "vp_state": current_state,
            "vp_list": gr.update(),
        }
    new_state = remove_fn(current_state, selected_id)
    choices = get_choices_fn(new_state)
    return {
        "vp_state": new_state,
        "vp_list": gr.update(choices=choices),
    }


# =============================================================================
# Polygon preset handler
# =============================================================================
def on_polygon_preset_change(
    preset: str,
    polygon_presets: dict[str, int],
) -> list[list[float]]:
    """Generate points for polygon presets.

    Args:
        preset: Preset name (custom, triangle, pentagon, hexagon)
        polygon_presets: Dict mapping preset names to number of sides

    Returns:
        List of [x, y] coordinate pairs
    """
    if preset == "custom":
        return [[600.0, 300.0], [1000.0, 700.0], [200.0, 700.0]]

    num_sides = polygon_presets.get(preset, 3)
    center_x, center_y, radius = 600.0, 600.0, 250.0
    points: list[list[float]] = []

    for i in range(num_sides):
        angle = 2 * math.pi * i / num_sides - math.pi / 2
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append([x, y])

    return points


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
