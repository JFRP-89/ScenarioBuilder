"""Gradio UI adapter for ScenarioBuilder.

This module contains ONLY:
- ``build_app()`` -- assembles the Gradio layout and calls ``wire_events()``
- ``__main__`` launcher

All helpers, handlers, constants and event wiring live in sibling modules.
"""

from __future__ import annotations

import os
import sys

# Add src to path if running as script (not as module)
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if sys.path and os.path.normpath(sys.path[0]) == os.path.normpath(script_dir):
        sys.path.pop(0)
    src_path = os.path.abspath(
        os.path.join(script_dir, os.pardir, os.pardir, os.pardir)
    )
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

import gradio as gr
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components import build_svg_preview
from adapters.ui_gradio.ui.sections import (
    actor_section,
    deployment_zones_section,
    objective_points_section,
    scenario_details_section,
    scenario_meta_section,
    scenography_section,
    special_rules_section,
    table_section,
    visibility_section,
)
from adapters.ui_gradio.ui.wiring import wire_events


# =============================================================================
# App builder
# =============================================================================
def build_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app.

    This function constructs the UI without making any HTTP calls.
    HTTP calls only happen when user interacts with the UI.

    Returns:
        A gradio.Blocks instance ready to launch
    """
    with gr.Blocks(title="Scenario Card Generator") as app:
        gr.Markdown("# Scenario Card Generator")

        # Actor ID
        actor_id = actor_section.build_actor_section(get_default_actor_id())

        # Scenario Name, Mode, Seed, Armies
        scenario_name, mode, seed, armies = (
            scenario_meta_section.build_scenario_meta_section()
        )

        # Visibility
        visibility, shared_with_row, shared_with = (
            visibility_section.build_visibility_section()
        )

        # Table Configuration
        (
            table_preset,
            prev_unit_state,
            custom_table_row,
            table_width,
            table_height,
            table_unit,
        ) = table_section.build_table_section()

        # Scenario Details
        (
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
            _,  # vp_buttons_row (unused)
        ) = scenario_details_section.build_scenario_details_section()

        # Special Rules Builder
        (
            special_rules_state,
            special_rules_toggle,
            rules_group,
            rule_type_radio,
            rule_name_input,
            rule_value_input,
            add_rule_btn,
            remove_rule_btn,
            rules_list,
            remove_selected_rule_btn,
            _,  # rule_name_state (unused)
            _,  # rule_value_state (unused)
        ) = special_rules_section.build_special_rules_section()

        # Deployment Zones Builder
        (
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
        ) = deployment_zones_section.build_deployment_zones_section()

        # Objective Points Builder (max 10 markers)
        (
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
        ) = objective_points_section.build_objective_points_section()

        # Scenography Builder
        (
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
        ) = scenography_section.build_scenography_section()

        # SVG Map Preview
        svg_preview = build_svg_preview(
            elem_id_prefix="card-svg-preview",
            label="Map Preview",
        )

        # Generate button and output
        generate_btn = gr.Button(
            "Generate Card", variant="primary", elem_id="generate-button"
        )
        output = gr.JSON(label="Generated Card", elem_id="result-json")

        # ── Wire all events ──────────────────────────────────────────────
        wire_events(
            actor_id=actor_id,
            scenario_name=scenario_name,
            mode=mode,
            seed=seed,
            armies=armies,
            table_preset=table_preset,
            prev_unit_state=prev_unit_state,
            custom_table_row=custom_table_row,
            table_width=table_width,
            table_height=table_height,
            table_unit=table_unit,
            deployment=deployment,
            layout=layout,
            objectives=objectives,
            initial_priority=initial_priority,
            objectives_with_vp_toggle=objectives_with_vp_toggle,
            vp_group=vp_group,
            vp_state=vp_state,
            vp_input=vp_input,
            add_vp_btn=add_vp_btn,
            remove_vp_btn=remove_vp_btn,
            vp_list=vp_list,
            remove_selected_vp_btn=remove_selected_vp_btn,
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
            visibility=visibility,
            shared_with_row=shared_with_row,
            shared_with=shared_with,
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
            generate_btn=generate_btn,
            svg_preview=svg_preview,
            output=output,
        )

    return app


# =============================================================================
# Main entry point
# =============================================================================
if __name__ == "__main__":
    build_app().launch(
        server_name=os.environ.get(
            "UI_HOST", "0.0.0.0"
        ),  # nosec B104 - container/local dev
        server_port=int(os.environ.get("UI_PORT", "7860")),
    )
