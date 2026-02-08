"""Central event wiring for the Gradio UI.

This package delegates to per-section wiring modules.  The public API
consists of:

* ``wire_events(**components)`` - hooks up every ``.click`` / ``.change``
  binding by dispatching to the section-level ``wire_*`` functions.
* ``_on_table_preset_change`` / ``_on_table_unit_change`` - thin adapters
  re-exported for backward-compatible test imports via ``app.py`` shims.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.ui.wiring.wire_deployment_zones import wire_deployment_zones
from adapters.ui_gradio.ui.wiring.wire_generate import wire_generate
from adapters.ui_gradio.ui.wiring.wire_objectives import wire_objectives
from adapters.ui_gradio.ui.wiring.wire_scenography import wire_scenography
from adapters.ui_gradio.ui.wiring.wire_special_rules import wire_special_rules
from adapters.ui_gradio.ui.wiring.wire_table import (
    _on_table_preset_change,
    _on_table_unit_change,
    wire_table,
)
from adapters.ui_gradio.ui.wiring.wire_victory_points import wire_victory_points
from adapters.ui_gradio.ui.wiring.wire_visibility import wire_visibility

__all__ = [
    "_on_table_preset_change",
    "_on_table_unit_change",
    "wire_events",
]


def wire_events(
    *,
    # Actor / meta
    actor_id: gr.Textbox,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    seed: gr.Number,
    armies: gr.Textbox,
    # Table
    table_preset: gr.Radio,
    prev_unit_state: gr.State,
    custom_table_row: gr.Row,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    # Scenario details
    deployment: gr.Textbox,
    layout: gr.Textbox,
    objectives: gr.Textbox,
    initial_priority: gr.Textbox,
    objectives_with_vp_toggle: gr.Checkbox,
    vp_group: gr.Group,
    vp_state: gr.State,
    vp_input: gr.Textbox,
    add_vp_btn: gr.Button,
    remove_vp_btn: gr.Button,
    vp_list: gr.Dropdown,
    remove_selected_vp_btn: gr.Button,
    # Special rules
    special_rules_state: gr.State,
    special_rules_toggle: gr.Checkbox,
    rules_group: gr.Group,
    rule_type_radio: gr.Radio,
    rule_name_input: gr.Textbox,
    rule_value_input: gr.Textbox,
    add_rule_btn: gr.Button,
    remove_rule_btn: gr.Button,
    rules_list: gr.Dropdown,
    remove_selected_rule_btn: gr.Button,
    # Visibility
    visibility: gr.Radio,
    shared_with_row: gr.Row,
    shared_with: gr.Textbox,
    # Deployment zones
    deployment_zones_toggle: gr.Checkbox,
    zones_group: gr.Group,
    deployment_zones_state: gr.State,
    zone_table_width_state: gr.State,
    zone_table_height_state: gr.State,
    zone_unit_state: gr.State,
    zone_type_select: gr.Radio,
    border_row: gr.Row,
    zone_border_select: gr.Radio,
    corner_row: gr.Row,
    zone_corner_select: gr.Radio,
    fill_side_row: gr.Row,
    zone_fill_side_checkbox: gr.Checkbox,
    perfect_triangle_row: gr.Row,
    zone_perfect_triangle_checkbox: gr.Checkbox,
    zone_unit: gr.Radio,
    zone_description: gr.Textbox,
    rect_dimensions_row: gr.Row,
    zone_width: gr.Number,
    zone_height: gr.Number,
    triangle_dimensions_row: gr.Row,
    zone_triangle_side1: gr.Number,
    zone_triangle_side2: gr.Number,
    circle_dimensions_row: gr.Row,
    zone_circle_radius: gr.Number,
    separation_row: gr.Row,
    zone_sep_x: gr.Number,
    zone_sep_y: gr.Number,
    add_zone_btn: gr.Button,
    remove_last_zone_btn: gr.Button,
    deployment_zones_list: gr.Dropdown,
    remove_selected_zone_btn: gr.Button,
    # Objective points
    objective_points_toggle: gr.Checkbox,
    objective_points_group: gr.Group,
    objective_points_state: gr.State,
    objective_unit_state: gr.State,
    objective_description: gr.Textbox,
    objective_cx_input: gr.Number,
    objective_cy_input: gr.Number,
    objective_unit: gr.Radio,
    add_objective_btn: gr.Button,
    objective_points_list: gr.Dropdown,
    remove_last_objective_btn: gr.Button,
    remove_selected_objective_btn: gr.Button,
    # Scenography
    scenography_toggle: gr.Checkbox,
    scenography_group: gr.Group,
    scenography_state: gr.State,
    scenography_unit_state: gr.State,
    scenography_description: gr.Textbox,
    scenography_type: gr.Radio,
    scenography_unit: gr.Radio,
    circle_form_row: gr.Row,
    circle_cx: gr.Number,
    circle_cy: gr.Number,
    circle_r: gr.Number,
    rect_form_row: gr.Row,
    rect_x: gr.Number,
    rect_y: gr.Number,
    rect_width: gr.Number,
    rect_height: gr.Number,
    polygon_form_col: gr.Column,
    polygon_preset: gr.Dropdown,
    polygon_points: gr.Dataframe,
    delete_polygon_row_btn: gr.Button,
    polygon_delete_msg: gr.Textbox,
    allow_overlap_checkbox: gr.Checkbox,
    add_scenography_btn: gr.Button,
    remove_last_scenography_btn: gr.Button,
    scenography_list: gr.Dropdown,
    remove_selected_scenography_btn: gr.Button,
    # Generate
    generate_btn: gr.Button,
    svg_preview: gr.HTML,
    output: gr.JSON,
) -> None:
    """Hook every UI event to its handler by dispatching to section wirers."""

    wire_table(
        table_preset=table_preset,
        prev_unit_state=prev_unit_state,
        custom_table_row=custom_table_row,
        table_width=table_width,
        table_height=table_height,
        table_unit=table_unit,
        objective_cx_input=objective_cx_input,
        objective_cy_input=objective_cy_input,
    )

    wire_special_rules(
        special_rules_state=special_rules_state,
        special_rules_toggle=special_rules_toggle,
        rules_group=rules_group,
        rule_type_radio=rule_type_radio,
        rule_name_input=rule_name_input,
        rule_value_input=rule_value_input,
        add_rule_btn=add_rule_btn,
        remove_rule_btn=remove_rule_btn,
        rules_list=rules_list,
        remove_selected_rule_btn=remove_selected_rule_btn,
        output=output,
    )

    wire_victory_points(
        objectives_with_vp_toggle=objectives_with_vp_toggle,
        vp_group=vp_group,
        vp_state=vp_state,
        vp_input=vp_input,
        add_vp_btn=add_vp_btn,
        remove_vp_btn=remove_vp_btn,
        vp_list=vp_list,
        remove_selected_vp_btn=remove_selected_vp_btn,
    )

    wire_scenography(
        scenography_toggle=scenography_toggle,
        scenography_group=scenography_group,
        scenography_state=scenography_state,
        scenography_unit_state=scenography_unit_state,
        scenography_description=scenography_description,
        scenography_type=scenography_type,
        scenography_unit=scenography_unit,
        circle_form_row=circle_form_row,
        circle_cx=circle_cx,
        circle_cy=circle_cy,
        circle_r=circle_r,
        rect_form_row=rect_form_row,
        rect_x=rect_x,
        rect_y=rect_y,
        rect_width=rect_width,
        rect_height=rect_height,
        polygon_form_col=polygon_form_col,
        polygon_preset=polygon_preset,
        polygon_points=polygon_points,
        delete_polygon_row_btn=delete_polygon_row_btn,
        polygon_delete_msg=polygon_delete_msg,
        allow_overlap_checkbox=allow_overlap_checkbox,
        add_scenography_btn=add_scenography_btn,
        remove_last_scenography_btn=remove_last_scenography_btn,
        scenography_list=scenography_list,
        remove_selected_scenography_btn=remove_selected_scenography_btn,
        table_width=table_width,
        table_height=table_height,
        table_unit=table_unit,
        output=output,
    )

    wire_deployment_zones(
        deployment_zones_toggle=deployment_zones_toggle,
        zones_group=zones_group,
        deployment_zones_state=deployment_zones_state,
        zone_table_width_state=zone_table_width_state,
        zone_table_height_state=zone_table_height_state,
        zone_unit_state=zone_unit_state,
        zone_type_select=zone_type_select,
        border_row=border_row,
        zone_border_select=zone_border_select,
        corner_row=corner_row,
        zone_corner_select=zone_corner_select,
        fill_side_row=fill_side_row,
        zone_fill_side_checkbox=zone_fill_side_checkbox,
        perfect_triangle_row=perfect_triangle_row,
        zone_perfect_triangle_checkbox=zone_perfect_triangle_checkbox,
        zone_unit=zone_unit,
        zone_description=zone_description,
        rect_dimensions_row=rect_dimensions_row,
        zone_width=zone_width,
        zone_height=zone_height,
        triangle_dimensions_row=triangle_dimensions_row,
        zone_triangle_side1=zone_triangle_side1,
        zone_triangle_side2=zone_triangle_side2,
        circle_dimensions_row=circle_dimensions_row,
        zone_circle_radius=zone_circle_radius,
        separation_row=separation_row,
        zone_sep_x=zone_sep_x,
        zone_sep_y=zone_sep_y,
        add_zone_btn=add_zone_btn,
        remove_last_zone_btn=remove_last_zone_btn,
        deployment_zones_list=deployment_zones_list,
        remove_selected_zone_btn=remove_selected_zone_btn,
        table_preset=table_preset,
        table_width=table_width,
        table_height=table_height,
        table_unit=table_unit,
        output=output,
    )

    wire_objectives(
        objective_points_toggle=objective_points_toggle,
        objective_points_group=objective_points_group,
        objective_points_state=objective_points_state,
        objective_unit_state=objective_unit_state,
        objective_description=objective_description,
        objective_cx_input=objective_cx_input,
        objective_cy_input=objective_cy_input,
        objective_unit=objective_unit,
        add_objective_btn=add_objective_btn,
        objective_points_list=objective_points_list,
        remove_last_objective_btn=remove_last_objective_btn,
        remove_selected_objective_btn=remove_selected_objective_btn,
        table_width=table_width,
        table_height=table_height,
        table_unit=table_unit,
        output=output,
    )

    wire_visibility(
        visibility=visibility,
        shared_with_row=shared_with_row,
    )

    wire_generate(
        actor_id=actor_id,
        scenario_name=scenario_name,
        mode=mode,
        seed=seed,
        armies=armies,
        table_preset=table_preset,
        table_width=table_width,
        table_height=table_height,
        table_unit=table_unit,
        deployment=deployment,
        layout=layout,
        objectives=objectives,
        initial_priority=initial_priority,
        special_rules_state=special_rules_state,
        visibility=visibility,
        shared_with=shared_with,
        scenography_state=scenography_state,
        deployment_zones_state=deployment_zones_state,
        objective_points_state=objective_points_state,
        objectives_with_vp_toggle=objectives_with_vp_toggle,
        vp_state=vp_state,
        generate_btn=generate_btn,
        svg_preview=svg_preview,
        output=output,
    )
