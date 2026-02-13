"""UI section visibility toggle handlers."""

from __future__ import annotations

from typing import Any

import gradio as gr


# =============================================================================
# Visibility toggle handlers
# =============================================================================
def toggle_section(enabled: bool) -> dict[str, Any]:
    """Show/hide a UI section when its toggle changes.

    Args:
        enabled: Whether section is enabled

    Returns:
        Gradio update with visibility
    """
    update: dict[str, Any] = gr.update(visible=enabled)
    return update


# Aliases - wiring modules import by section-specific name.
toggle_vp_section = toggle_section
toggle_deployment_zones_section = toggle_section
toggle_scenography_section = toggle_section
toggle_objective_points_section = toggle_section
toggle_special_rules_section = toggle_section


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
