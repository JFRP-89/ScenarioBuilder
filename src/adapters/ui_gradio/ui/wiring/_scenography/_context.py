"""Parameter object grouping all widget references for scenography wiring.

Replaces the 32-parameter keyword-only signature of ``wire_scenography``
with a single typed context object, improving readability and enabling
clean forwarding to sub-functions.

Note: This follows the same pattern as ``DeploymentZonesCtx``
(see ``_deployment/_context.py``).  The two context objects share a
structural parallel but differ in their field sets, so no shared base
class is warranted.
"""

from __future__ import annotations

from dataclasses import dataclass

import gradio as gr


@dataclass
class ScenographyCtx:
    """All Gradio widget references needed by the scenography wirer."""

    # Toggle & group
    scenography_toggle: gr.Checkbox
    scenography_group: gr.Group

    # Section state
    scenography_state: gr.State

    # Form — description & type
    scenography_description: gr.Textbox
    scenography_type: gr.Radio

    # Form — circle
    circle_form_row: gr.Row
    circle_cx: gr.Number
    circle_cy: gr.Number
    circle_r: gr.Number

    # Form — rectangle
    rect_form_row: gr.Row
    rect_x: gr.Number
    rect_y: gr.Number
    rect_width: gr.Number
    rect_height: gr.Number

    # Form — polygon
    polygon_form_col: gr.Column
    polygon_preset: gr.Dropdown
    polygon_points: gr.Dataframe
    delete_polygon_row_btn: gr.Button
    polygon_delete_msg: gr.Textbox

    # Overlap
    allow_overlap_checkbox: gr.Checkbox

    # Action buttons & list
    add_scenography_btn: gr.Button
    remove_last_scenography_btn: gr.Button
    scenography_list: gr.Dropdown
    remove_selected_scenography_btn: gr.Button

    # Table context (read-only references used for coordinate math)
    table_width: gr.Number
    table_height: gr.Number
    table_unit: gr.Radio

    # Unit state
    scenography_unit_state: gr.State
    scenography_unit: gr.Radio

    # Editing state
    scenography_editing_state: gr.State
    cancel_edit_scenography_btn: gr.Button

    # Output
    output: gr.JSON
