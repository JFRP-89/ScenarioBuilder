"""Create scenario page builder.

Builds the full "Create Scenario" form (actor, meta, visibility, table,
scenario details, special rules, deployment zones, objective points,
scenography, map preview, generate/create buttons).

Extracted from ``app.py`` to keep the main module under 1 000 LOC.
"""

from __future__ import annotations

from types import SimpleNamespace

import gradio as gr
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


def build_create_page(
    *,
    auth_enabled: bool = True,  # reserved for future per-section gating
) -> SimpleNamespace:
    """Build the Create Scenario page and return all components.

    Parameters
    ----------
    auth_enabled:
        Reserved for forwarding to section builders that support it.
        Currently unused (no section accepts it yet).

    Returns
    -------
    tuple
        A flat tuple of every Gradio component / state created inside the
        page, in the order listed below.  The caller unpacks them by
        position — **do not reorder**.

        Container & header
        ~~~~~~~~~~~~~~~~~~
        create_container, create_back_btn, create_heading_md

        Actor
        ~~~~~
        actor_id

        Meta
        ~~~~
        scenario_name, mode, is_replicable, generate_from_seed,
        apply_seed_btn, refill_scenario_btn, armies

        Visibility
        ~~~~~~~~~~
        visibility, shared_with_row, shared_with

        Table
        ~~~~~
        table_preset, prev_unit_state, custom_table_row,
        table_width, table_height, table_unit

        Scenario details (deployment / layout / objectives / VP)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        deployment, layout, objectives, initial_priority,
        objectives_with_vp_toggle, vp_group, vp_state, vp_input,
        add_vp_btn, remove_vp_btn, vp_list, remove_selected_vp_btn,
        vp_editing_state, cancel_edit_vp_btn

        Special rules
        ~~~~~~~~~~~~~
        special_rules_state, special_rules_toggle, rules_group,
        rule_type_radio, rule_name_input, rule_value_input,
        add_rule_btn, remove_rule_btn, rules_list,
        remove_selected_rule_btn, rule_editing_state,
        cancel_edit_rule_btn

        Deployment zones
        ~~~~~~~~~~~~~~~~
        deployment_zones_toggle, deployment_zones_state,
        zone_table_width_state, zone_table_height_state,
        zone_unit_state, zones_group, zone_type_select,
        border_row, zone_border_select, corner_row,
        zone_corner_select, fill_side_row,
        zone_fill_side_checkbox, perfect_triangle_row,
        zone_perfect_triangle_checkbox, zone_unit,
        zone_description, rect_dimensions_row, zone_width,
        zone_height, triangle_dimensions_row,
        zone_triangle_side1, zone_triangle_side2,
        circle_dimensions_row, zone_circle_radius,
        separation_row, zone_sep_x, zone_sep_y,
        add_zone_btn, remove_last_zone_btn,
        deployment_zones_list, remove_selected_zone_btn,
        zone_editing_state, cancel_edit_zone_btn

        Objective points
        ~~~~~~~~~~~~~~~~
        objective_points_toggle, objective_points_state,
        objective_unit_state, objective_description,
        objective_cx_input, objective_cy_input, objective_unit,
        add_objective_btn, objective_points_list,
        remove_last_objective_btn, remove_selected_objective_btn,
        objective_points_group, objective_editing_state,
        cancel_edit_objective_btn

        Scenography
        ~~~~~~~~~~~
        scenography_toggle, scenography_state,
        scenography_unit_state, scenography_description,
        scenography_type, scenography_unit,
        circle_form_row, circle_cx, circle_cy, circle_r,
        rect_form_row, rect_x, rect_y, rect_width, rect_height,
        polygon_form_col, polygon_preset, polygon_points,
        delete_polygon_row_btn, polygon_delete_msg,
        allow_overlap_checkbox, add_scenography_btn,
        remove_last_scenography_btn, scenography_list,
        remove_selected_scenography_btn, scenography_group,
        scenography_editing_state, cancel_edit_scenography_btn

        Bottom controls
        ~~~~~~~~~~~~~~~
        svg_preview, generate_btn, output, preview_full_state,
        create_scenario_btn, create_scenario_status
    """
    # ── suppress unused-variable warning for reserved param ──
    _ = auth_enabled

    with gr.Column(visible=False, elem_id="page-create-scenario") as create_container:
        with gr.Row():
            create_back_btn = gr.Button(
                "← Home",
                variant="secondary",
                size="sm",
                elem_id="create-back-btn",
            )
            create_heading_md = gr.Markdown(
                "## Create New Scenario",
                elem_id="create-heading",
            )

        # ── Form sections ────────────────────────────────────────
        actor_id = actor_section.build_actor_section("")

        (
            scenario_name,
            mode,
            is_replicable,
            generate_from_seed,
            apply_seed_btn,
            refill_scenario_btn,
            armies,
        ) = scenario_meta_section.build_scenario_meta_section()

        visibility, shared_with_row, shared_with = (
            visibility_section.build_visibility_section()
        )

        (
            table_preset,
            prev_unit_state,
            custom_table_row,
            table_width,
            table_height,
            table_unit,
        ) = table_section.build_table_section()

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
            _,
            vp_editing_state,
            cancel_edit_vp_btn,
        ) = scenario_details_section.build_scenario_details_section()

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
            _,
            _,
            rule_editing_state,
            cancel_edit_rule_btn,
        ) = special_rules_section.build_special_rules_section()

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
            zone_editing_state,
            cancel_edit_zone_btn,
        ) = deployment_zones_section.build_deployment_zones_section()

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
            objective_editing_state,
            cancel_edit_objective_btn,
        ) = objective_points_section.build_objective_points_section()

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
            scenography_editing_state,
            cancel_edit_scenography_btn,
        ) = scenography_section.build_scenography_section()

        svg_preview = build_svg_preview(
            elem_id_prefix="card-svg-preview",
            label="Map Preview",
        )

        generate_btn = gr.Button(
            "Generate Card",
            variant="primary",
            elem_id="generate-button",
        )
        output = gr.JSON(label="Generated Card", elem_id="result-json")
        # Hidden state to store full preview data (with _payload and _actor_id)
        # Needed for submission, but filtered from JSON display
        preview_full_state = gr.State(value=None)

        create_scenario_btn = gr.Button(
            "Create Scenario",
            variant="primary",
            elem_id="create-scenario-button",
        )
        create_scenario_status = gr.Textbox(
            label="",
            elem_id="create-scenario-status",
            interactive=False,
            visible=False,
        )

    # ── Return every component the caller needs ──────────────────
    return SimpleNamespace(
        # Container & header
        container=create_container,
        back_btn=create_back_btn,
        create_heading_md=create_heading_md,
        # Actor
        actor_id=actor_id,
        # Meta
        scenario_name=scenario_name,
        mode=mode,
        is_replicable=is_replicable,
        generate_from_seed=generate_from_seed,
        apply_seed_btn=apply_seed_btn,
        refill_scenario_btn=refill_scenario_btn,
        armies=armies,
        # Visibility
        visibility=visibility,
        shared_with_row=shared_with_row,
        shared_with=shared_with,
        # Table
        table_preset=table_preset,
        prev_unit_state=prev_unit_state,
        custom_table_row=custom_table_row,
        table_width=table_width,
        table_height=table_height,
        table_unit=table_unit,
        # Scenario details
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
        vp_editing_state=vp_editing_state,
        cancel_edit_vp_btn=cancel_edit_vp_btn,
        # Special rules
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
        rule_editing_state=rule_editing_state,
        cancel_edit_rule_btn=cancel_edit_rule_btn,
        # Deployment zones
        deployment_zones_toggle=deployment_zones_toggle,
        deployment_zones_state=deployment_zones_state,
        zone_table_width_state=zone_table_width_state,
        zone_table_height_state=zone_table_height_state,
        zone_unit_state=zone_unit_state,
        zones_group=zones_group,
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
        zone_editing_state=zone_editing_state,
        cancel_edit_zone_btn=cancel_edit_zone_btn,
        # Objective points
        objective_points_toggle=objective_points_toggle,
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
        objective_points_group=objective_points_group,
        objective_editing_state=objective_editing_state,
        cancel_edit_objective_btn=cancel_edit_objective_btn,
        # Scenography
        scenography_toggle=scenography_toggle,
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
        scenography_group=scenography_group,
        scenography_editing_state=scenography_editing_state,
        cancel_edit_scenography_btn=cancel_edit_scenography_btn,
        # Bottom controls
        svg_preview=svg_preview,
        generate_btn=generate_btn,
        output=output,
        preview_full_state=preview_full_state,
        create_scenario_btn=create_scenario_btn,
        create_scenario_status=create_scenario_status,
    )
