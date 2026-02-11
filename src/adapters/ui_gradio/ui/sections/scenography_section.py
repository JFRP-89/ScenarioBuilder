"""Scenography section."""

from typing import Any

import gradio as gr
from adapters.ui_gradio.ui.components import build_unit_selector

# Scenography types
SCENOGRAPHY_TYPES = ["circle", "rect", "polygon"]


def build_scenography_section() -> tuple[Any, ...]:
    """Build scenography builder UI components (starts empty).

    Returns:
        Tuple of (scenography_toggle, scenography_state, scenography_unit_state,
                 scenography_description, scenography_type, scenography_unit,
                 circle_form_row, circle_cx, circle_cy, circle_r, rect_form_row,
                 rect_x, rect_y, rect_width, rect_height, polygon_form_col,
                 polygon_preset, polygon_points, delete_polygon_row_btn,
                 polygon_delete_msg, allow_overlap_checkbox, add_scenography_btn,
                 remove_last_scenography_btn, scenography_list,
                 remove_selected_scenography_btn, scenography_group)
    """
    # Toggle for Scenography section
    with gr.Row():
        scenography_toggle = gr.Checkbox(
            label="Add Scenography",
            value=False,
            elem_id="scenography-toggle",
        )

    # Scenography section (collapsible)
    with gr.Group(visible=False) as scenography_group:
        gr.Markdown("### Scenography (Map Specs)")
        gr.Markdown(
            "_Add terrain elements (circles, rectangles, polygons). "
            "By default, elements cannot overlap._"
        )

        scenography_state = gr.State([])

        # Description for scenography element
        with gr.Row():
            scenography_description = gr.Textbox(
                value="",
                label="Description",
                placeholder="e.g., Forest, Village, River, Ruins",
                elem_id="scenography-description",
                interactive=True,
            )

        # Unit selector
        with gr.Row():
            scenography_unit_state, scenography_unit = build_unit_selector(
                "scenography"
            )

        # Element type selector
        with gr.Row():
            scenography_type = gr.Radio(
                choices=SCENOGRAPHY_TYPES,
                value="circle",
                label="Element Type",
                elem_id="scenography-type",
            )

        # Circle form (visible by default now)
        with gr.Row(visible=True) as circle_form_row:
            circle_cx = gr.Number(
                value=90, precision=2, label="Center X", elem_id="circle-cx"
            )
            circle_cy = gr.Number(
                value=90, precision=2, label="Center Y", elem_id="circle-cy"
            )
            circle_r = gr.Number(
                value=15, precision=2, label="Radius", elem_id="circle-r"
            )

        # Rectangle form (hidden by default)
        with gr.Row(visible=False) as rect_form_row:
            rect_x = gr.Number(value=30, precision=2, label="X", elem_id="rect-x")
            rect_y = gr.Number(value=30, precision=2, label="Y", elem_id="rect-y")
            rect_width = gr.Number(
                value=40, precision=2, label="Width", elem_id="rect-width"
            )
            rect_height = gr.Number(
                value=30, precision=2, label="Height", elem_id="rect-height"
            )

        # Polygon form (hidden by default)
        with gr.Column(visible=False) as polygon_form_col:
            with gr.Row():
                polygon_preset = gr.Dropdown(
                    choices=["custom", "triangle", "pentagon", "hexagon"],
                    value="triangle",
                    label="Polygon Preset",
                    elem_id="polygon-preset",
                )
            gr.Markdown(
                "_Points are auto-generated for presets. For custom, edit the "
                "table below. Min: 3 points, Max: 200._"
            )
            polygon_points = gr.Dataframe(
                headers=["x", "y"],
                datatype=["number", "number"],
                value=[[60, 30], [100, 70], [20, 70]],
                label="Polygon Points",
                elem_id="polygon-points",
                interactive=True,
                col_count=(2, "fixed"),
            )

            with gr.Row():
                delete_polygon_row_btn = gr.Button(
                    "🗑️ Delete Last Row",
                    size="sm",
                    elem_id="delete-polygon-row-btn",
                )
                polygon_delete_msg = gr.Textbox(
                    label="Status",
                    interactive=False,
                    value="",
                    elem_id="polygon-delete-msg",
                    max_lines=1,
                )

        with gr.Row():
            allow_overlap_checkbox = gr.Checkbox(
                value=False,
                label="Allow Overlap",
                elem_id="allow-overlap",
            )

        scenography_editing_state = gr.State(None)

        with gr.Row():
            add_scenography_btn = gr.Button(
                "+ Add Element", size="sm", elem_id="add-scenography-btn"
            )
            cancel_edit_scenography_btn = gr.Button(
                "Cancel Edit",
                size="sm",
                visible=False,
                elem_id="cancel-edit-scenography-btn",
            )
            remove_last_scenography_btn = gr.Button(
                "- Remove Last", size="sm", elem_id="remove-last-scenography-btn"
            )

        # Scenography list display
        gr.Markdown("_Current Elements:_")
        scenography_list = gr.Dropdown(
            choices=[],
            value=None,
            label="Scenography Elements",
            elem_id="scenography-list",
            interactive=True,
            allow_custom_value=False,
        )
        remove_selected_scenography_btn = gr.Button(
            "Remove Selected", size="sm", elem_id="remove-selected-scenography-btn"
        )

    return (
        scenography_toggle,
        scenography_state,
        scenography_unit_state,
        scenography_description,
        scenography_type,
        scenography_unit,
        circle_form_row,
        circle_cx,
        circle_cy,
        circle_r,
        rect_form_row,
        rect_x,
        rect_y,
        rect_width,
        rect_height,
        polygon_form_col,
        polygon_preset,
        polygon_points,
        delete_polygon_row_btn,
        polygon_delete_msg,
        allow_overlap_checkbox,
        add_scenography_btn,
        remove_last_scenography_btn,
        scenography_list,
        remove_selected_scenography_btn,
        scenography_group,
        scenography_editing_state,
        cancel_edit_scenography_btn,
    )
