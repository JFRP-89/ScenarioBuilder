"""Victory points and polygon preset handlers."""

from __future__ import annotations

import math
from typing import Any, Callable

import gradio as gr
from adapters.ui_gradio.ui_types import VictoryPointItem


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
