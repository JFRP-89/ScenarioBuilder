"""Scenario details section (deployment, layout, objectives, priority, victory points)."""

from typing import Any

import gradio as gr


def build_scenario_details_section() -> (
    tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]
):
    """Build scenario details UI components.

    Returns:
        Tuple of (deployment, layout, objectives, initial_priority,
                 objectives_with_vp_toggle, vp_group, vp_state, vp_input,
                 add_vp_btn, remove_vp_btn, vp_list, remove_selected_vp_btn, vp_buttons_row)
    """
    gr.Markdown("## Scenario Details")
    with gr.Row():
        deployment = gr.Textbox(
            label="Deployment",
            placeholder="e.g., Standard, Flanking",
            elem_id="deployment",
        )
        layout = gr.Textbox(
            label="Layout", placeholder="e.g., Open Field, Urban", elem_id="layout"
        )

    with gr.Row():
        objectives = gr.Textbox(
            label="Objectives",
            placeholder="e.g., Control Center, Eliminate Leader",
            elem_id="objectives",
        )
        initial_priority = gr.Textbox(
            label="Initial Priority",
            placeholder="e.g., Check the rulebook for it",
            elem_id="initial_priority",
        )

    # Victory Points section toggle
    with gr.Row():
        objectives_with_vp_toggle = gr.Checkbox(
            label="Add Victory Points Scoring",
            value=False,
            elem_id="objectives-with-vp-toggle",
        )

    # Victory points section (collapsible group)
    with gr.Group(visible=False) as vp_group:
        gr.Markdown("### Victory Points Scoring")
        gr.Markdown(
            "_Each point describes scoring conditions and victory point values._"
        )

        vp_state = gr.State([])

        with gr.Row():
            vp_input = gr.Textbox(
                label="Victory Point Description",
                placeholder="e.g., 1 point if...",
                lines=2,
                elem_id="vp-input",
                interactive=True,
            )

        with gr.Row() as vp_buttons_row:
            add_vp_btn = gr.Button(
                "+ Add Victory Point", size="sm", elem_id="add-vp-btn"
            )
            remove_vp_btn = gr.Button(
                "- Remove Last", size="sm", elem_id="remove-vp-btn"
            )

        # Victory Points list display
        gr.Markdown("_Current Victory Points:_")
        vp_list = gr.Dropdown(
            choices=[],
            value=None,
            label="Victory Points",
            elem_id="vp-list",
            interactive=True,
            allow_custom_value=False,
        )
        remove_selected_vp_btn = gr.Button(
            "Remove Selected",
            size="sm",
            elem_id="remove-selected-vp-btn",
        )

    return (
        deployment,
        layout,
        objectives,
        initial_priority,
        objectives_with_vp_toggle,
        vp_group,
        vp_state,
        vp_input,
        add_vp_btn,
        remove_vp_btn,
        vp_list,
        remove_selected_vp_btn,
        vp_buttons_row,
    )
