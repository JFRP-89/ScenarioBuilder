"""Gradio UI adapter for ScenarioBuilder.

This module contains ONLY:
- ``build_app()`` -- assembles the multi-page Gradio layout
- ``__main__`` launcher

Pages are built in ``ui/pages/``, wiring in ``ui/wiring/``.
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
from adapters.ui_gradio.ui.components import build_svg_preview, configure_renderer
from adapters.ui_gradio.ui.pages.edit_scenario import build_edit_page
from adapters.ui_gradio.ui.pages.favorites import build_favorites_page
from adapters.ui_gradio.ui.pages.home import build_home_page
from adapters.ui_gradio.ui.pages.list_scenarios import build_list_page
from adapters.ui_gradio.ui.pages.scenario_detail import build_detail_page
from adapters.ui_gradio.ui.router import (
    build_detail_card_id_state,
    build_page_state,
    build_previous_page_state,
)
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
from adapters.ui_gradio.ui.wiring.wire_detail import wire_detail_page
from adapters.ui_gradio.ui.wiring.wire_fav_toggle import wire_fav_toggle
from adapters.ui_gradio.ui.wiring.wire_favorites import wire_favorites_page
from adapters.ui_gradio.ui.wiring.wire_home import wire_home_page
from adapters.ui_gradio.ui.wiring.wire_list import wire_list_page
from adapters.ui_gradio.ui.wiring.wire_navigation import wire_navigation
from adapters.ui_gradio.ui.wiring.wire_view import wire_view_navigation


# =============================================================================
# App builder
# =============================================================================
def build_app() -> gr.Blocks:
    """Build and return the multi-page Gradio Blocks app.

    Pages: Home, List Scenarios, Scenario Detail, Create Scenario,
           Edit Scenario, Favorites.

    Navigation uses gr.State to track the current page and show/hide
    gr.Column containers.

    Returns:
        A gradio.Blocks instance ready to launch
    """
    with gr.Blocks(title="Scenario Card Generator") as app:
        # ── Inject infrastructure renderer (composition root) ────────
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        configure_renderer(SvgMapRenderer().render)

        # ── Global state ─────────────────────────────────────────────
        page_state = build_page_state()
        detail_card_id_state = build_detail_card_id_state()
        previous_page_state = build_previous_page_state()
        editing_card_id = gr.State(value="")

        # ════════════════════════════════════════════════════════════
        # PAGE 1: Home (visible by default)
        # ════════════════════════════════════════════════════════════
        (
            home_container,
            home_create_btn,
            home_browse_btn,
            home_favorites_btn,
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_search_box,
            home_per_page_dropdown,
            home_reload_btn,
            home_recent_html,
            home_prev_btn,
            home_page_info,
            home_next_btn,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ) = build_home_page()

        # ════════════════════════════════════════════════════════════
        # PAGE 2: List Scenarios
        # ════════════════════════════════════════════════════════════
        (
            list_container,
            list_filter,
            list_unit_selector,
            list_search_box,
            list_per_page_dropdown,
            list_reload_btn,
            list_cards_html,
            list_back_btn,
            list_page_info,
            list_prev_btn,
            list_next_btn,
            list_cards_cache_state,
            list_fav_ids_cache_state,
            list_loaded_state,
            list_page_state,
        ) = build_list_page()

        # ════════════════════════════════════════════════════════════
        # PAGE 3: Scenario Detail
        # ════════════════════════════════════════════════════════════
        (
            detail_container,
            detail_title_md,
            detail_svg_preview,
            detail_content_html,
            detail_edit_btn,
            detail_delete_btn,
            detail_delete_confirm_row,
            detail_delete_confirm_msg,
            detail_delete_confirm_btn,
            detail_delete_cancel_btn,
            detail_favorite_btn,
            detail_back_btn,
        ) = build_detail_page()

        # ════════════════════════════════════════════════════════════
        # PAGE 4: Create Scenario (wraps the existing form)
        # ════════════════════════════════════════════════════════════
        with gr.Column(
            visible=False, elem_id="page-create-scenario"
        ) as create_container:
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

            # ── Existing form sections (unchanged) ───────────────
            actor_id = actor_section.build_actor_section(get_default_actor_id())

            scenario_name, mode, seed, armies = (
                scenario_meta_section.build_scenario_meta_section()
            )

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

        # ════════════════════════════════════════════════════════════
        # PAGE 5: Edit Scenario
        # ════════════════════════════════════════════════════════════
        (
            edit_container,
            edit_title_md,
            edit_svg_preview,
            edit_card_json,
            edit_back_btn,
        ) = build_edit_page()

        # ════════════════════════════════════════════════════════════
        # PAGE 6: Favorites
        # ════════════════════════════════════════════════════════════
        (
            favorites_container,
            favorites_unit_selector,
            favorites_search_box,
            favorites_per_page_dropdown,
            favorites_reload_btn,
            favorites_cards_html,
            favorites_back_btn,
            favorites_page_info,
            favorites_prev_btn,
            favorites_next_btn,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
            favorites_loaded_state,
            favorites_page_state,
        ) = build_favorites_page()

        # ── Collect page containers (order must match ALL_PAGES) ──
        page_containers = [
            home_container,  # PAGE_HOME
            list_container,  # PAGE_LIST
            detail_container,  # PAGE_DETAIL
            create_container,  # PAGE_CREATE
            edit_container,  # PAGE_EDIT
            favorites_container,  # PAGE_FAVORITES
        ]

        # ── Global hidden components for favorite toggle via JS ──
        fav_toggle_card_id = gr.Textbox(
            value="",
            visible=False,
            elem_id="fav-toggle-card-id",
        )
        fav_toggle_btn = gr.Button(
            "toggle",
            visible=False,
            elem_id="fav-toggle-btn",
        )

        # ── Global hidden components for View button via JS ──
        view_card_id = gr.Textbox(
            value="",
            visible=False,
            elem_id="view-card-id",
        )
        view_card_btn = gr.Button(
            "view",
            visible=False,
            elem_id="view-card-btn",
        )

        # ── Wire navigation ──────────────────────────────────────
        wire_navigation(
            page_state=page_state,
            previous_page_state=previous_page_state,
            page_containers=page_containers,
            home_create_btn=home_create_btn,
            home_browse_btn=home_browse_btn,
            home_favorites_btn=home_favorites_btn,
            list_back_btn=list_back_btn,
            detail_back_btn=detail_back_btn,
            create_back_btn=create_back_btn,
            edit_back_btn=edit_back_btn,
            favorites_back_btn=favorites_back_btn,
        )

        # ── Wire home page (initial load) ────────────────────────
        wire_home_page(
            home_recent_html=home_recent_html,
            home_mode_filter=home_mode_filter,
            home_preset_filter=home_preset_filter,
            home_unit_selector=home_unit_selector,
            home_search_box=home_search_box,
            home_per_page_dropdown=home_per_page_dropdown,
            home_reload_btn=home_reload_btn,
            home_prev_btn=home_prev_btn,
            home_page_info=home_page_info,
            home_next_btn=home_next_btn,
            home_page_state=home_page_state,
            home_cards_cache_state=home_cards_cache_state,
            home_fav_ids_cache_state=home_fav_ids_cache_state,
            app=app,
        )

        # ── Wire list page (filter + load) ───────────────────────
        wire_list_page(
            page_state=page_state,
            page_containers=page_containers,
            list_filter=list_filter,
            list_unit_selector=list_unit_selector,
            list_search_box=list_search_box,
            list_per_page_dropdown=list_per_page_dropdown,
            list_reload_btn=list_reload_btn,
            list_cards_html=list_cards_html,
            list_page_info=list_page_info,
            list_prev_btn=list_prev_btn,
            list_next_btn=list_next_btn,
            list_page_state=list_page_state,
            home_browse_btn=home_browse_btn,
            list_cards_cache_state=list_cards_cache_state,
            list_fav_ids_cache_state=list_fav_ids_cache_state,
            list_loaded_state=list_loaded_state,
        )

        # ── Wire detail page (load card, fav, edit, delete) ─────
        wire_detail_page(
            page_state=page_state,
            page_containers=page_containers,
            previous_page_state=previous_page_state,
            detail_card_id_state=detail_card_id_state,
            detail_title_md=detail_title_md,
            detail_svg_preview=detail_svg_preview,
            detail_content_html=detail_content_html,
            detail_edit_btn=detail_edit_btn,
            detail_delete_btn=detail_delete_btn,
            detail_delete_confirm_row=detail_delete_confirm_row,
            detail_delete_confirm_btn=detail_delete_confirm_btn,
            detail_delete_cancel_btn=detail_delete_cancel_btn,
            detail_favorite_btn=detail_favorite_btn,
            edit_title_md=edit_title_md,
            edit_svg_preview=edit_svg_preview,
            edit_card_json=edit_card_json,
            # Form fields for populate-on-edit
            editing_card_id=editing_card_id,
            create_heading_md=create_heading_md,
            scenario_name=scenario_name,
            mode=mode,
            seed=seed,
            armies=armies,
            table_preset=table_preset,
            deployment=deployment,
            layout=layout,
            objectives=objectives,
            initial_priority=initial_priority,
            objectives_with_vp_toggle=objectives_with_vp_toggle,
            vp_state=vp_state,
            visibility=visibility,
            shared_with=shared_with,
            special_rules_state=special_rules_state,
            scenography_state=scenography_state,
            deployment_zones_state=deployment_zones_state,
            objective_points_state=objective_points_state,
            svg_preview=svg_preview,
            output=output,
            # Dropdowns, toggles, groups for shape sections
            deployment_zones_list=deployment_zones_list,
            deployment_zones_toggle=deployment_zones_toggle,
            zones_group=zones_group,
            objective_points_list=objective_points_list,
            objective_points_toggle=objective_points_toggle,
            objective_points_group=objective_points_group,
            scenography_list=scenography_list,
            scenography_toggle=scenography_toggle,
            scenography_group=scenography_group,
            # Dropdowns, toggles, groups for VP / special rules
            vp_list=vp_list,
            vp_group=vp_group,
            rules_list=rules_list,
            special_rules_toggle=special_rules_toggle,
            rules_group=rules_group,
        )

        # ── Wire favorites page ──────────────────────────────────
        wire_favorites_page(
            page_state=page_state,
            page_containers=page_containers,
            favorites_unit_selector=favorites_unit_selector,
            favorites_search_box=favorites_search_box,
            favorites_per_page_dropdown=favorites_per_page_dropdown,
            favorites_reload_btn=favorites_reload_btn,
            favorites_cards_html=favorites_cards_html,
            favorites_page_info=favorites_page_info,
            favorites_prev_btn=favorites_prev_btn,
            favorites_next_btn=favorites_next_btn,
            favorites_page_state=favorites_page_state,
            home_favorites_btn=home_favorites_btn,
            favorites_cards_cache_state=favorites_cards_cache_state,
            favorites_fav_ids_cache_state=favorites_fav_ids_cache_state,
            favorites_loaded_state=favorites_loaded_state,
        )

        # ── Wire global favorite toggle (star clicks) ────────────
        wire_fav_toggle(
            fav_toggle_card_id=fav_toggle_card_id,
            fav_toggle_btn=fav_toggle_btn,
        )

        # ── Wire global View button (card View clicks) ──────────
        wire_view_navigation(
            view_card_id=view_card_id,
            view_card_btn=view_card_btn,
            page_state=page_state,
            detail_card_id_state=detail_card_id_state,
            previous_page_state=previous_page_state,
            page_containers=page_containers,
        )

        # ── Wire existing create-form events (unchanged) ─────────
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
            vp_editing_state=vp_editing_state,
            cancel_edit_vp_btn=cancel_edit_vp_btn,
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
            zone_editing_state=zone_editing_state,
            cancel_edit_zone_btn=cancel_edit_zone_btn,
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
            objective_editing_state=objective_editing_state,
            cancel_edit_objective_btn=cancel_edit_objective_btn,
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
            scenography_editing_state=scenography_editing_state,
            cancel_edit_scenography_btn=cancel_edit_scenography_btn,
            generate_btn=generate_btn,
            svg_preview=svg_preview,
            output=output,
            create_scenario_btn=create_scenario_btn,
            create_scenario_status=create_scenario_status,
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home_recent_html,
            editing_card_id=editing_card_id,
            create_heading_md=create_heading_md,
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
