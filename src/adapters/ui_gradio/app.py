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
from adapters.ui_gradio.ui._url_sync_js import build_url_sync_head_js
from adapters.ui_gradio.ui.components import configure_renderer
from adapters.ui_gradio.ui.pages.auth_components import (
    build_auth_gate,
    build_profile_panel,
    build_top_bar,
)
from adapters.ui_gradio.ui.pages.create_scenario import build_create_page
from adapters.ui_gradio.ui.pages.edit_scenario import build_edit_page
from adapters.ui_gradio.ui.pages.favorites import build_favorites_page
from adapters.ui_gradio.ui.pages.home import build_home_page
from adapters.ui_gradio.ui.pages.list_scenarios import build_list_page
from adapters.ui_gradio.ui.pages.scenario_detail import build_detail_page
from adapters.ui_gradio.ui.router import (
    build_detail_card_id_state,
    build_detail_reload_trigger,
    build_page_state,
    build_previous_page_state,
)
from adapters.ui_gradio.ui.wiring import wire_events
from adapters.ui_gradio.ui.wiring._kwargs import kwargs_for_call
from adapters.ui_gradio.ui.wiring.wire_auth import AuthEventsCtx, wire_auth_events
from adapters.ui_gradio.ui.wiring.wire_detail import DetailPageCtx, wire_detail_page
from adapters.ui_gradio.ui.wiring.wire_fav_toggle import wire_fav_toggle
from adapters.ui_gradio.ui.wiring.wire_favorites import (
    FavoritesPageCtx,
    wire_favorites_page,
)
from adapters.ui_gradio.ui.wiring.wire_home import (
    HomePageCtx,
    load_recent_cards,
    wire_home_page,
)
from adapters.ui_gradio.ui.wiring.wire_list import ListPageCtx, wire_list_page
from adapters.ui_gradio.ui.wiring.wire_navigation import NavigationCtx, wire_navigation
from adapters.ui_gradio.ui.wiring.wire_view import wire_view_navigation


