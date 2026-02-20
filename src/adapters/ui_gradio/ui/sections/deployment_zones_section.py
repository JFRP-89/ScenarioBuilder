"""Deployment zones section."""

from typing import Any

import gradio as gr
from adapters.ui_gradio.ui.components import build_unit_selector


def build_deployment_zones_section() -> tuple[Any, ...]:
    """Build deployment zones UI components.

    Returns:
        Tuple of (deployment_zones_toggle, deployment_zones_state,
                 zone_table_width_state, zone_table_height_state,
                 zone_unit_state, zones_group, zone_type_select,
                 border_row, zone_border_select, corner_row, zone_corner_select,
                 fill_side_row, zone_fill_side_checkbox,
                 perfect_triangle_row, zone_perfect_triangle_checkbox,
                 zone_unit, zone_description,
                 rect_dimensions_row, zone_width, zone_height,
                 triangle_dimensions_row, zone_triangle_side1, zone_triangle_side2,
                 circle_dimensions_row, zone_circle_radius,
                 separation_row, zone_sep_x, zone_sep_y,
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
        gr.Markdown("### Deployment Zones")
        gr.Markdown(
            "_Define deployment zones for army placement. Choose type and location._"
        )

        deployment_zones_state = gr.State([])
        zone_table_width_state = gr.State(
            120
        )  # Track current table width for UI updates (in cm)
        zone_table_height_state = gr.State(
            120
        )  # Track current table height for UI updates (in cm)

        # Zone Type Selection
        with gr.Row():
            zone_type_select = gr.Radio(
                choices=["rectangle", "triangle", "circle"],
                value="rectangle",
                label="Zone Type",
                elem_id="zone-type-select",
            )

        # Border selection (for rectangles)
        with gr.Row(visible=True) as border_row:
            zone_border_select = gr.Radio(
                choices=["north", "south", "east", "west"],
                value="north",
                label="Border",
                elem_id="zone-border-select",
            )

        # Corner selection (for triangles)
        with gr.Row(visible=False) as corner_row:
            zone_corner_select = gr.Radio(
                choices=["north-west", "north-east", "south-west", "south-east"],
                value="north-west",
                label="Corner",
                elem_id="zone-corner-select",
            )

        # Fill Full Side checkbox (rectangles only)
        with gr.Row(visible=True) as fill_side_row:
            zone_fill_side_checkbox = gr.Checkbox(
                value=True,
                label="Fill Full Side (width for north/south, height for east/west)",
                elem_id="zone-fill-side",
            )

        # Perfect Triangle checkbox (triangles only)
        with gr.Row(visible=False) as perfect_triangle_row:
            zone_perfect_triangle_checkbox = gr.Checkbox(
                value=True,
                label="Perfect Isosceles Triangle (equal sides)",
                elem_id="zone-perfect-triangle",
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

        # Rectangle dimensions (visible for rectangles)
        with gr.Row(visible=True) as rect_dimensions_row:
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

        # Triangle dimensions (visible for triangles)
        with gr.Row(visible=False) as triangle_dimensions_row:
            zone_triangle_side1 = gr.Number(
                value=30,
                precision=2,
                label="X (cm)",
                elem_id="zone-triangle-side1",
                interactive=True,
            )
            zone_triangle_side2 = gr.Number(
                value=30,
                precision=2,
                label="Y (cm) [LOCKED]",
                elem_id="zone-triangle-side2",
                interactive=False,
            )

        # Circle dimensions (visible for circles)
        with gr.Row(visible=False) as circle_dimensions_row:
            zone_circle_radius = gr.Number(
                value=30,
                precision=2,
                label="Radius (cm)",
                elem_id="zone-circle-radius",
                interactive=True,
            )

        # Separation coordinates (only for rectangles)
        with gr.Row(visible=True) as separation_row:
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

        zone_editing_state = gr.State(None)

        with gr.Row():
            add_zone_btn = gr.Button("+ Add Zone", size="sm", elem_id="add-zone-btn")
            cancel_edit_zone_btn = gr.Button(
                "Cancel Edit",
                size="sm",
                visible=False,
                elem_id="cancel-edit-zone-btn",
            )
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
        zone_type_select,
        border_row,
        zone_border_select,
        corner_row,
        zone_corner_select,
        fill_side_row,
        zone_fill_side_checkbox,
        perfect_triangle_row,
        zone_perfect_triangle_checkbox,
        zone_unit,
        zone_description,
        rect_dimensions_row,
        zone_width,
        zone_height,
        triangle_dimensions_row,
        zone_triangle_side1,
        zone_triangle_side2,
        circle_dimensions_row,
        zone_circle_radius,
        separation_row,
        zone_sep_x,
        zone_sep_y,
        add_zone_btn,
        remove_last_zone_btn,
        deployment_zones_list,
        remove_selected_zone_btn,
        zone_editing_state,
        cancel_edit_zone_btn,
    )
