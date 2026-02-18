"""Parameter object grouping all widget references for deployment zones wiring.

Replaces the 39-parameter keyword-only signature of ``wire_deployment_zones``
with a single typed context object, improving readability and enabling
clean forwarding to sub-functions.

Note: This follows the same pattern as ``ScenographyCtx``
(see ``_scenography/_context.py``).  The two context objects share a
structural parallel but differ in their field sets, so no shared base
class is warranted.
"""

from __future__ import annotations

from dataclasses import dataclass

import gradio as gr


@dataclass
class DeploymentZonesCtx:
    """All Gradio widget references needed by the deployment-zones wirer."""

    # Toggle & group
    deployment_zones_toggle: gr.Checkbox
    zones_group: gr.Group

    # Section state
    deployment_zones_state: gr.State
    zone_table_width_state: gr.State
    zone_table_height_state: gr.State
    zone_unit_state: gr.State

    # Zone form — type & modifiers
    zone_type_select: gr.Radio
    border_row: gr.Row
    zone_border_select: gr.Radio
    corner_row: gr.Row
    zone_corner_select: gr.Radio
    fill_side_row: gr.Row
    zone_fill_side_checkbox: gr.Checkbox
    perfect_triangle_row: gr.Row
    zone_perfect_triangle_checkbox: gr.Checkbox
    zone_unit: gr.Radio
    zone_description: gr.Textbox

    # Dimensions — rectangle
    rect_dimensions_row: gr.Row
    zone_width: gr.Number
    zone_height: gr.Number

    # Dimensions — triangle
    triangle_dimensions_row: gr.Row
    zone_triangle_side1: gr.Number
    zone_triangle_side2: gr.Number

    # Dimensions — circle
    circle_dimensions_row: gr.Row
    zone_circle_radius: gr.Number

    # Separation
    separation_row: gr.Row
    zone_sep_x: gr.Number
    zone_sep_y: gr.Number

    # Action buttons & list
    add_zone_btn: gr.Button
    remove_last_zone_btn: gr.Button
    deployment_zones_list: gr.Dropdown
    remove_selected_zone_btn: gr.Button

    # Table context (read-only references used for coordinate math)
    table_preset: gr.Radio
    table_width: gr.Number
    table_height: gr.Number
    table_unit: gr.Radio

    # Editing state
    zone_editing_state: gr.State
    cancel_edit_zone_btn: gr.Button

    # Output
    output: gr.JSON