# =============================================================================
# App builder
# =============================================================================
def build_app() -> gr.Blocks:
    """Build and return the multi-page Gradio Blocks app.

    Pages: Home, List Scenarios, Scenario Detail, Create Scenario,
           Edit Scenario, Favorites.

    Navigation uses gr.State to track the current page and show/hide
    gr.Column containers.  Browser URL is kept in sync via JS.

    Returns:
        A gradio.Blocks instance ready to launch
    """
    # ── Build URL-sync JavaScript for <head> ─────────────────────
    # Mirrors PAGE_TO_URL from router.py on the client side.
    _URL_SYNC_JS = build_url_sync_head_js()

    with gr.Blocks(title="Scenario Card Generator", head=_URL_SYNC_JS) as app:
        # ── Inject infrastructure renderer (composition root) ────────
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        configure_renderer(SvgMapRenderer().render)

        # ── Global state ─────────────────────────────────────────────
        page_state = build_page_state()
        detail_card_id_state = build_detail_card_id_state()
        detail_reload_trigger = build_detail_reload_trigger()
        previous_page_state = build_previous_page_state()
        editing_card_id = gr.Textbox(
            value="", visible=False, elem_id="editing-card-id-mirror"
        )
        editing_reload_trigger = gr.State(value=0)
        actor_id_state = gr.State(value="")
        session_id_state = gr.State(value="")

        # ── Auth gate, top bar, profile panel ────────────────────────
        auth_gate, auth_message = build_auth_gate()
        top_bar_row, user_label, profile_btn, logout_btn = build_top_bar()
        (
            profile_panel,
            profile_username_display,
            profile_name_input,
            profile_email_input,
            profile_pw_input,
            profile_pw_confirm_input,
            profile_save_btn,
            profile_close_btn,
            profile_message,
        ) = build_profile_panel()

        # ── Build pages ──────────────────────────────────────────────
        home = build_home_page()
        home.container.visible = False  # shown after login

        lst = build_list_page()
        detail = build_detail_page()
        create = build_create_page()
        edit = build_edit_page()
        fav = build_favorites_page()

        # ── Collect page containers (order must match ALL_PAGES) ──
        page_containers = [
            home.container,  # PAGE_HOME
            lst.container,  # PAGE_LIST
            detail.container,  # PAGE_DETAIL
            create.container,  # PAGE_CREATE
            edit.container,  # PAGE_EDIT
            fav.container,  # PAGE_FAVORITES
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

        # NOTE: detail_card_id_state and editing_card_id are Textbox
        # (not State) so that .change() is statically recognized and
        # their values are available in the DOM for JS URL-sync.
        # No separate mirrors needed — they ARE the mirrors.

        # --- Wiring ---
        wire_navigation(
            ctx=NavigationCtx(
                page_state=page_state,
                previous_page_state=previous_page_state,
                page_containers=page_containers,
                home_create_btn=home.create_btn,
                list_back_btn=lst.back_btn,
                detail_back_btn=detail.back_btn,
                create_back_btn=create.back_btn,
                edit_back_btn=edit.back_btn,
                favorites_back_btn=fav.back_btn,
                session_id_state=session_id_state,
                actor_id_state=actor_id_state,
                login_panel=auth_gate,
                top_bar_row=top_bar_row,
                login_message=auth_message,
                # Form reset when navigating to Create page
                create_form_components=[
                    create.scenario_name,
                    create.mode,
                    create.is_replicable,
                    create.generate_from_seed,
                    create.armies,
                    create.deployment,
                    create.layout,
                    create.objectives,
                    create.initial_priority,
                    create.visibility,
                    create.shared_with,
                    create.special_rules_state,
                    create.objectives_with_vp_toggle,
                    create.vp_state,
                    create.scenography_state,
                    create.deployment_zones_state,
                    create.objective_points_state,
                    create.svg_preview,
                    create.output,
                ],
                create_dropdown_lists=[
                    create.vp_input,
                    create.vp_list,
                    create.rules_list,
                    create.scenography_list,
                    create.deployment_zones_list,
                    create.objective_points_list,
                ],
                editing_card_id=editing_card_id,
                create_heading_md=create.create_heading_md,
                create_scenario_btn=create.create_scenario_btn,
                # Home-page reload when navigating back
                home_reload_fn=load_recent_cards,
                home_reload_inputs=[
                    home.mode_filter,
                    home.preset_filter,
                    home.unit_selector,
                    home.page_state,
                    home.search_box,
                    home.per_page_dropdown,
                    actor_id_state,
                ],
                home_reload_outputs=[
                    home.recent_cards_html,
                    home.page_info,
                    home.page_state,
                    home.cards_cache_state,
                    home.fav_ids_cache_state,
                ],
            )
        )

        wire_home_page(
            ctx=HomePageCtx(
                home_recent_html=home.recent_cards_html,
                home_mode_filter=home.mode_filter,
                home_preset_filter=home.preset_filter,
                home_unit_selector=home.unit_selector,
                home_search_box=home.search_box,
                home_per_page_dropdown=home.per_page_dropdown,
                home_reload_btn=home.reload_btn,
                home_prev_btn=home.prev_btn,
                home_page_info=home.page_info,
                home_next_btn=home.next_btn,
                home_page_state=home.page_state,
                home_cards_cache_state=home.cards_cache_state,
                home_fav_ids_cache_state=home.fav_ids_cache_state,
                app=app,
                actor_id_state=actor_id_state,
            )
        )

        wire_list_page(
            ctx=ListPageCtx(
                page_state=page_state,
                page_containers=page_containers,
                list_filter=lst.filter_radio,
                list_unit_selector=lst.unit_selector,
                list_search_box=lst.search_box,
                list_per_page_dropdown=lst.per_page_dropdown,
                list_reload_btn=lst.reload_btn,
                list_cards_html=lst.cards_html,
                list_page_info=lst.page_info,
                list_prev_btn=lst.prev_btn,
                list_next_btn=lst.next_btn,
                list_page_state=lst.page_state,
                home_browse_btn=home.browse_btn,
                list_cards_cache_state=lst.cards_cache_state,
                list_fav_ids_cache_state=lst.fav_ids_cache_state,
                list_loaded_state=lst.loaded_state,
                actor_id_state=actor_id_state,
                session_id_state=session_id_state,
            )
        )

        wire_detail_page(
            ctx=DetailPageCtx(
                page_state=page_state,
                page_containers=page_containers,
                previous_page_state=previous_page_state,
                detail_card_id_state=detail_card_id_state,
                detail_reload_trigger=detail_reload_trigger,
                editing_reload_trigger=editing_reload_trigger,
                detail_title_md=detail.card_title_md,
                detail_svg_preview=detail.svg_preview,
                detail_content_html=detail.detail_content_html,
                detail_edit_btn=detail.edit_btn,
                detail_delete_btn=detail.delete_btn,
                detail_delete_confirm_row=detail.delete_confirm_row,
                detail_delete_confirm_btn=detail.delete_confirm_btn,
                detail_delete_cancel_btn=detail.delete_cancel_btn,
                detail_favorite_btn=detail.favorite_btn,
                edit_title_md=edit.card_title_md,
                edit_svg_preview=edit.svg_preview,
                edit_card_json=edit.card_json,
                editing_card_id=editing_card_id,
                create_heading_md=create.create_heading_md,
                scenario_name=create.scenario_name,
                mode=create.mode,
                is_replicable=create.is_replicable,
                armies=create.armies,
                table_preset=create.table_preset,
                deployment=create.deployment,
                layout=create.layout,
                objectives=create.objectives,
                initial_priority=create.initial_priority,
                objectives_with_vp_toggle=create.objectives_with_vp_toggle,
                vp_state=create.vp_state,
                visibility=create.visibility,
                shared_with=create.shared_with,
                special_rules_state=create.special_rules_state,
                scenography_state=create.scenography_state,
                deployment_zones_state=create.deployment_zones_state,
                objective_points_state=create.objective_points_state,
                svg_preview=create.svg_preview,
                output=create.output,
                deployment_zones_list=create.deployment_zones_list,
                deployment_zones_toggle=create.deployment_zones_toggle,
                zones_group=create.zones_group,
                objective_points_list=create.objective_points_list,
                objective_points_toggle=create.objective_points_toggle,
                objective_points_group=create.objective_points_group,
                scenography_list=create.scenography_list,
                scenography_toggle=create.scenography_toggle,
                scenography_group=create.scenography_group,
                vp_list=create.vp_list,
                vp_group=create.vp_group,
                rules_list=create.rules_list,
                special_rules_toggle=create.special_rules_toggle,
                rules_group=create.rules_group,
                actor_id_state=actor_id_state,
                create_scenario_btn=create.create_scenario_btn,
            )
        )

        wire_favorites_page(
            ctx=FavoritesPageCtx(
                page_state=page_state,
                page_containers=page_containers,
                favorites_unit_selector=fav.unit_selector,
                favorites_search_box=fav.search_box,
                favorites_per_page_dropdown=fav.per_page_dropdown,
                favorites_reload_btn=fav.reload_btn,
                favorites_cards_html=fav.cards_html,
                favorites_page_info=fav.page_info,
                favorites_prev_btn=fav.prev_btn,
                favorites_next_btn=fav.next_btn,
                favorites_page_state=fav.page_state,
                home_favorites_btn=home.favorites_btn,
                favorites_cards_cache_state=fav.cards_cache_state,
                favorites_fav_ids_cache_state=fav.fav_ids_cache_state,
                favorites_loaded_state=fav.loaded_state,
                actor_id_state=actor_id_state,
                session_id_state=session_id_state,
            )
        )

        wire_fav_toggle(
            fav_toggle_card_id=fav_toggle_card_id,
            fav_toggle_btn=fav_toggle_btn,
            actor_id_state=actor_id_state,
        )

        wire_view_navigation(
            view_card_id=view_card_id,
            view_card_btn=view_card_btn,
            page_state=page_state,
            detail_card_id_state=detail_card_id_state,
            detail_reload_trigger=detail_reload_trigger,
            previous_page_state=previous_page_state,
            page_containers=page_containers,
            session_id_state=session_id_state,
            actor_id_state=actor_id_state,
            login_panel=auth_gate,
            top_bar_row=top_bar_row,
            login_message=auth_message,
        )

        # ── Create-form events: use ** unpacking for compactness ──
        _CREATE_OVERRIDES = {
            "page_state",
            "page_containers",
            "home_recent_html",
            "home_page_info",
            "home_page_state",
            "home_cards_cache_state",
            "home_fav_ids_cache_state",
            "editing_card_id",
        }
        _payload = {
            k: v for k, v in vars(create).items() if k not in ("container", "back_btn")
        }
        _create_kwargs = kwargs_for_call(
            _payload,
            wire_events,
            explicit_overrides=_CREATE_OVERRIDES,
            strict_extras=False,
        )
        wire_events(
            **_create_kwargs,
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home.recent_cards_html,
            home_page_info=home.page_info,
            home_page_state=home.page_state,
            home_cards_cache_state=home.cards_cache_state,
            home_fav_ids_cache_state=home.fav_ids_cache_state,
            editing_card_id=editing_card_id,
        )

        # ── Auth wiring (logout, profile, auth-check on load) ────
        wire_auth_events(
            ctx=AuthEventsCtx(
                app=app,
                auth_gate=auth_gate,
                auth_message=auth_message,
                top_bar_row=top_bar_row,
                user_label=user_label,
                logout_btn=logout_btn,
                profile_btn=profile_btn,
                profile_panel=profile_panel,
                profile_username_display=profile_username_display,
                profile_name_input=profile_name_input,
                profile_email_input=profile_email_input,
                profile_pw_input=profile_pw_input,
                profile_pw_confirm_input=profile_pw_confirm_input,
                profile_save_btn=profile_save_btn,
                profile_close_btn=profile_close_btn,
                profile_message=profile_message,
                page_state=page_state,
                detail_card_id_state=detail_card_id_state,
                detail_reload_trigger=detail_reload_trigger,
                editing_card_id=editing_card_id,
                editing_reload_trigger=editing_reload_trigger,
                actor_id_state=actor_id_state,
                session_id_state=session_id_state,
                actor_id_component=create.actor_id,
                page_containers=page_containers,
                load_recent_cards_fn=load_recent_cards,
                home_mode_filter=home.mode_filter,
                home_preset_filter=home.preset_filter,
                home_unit_selector=home.unit_selector,
                home_page_state=home.page_state,
                home_search_box=home.search_box,
                home_per_page_dropdown=home.per_page_dropdown,
                home_recent_html=home.recent_cards_html,
                home_page_info=home.page_info,
                home_cards_cache_state=home.cards_cache_state,
                home_fav_ids_cache_state=home.fav_ids_cache_state,
            )
        )

    return app


# =============================================================================
# Main entry point (standalone — prefer combined_app for production)
# =============================================================================
if __name__ == "__main__":
    build_app().launch(
        server_name=os.environ.get(
            "UI_HOST", "0.0.0.0"
        ),  # nosec B104 - container/local dev
        server_port=int(os.environ.get("UI_PORT", "7860")),
    )
