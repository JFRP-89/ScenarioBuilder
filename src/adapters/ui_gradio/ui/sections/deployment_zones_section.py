"""Deployment zones section."""

from typing import Any

import gradio as gr
from adapters.ui_gradio.ui.components import build_unit_selector


def build_deployment_zones_section() -> tuple[Any, ...]:
    """Build deployment zones UI components.

    Returns:
        Tuple of (deployment_zones_toggle, deployment_zones_state,
                 zone_table_width_state, zone_table_height_state,
                 zone_unit_state, zones_group, zone_border_select,
                 zone_fill_side_checkbox, zone_unit, zone_description,
                 zone_width, zone_height, zone_sep_x, zone_sep_y,
                 add_zone_btn, remove_last_zone_btn, deployment_zones_list,
                 remove_selected_zone_btn)
    """
    # Toggle for Deployment Zones section
    with gr.Row():
        deployment_zones_toggle = gr.Checkbox(
            label="Add Deployment Zones",
            value=False,
            elem_id="deployment-zones-toggle",
        )

    # Deployment Zones section (collapsible)
    with gr.Group(visible=False) as zones_group:
        gr.Markdown("### Deployment Zones (0-2 rectangles)")
        gr.Markdown(
            "_Define deployment zones for army placement. "
            "Max 2 zones. Select border; dimensions adapt automatically._"
        )

        deployment_zones_state = gr.State([])
        zone_table_width_state = gr.State(
            120
        )  # Track current table width for UI updates (in cm)
        zone_table_height_state = gr.State(
            120
        )  # Track current table height for UI updates (in cm)

        with gr.Row():
            zone_border_select = gr.Radio(
                choices=["north", "south", "east", "west"],
                value="north",
                label="Border",
                elem_id="zone-border-select",
            )

        with gr.Row():
            zone_fill_side_checkbox = gr.Checkbox(
                value=True,
                label="Fill Full Side (width for north/south, height for east/west)",
                elem_id="zone-fill-side",
            )

        with gr.Row():
            zone_unit_state, zone_unit = build_unit_selector("zone")

        with gr.Row():
            zone_description = gr.Textbox(
                value="",
                label="Description",
                placeholder="e.g., Attacking Army, Defending Army, Army of Gondor",
                elem_id="zone-description",
                interactive=True,
            )

        with gr.Row():
            zone_width = gr.Number(
                value=120,
                precision=2,
                label="Width (cm) [LOCKED]",
                elem_id="zone-width",
                interactive=False,
            )
            zone_height = gr.Number(
                value=20,
                precision=2,
                label="Height",
                elem_id="zone-height",
                interactive=True,
            )

        with gr.Row():
            zone_sep_x = gr.Number(
                value=0,
                precision=2,
                label="Separation X (cm) [LOCKED]",
                elem_id="zone-sep-x",
                interactive=False,
            )
            zone_sep_y = gr.Number(
                value=0,
                precision=2,
                label="Separation Y",
                elem_id="zone-sep-y",
                interactive=True,
            )

        with gr.Row():
            add_zone_btn = gr.Button("+ Add Zone", size="sm", elem_id="add-zone-btn")
            remove_last_zone_btn = gr.Button(
                "- Remove Last", size="sm", elem_id="remove-last-zone-btn"
            )

        # Zone list display
        gr.Markdown("_Current Zones:_")
        deployment_zones_list = gr.Dropdown(
            choices=[],
            value=None,
            label="Zones",
            elem_id="deployment-zones-list",
            interactive=True,
            allow_custom_value=False,
        )
        remove_selected_zone_btn = gr.Button(
            "Remove Selected", size="sm", elem_id="remove-selected-zone-btn"
        )
    return (
        deployment_zones_toggle,
        deployment_zones_state,
        zone_table_width_state,
        zone_table_height_state,
        zone_unit_state,
        zones_group,
        zone_border_select,
        zone_fill_side_checkbox,
        zone_unit,
        zone_description,
        zone_width,
        zone_height,
        zone_sep_x,
        zone_sep_y,
        add_zone_btn,
        remove_last_zone_btn,
        deployment_zones_list,
        remove_selected_zone_btn,
    )
