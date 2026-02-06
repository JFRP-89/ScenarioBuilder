"""Objective points section."""

from typing import Any

import gradio as gr


def build_objective_points_section() -> tuple[Any, ...]:
    """Build objective points marker UI (max 10 points).

    Returns:
        Tuple of (objective_points_toggle, objective_points_state,
                 objective_description, objective_cx_input, objective_cy_input,
                 add_objective_btn, objective_points_list, remove_last_objective_btn,
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
                label="X Coordinate (mm)",
                value=600,  # Default to center of standard 1200x1200
                precision=0,
                elem_id="objective-cx",
            )
            objective_cy_input = gr.Number(
                label="Y Coordinate (mm)",
                value=600,  # Default to center of standard 1200x1200
                precision=0,
                elem_id="objective-cy",
            )

        # Add point button
        with gr.Row():
            add_objective_btn = gr.Button(
                "Add Objective Point",
                variant="primary",
                elem_id="add-objective-btn",
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
        objective_description,
        objective_cx_input,
        objective_cy_input,
        add_objective_btn,
        objective_points_list,
        remove_last_objective_btn,
        remove_selected_objective_btn,
        objective_points_group,
    )
