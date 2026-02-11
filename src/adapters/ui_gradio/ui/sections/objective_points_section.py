"""Objective points section."""

from typing import Any

import gradio as gr
from adapters.ui_gradio.ui.components import build_unit_selector


def build_objective_points_section() -> tuple[Any, ...]:
    """Build objective points marker UI (max 10 points).

    Returns:
        Tuple of (objective_points_toggle, objective_points_state,
                 objective_unit_state, objective_description, objective_cx_input,
                 objective_cy_input, objective_unit, add_objective_btn,
                 objective_points_list, remove_last_objective_btn,
                 remove_selected_objective_btn, objective_points_group)
    """
    # Toggle for Objective Points section
    with gr.Row():
        objective_points_toggle = gr.Checkbox(
            label="Add Objective Points",
            value=False,
            elem_id="objective-points-toggle",
        )

    # Objective Points section (collapsible)
    with gr.Group(visible=False) as objective_points_group:
        objective_points_state = gr.State([])

        gr.Markdown("### Objective Points (Markers)")
        gr.Markdown(
            "_Black circular markers for map objectives. Max 10 per board. "
            "Default position: map center._"
        )

        # Unit selector
        with gr.Row():
            objective_unit_state, objective_unit = build_unit_selector("objective")

        # Description for objective point
        with gr.Row():
            objective_description = gr.Textbox(
                value="",
                label="Description",
                placeholder="e.g., Objective A, Objective B, Relic, Treasure",
                elem_id="objective-description",
                interactive=True,
            )

        # Input fields for new point
        with gr.Row():
            objective_cx_input = gr.Number(
                label="X Coordinate",
                value=60,  # Default to center of standard 120x120 cm
                precision=2,
                elem_id="objective-cx",
            )
            objective_cy_input = gr.Number(
                label="Y Coordinate",
                value=60,  # Default to center of standard 120x120 cm
                precision=2,
                elem_id="objective-cy",
            )

        objective_editing_state = gr.State(None)

        # Add point button
        with gr.Row():
            add_objective_btn = gr.Button(
                "Add Objective Point",
                variant="primary",
                elem_id="add-objective-btn",
            )
            cancel_edit_objective_btn = gr.Button(
                "Cancel Edit",
                size="sm",
                visible=False,
                elem_id="cancel-edit-objective-btn",
            )

        # List of points
        with gr.Row():
            objective_points_list = gr.Dropdown(
                choices=[("No points", "")],
                value="",
                label="Objective Points",
                interactive=True,
                elem_id="objective-points-list",
            )

        # Remove buttons
        with gr.Row():
            remove_last_objective_btn = gr.Button(
                "Remove Last",
                elem_id="remove-last-objective-btn",
            )
            remove_selected_objective_btn = gr.Button(
                "Remove Selected",
                elem_id="remove-selected-objective-btn",
            )

    return (
        objective_points_toggle,
        objective_points_state,
        objective_unit_state,
        objective_description,
        objective_cx_input,
        objective_cy_input,
        objective_unit,
        add_objective_btn,
        objective_points_list,
        remove_last_objective_btn,
        remove_selected_objective_btn,
        objective_points_group,
        objective_editing_state,
        cancel_edit_objective_btn,
    )
