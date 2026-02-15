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

from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import (
    get_logged_in_label,
    get_profile,
    is_session_valid,
    update_profile,
)
from adapters.ui_gradio.ui.components import build_svg_preview, configure_renderer
from adapters.ui_gradio.ui.pages.edit_scenario import build_edit_page
from adapters.ui_gradio.ui.pages.favorites import build_favorites_page
from adapters.ui_gradio.ui.pages.home import build_home_page
from adapters.ui_gradio.ui.pages.list_scenarios import build_list_page
from adapters.ui_gradio.ui.pages.scenario_detail import build_detail_page
from adapters.ui_gradio.ui.router import (
    PAGE_TO_URL,
    build_detail_card_id_state,
    build_detail_reload_trigger,
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
from adapters.ui_gradio.ui.wiring.wire_home import load_recent_cards, wire_home_page
from adapters.ui_gradio.ui.wiring.wire_list import wire_list_page
from adapters.ui_gradio.ui.wiring.wire_navigation import wire_navigation
from adapters.ui_gradio.ui.wiring.wire_view import wire_view_navigation


def _event(component: Any, name: str) -> Any:
    """Access a dynamically-generated Gradio event trigger by name.

    Gradio attaches event methods (click, load, etc.) at runtime via
    ``EventListener``; some static analyzers cannot resolve them.
    This thin wrapper avoids false-positive 'no member' warnings.
    """
    return getattr(component, name)


def _close_profile():
    """Close profile panel."""
    return gr.update(visible=False)


def _check_auth(request: gr.Request):  # noqa: C901
    """Validate the ``sb_session`` HttpOnly cookie on page load.

    If the cookie carries a valid session, populate actor/session state
    and show the main UI.  Also reads the ``?page=`` query parameter from
    the browser ``Referer`` header so that the correct page container is
    shown immediately (e.g. after F5 on ``/sb/myscenarios/``).

    For the detail page (``scenario_detail``) the ``?id=`` query param
    is also extracted so the card content reloads on F5.

    Otherwise show the authentication-required gate with a login link.

    Returns a tuple of N outputs:
        page_state, detail_card_id_state, detail_reload_trigger,
        editing_card_id, editing_reload_trigger,
        actor_id_state, session_id_state, actor_id textbox,
        user_label, auth_gate, top_bar_row, *page_containers (one per page).
    """
    from adapters.ui_gradio.ui.router import (
        ALL_PAGES,
        PAGE_CREATE,
        PAGE_DETAIL,
        PAGE_EDIT,
        PAGE_HOME,
        URL_TO_PAGE,
    )

    def _page_visibility(target: str) -> list:
        """Return visibility updates for all page containers."""
        # Edit mode reuses the create form container
        effective = PAGE_CREATE if target == PAGE_EDIT else target
        return [gr.update(visible=(p == effective)) for p in ALL_PAGES]

    session_id = request.cookies.get("sb_session", "")
    if session_id:
        from infrastructure.auth.session_store import get_session

        session = get_session(session_id)
        if session is not None:
            actor_id = session["actor_id"]

            # ── Determine initial page + card_id from Referer URL ─
            initial_page = PAGE_HOME
            card_id_from_url = ""
            editing_id_from_url = ""
            referer = request.headers.get("referer", "")
            if referer:
                from urllib.parse import parse_qs, urlparse

                parsed = urlparse(referer)
                qs = parse_qs(parsed.query)

                # 1) Check ?page= query param  (redirect from /sb/create/)
                qp = qs.get("page", [None])[0]
                if qp and qp in ALL_PAGES:
                    initial_page = qp
                # 2) Check path directly  (e.g. /sb/myfavorites/)
                elif parsed.path:
                    path_norm = parsed.path.rstrip("/") + "/"
                    matched = URL_TO_PAGE.get(path_norm)
                    if matched and matched in ALL_PAGES:
                        initial_page = matched

                # 3) Extract card_id for detail page
                if initial_page == PAGE_DETAIL:
                    cid = qs.get("id", [None])[0]
                    if cid and cid.strip():
                        card_id_from_url = cid.strip()

                # 4) Extract card_id for edit page
                if initial_page == PAGE_EDIT:
                    cid = qs.get("id", [None])[0]
                    if cid and cid.strip():
                        editing_id_from_url = cid.strip()

            # detail_reload_trigger: bump to 1 so the .change handler fires
            reload_trigger = 1 if card_id_from_url else gr.update()

            # editing_reload_trigger: bump to 1 so the edit form repopulates
            edit_reload = 1 if editing_id_from_url else gr.update()

            return (
                initial_page,  # page_state
                card_id_from_url or gr.update(),  # detail_card_id_state
                reload_trigger,  # detail_reload_trigger
                editing_id_from_url or gr.update(),  # editing_card_id
                edit_reload,  # editing_reload_trigger
                actor_id,  # actor_id_state
                session_id,  # session_id_state
                gr.update(value=actor_id),  # actor_id textbox
                gr.update(value=get_logged_in_label(actor_id)),  # user_label
                gr.update(visible=False),  # auth_gate → hide
                gr.update(visible=True),  # top_bar_row → show
                *_page_visibility(initial_page),  # page containers
            )

    # Not authenticated — show the auth gate, hide everything else
    return (
        gr.update(),  # page_state (unchanged)
        gr.update(),  # detail_card_id_state (unchanged)
        gr.update(),  # detail_reload_trigger (unchanged)
        gr.update(),  # editing_card_id (unchanged)
        gr.update(),  # editing_reload_trigger (unchanged)
        "",  # actor_id_state
        "",  # session_id_state
        gr.update(),  # actor_id textbox
        gr.update(),  # user_label
        gr.update(visible=True),  # auth_gate → show
        gr.update(visible=False),  # top_bar_row → hide
        *_page_visibility("__none__"),  # hide all page containers
    )


# =============================================================================
# URL-sync JavaScript (injected into <head>)
# =============================================================================

# Elem-ID of each page container (must match what build_*_page sets).
_ELEM_ID_TO_PAGE = {
    "page-home": "home",
    "page-list-scenarios": "list_scenarios",
    "page-scenario-detail": "scenario_detail",
    "page-create-scenario": "create_scenario",
    "page-edit-scenario": "edit_scenario",
    "page-favorites": "favorites",
}


def _build_url_sync_head_js() -> str:
    """Return a ``<script>`` tag that keeps the browser URL in sync.

    Client-side behaviour:
    1. **MutationObserver** — watches each page container for
       attribute changes.  When a container becomes visible,
       it pushes the matching URL via ``history.pushState``.
    2. **popstate** — handles browser back/forward by showing
       the correct page container directly via style manipulation.
    """
    import json

    # Python dicts → JS object literals
    elem_to_page_js = json.dumps(_ELEM_ID_TO_PAGE)
    page_to_url_js = json.dumps(PAGE_TO_URL)

    # Reverse map: page name → elem id
    page_to_elem_js = json.dumps({v: k for k, v in _ELEM_ID_TO_PAGE.items()})

    return (
        "<script>\n"
        "(function() {\n"
        f"  var ELEM_TO_PAGE = {elem_to_page_js};\n"
        f"  var PAGE_TO_URL  = {page_to_url_js};\n"
        f"  var PAGE_TO_ELEM = {page_to_elem_js};\n"
        "\n"
        "  /* 1. Push URL when a page container becomes visible */\n"
        "  function _getInputVal(elemId) {\n"
        "    var c = document.getElementById(elemId);\n"
        "    if (!c) return '';\n"
        "    var inp = c.querySelector('textarea') || c.querySelector('input');\n"
        "    return inp ? inp.value : '';\n"
        "  }\n"
        "\n"
        "  function startObserver() {\n"
        "    var observer = new MutationObserver(function(mutations) {\n"
        "      for (var i = 0; i < mutations.length; i++) {\n"
        "        var el = mutations[i].target;\n"
        "        var pageName = ELEM_TO_PAGE[el.id];\n"
        "        if (!pageName) continue;\n"
        "        var isVisible = el.offsetParent !== null\n"
        "                        || getComputedStyle(el).display !== 'none';\n"
        "        if (isVisible) {\n"
        "          var targetUrl = PAGE_TO_URL[pageName];\n"
        "          if (targetUrl) {\n"
        "            /* Create container is shared: check editing mirror */\n"
        "            if (pageName === 'create_scenario') {\n"
        "              var eid = _getInputVal('editing-card-id-mirror');\n"
        "              if (eid) {\n"
        "                targetUrl = PAGE_TO_URL['edit_scenario'] + '?id=' + encodeURIComponent(eid);\n"
        "                pageName = 'edit_scenario';\n"
        "              }\n"
        "            }\n"
        "            var current = window.location.pathname + window.location.search;\n"
        "            if (current !== targetUrl) {\n"
        "              history.pushState({page: pageName}, '', targetUrl);\n"
        "            }\n"
        "          }\n"
        "        }\n"
        "      }\n"
        "    });\n"
        "    var ids = Object.keys(ELEM_TO_PAGE);\n"
        "    for (var j = 0; j < ids.length; j++) {\n"
        "      var el = document.getElementById(ids[j]);\n"
        "      if (el) observer.observe(el, { attributes: true });\n"
        "    }\n"
        "  }\n"
        "\n"
        "  /* 2. Handle browser back/forward — hide/show containers */\n"
        "  window.addEventListener('popstate', function(e) {\n"
        "    var page = (e.state && e.state.page) ? e.state.page : 'home';\n"
        "    /* edit_scenario reuses create_scenario container */\n"
        "    var showPage = (page === 'edit_scenario') ? 'create_scenario' : page;\n"
        "    var allIds = Object.keys(ELEM_TO_PAGE);\n"
        "    for (var k = 0; k < allIds.length; k++) {\n"
        "      var container = document.getElementById(allIds[k]);\n"
        "      if (!container) continue;\n"
        "      var shouldShow = (ELEM_TO_PAGE[allIds[k]] === showPage);\n"
        "      container.style.display = shouldShow ? '' : 'none';\n"
        "    }\n"
        "  });\n"
        "\n"
        "  /* 3. Detail page: replace URL with ?id=<card_id> when mirror updates */\n"
        "  var _lastDetailMirror = '';\n"
        "  var _lastEditMirror = '';\n"
        "  setInterval(function() {\n"
        "    /* Detail view mirror */\n"
        "    var dval = _getInputVal('detail-card-id-mirror');\n"
        "    if (dval && dval !== _lastDetailMirror) {\n"
        "      _lastDetailMirror = dval;\n"
        "      var detailEl = document.getElementById('page-scenario-detail');\n"
        "      if (detailEl && (detailEl.offsetParent !== null\n"
        "                       || getComputedStyle(detailEl).display !== 'none')) {\n"
        "        var url = PAGE_TO_URL['scenario_detail'] + '?id=' + encodeURIComponent(dval);\n"
        "        var current = window.location.pathname + window.location.search;\n"
        "        if (current !== url) {\n"
        "          history.replaceState({page: 'scenario_detail'}, '', url);\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "    /* Edit form mirror */\n"
        "    var eval2 = _getInputVal('editing-card-id-mirror');\n"
        "    if (eval2 && eval2 !== _lastEditMirror) {\n"
        "      _lastEditMirror = eval2;\n"
        "      var createEl = document.getElementById('page-create-scenario');\n"
        "      if (createEl && (createEl.offsetParent !== null\n"
        "                       || getComputedStyle(createEl).display !== 'none')) {\n"
        "        var url2 = PAGE_TO_URL['edit_scenario'] + '?id=' + encodeURIComponent(eval2);\n"
        "        var cur2 = window.location.pathname + window.location.search;\n"
        "        if (cur2 !== url2) {\n"
        "          history.replaceState({page: 'edit_scenario'}, '', url2);\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "    /* When editing mirror clears and create form is visible, revert to /sb/create/ */\n"
        "    if (!eval2 && _lastEditMirror) {\n"
        "      _lastEditMirror = '';\n"
        "      var createEl2 = document.getElementById('page-create-scenario');\n"
        "      if (createEl2 && (createEl2.offsetParent !== null\n"
        "                        || getComputedStyle(createEl2).display !== 'none')) {\n"
        "        var cur3 = window.location.pathname + window.location.search;\n"
        "        if (cur3 !== PAGE_TO_URL['create_scenario']) {\n"
        "          history.replaceState({page: 'create_scenario'}, '', PAGE_TO_URL['create_scenario']);\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "  }, 300);\n"
        "\n"
        "  /* Boot — start observer after Gradio renders */\n"
        "  if (document.readyState === 'loading') {\n"
        "    document.addEventListener('DOMContentLoaded', function() {\n"
        "      setTimeout(startObserver, 800);\n"
        "    });\n"
        "  } else {\n"
        "    setTimeout(startObserver, 800);\n"
        "  }\n"
        "})();\n"
        "</script>"
    )


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
    _URL_SYNC_JS = _build_url_sync_head_js()

    with gr.Blocks(title="Scenario Card Generator", head=_URL_SYNC_JS) as app:
        # ── Inject infrastructure renderer (composition root) ────────
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        configure_renderer(SvgMapRenderer().render)

        # ── Global state ─────────────────────────────────────────────
        page_state = build_page_state()
        detail_card_id_state = build_detail_card_id_state()
        detail_reload_trigger = build_detail_reload_trigger()
        previous_page_state = build_previous_page_state()
        editing_card_id = gr.State(value="")
        editing_reload_trigger = gr.State(value=0)
        actor_id_state = gr.State(value="")
        session_id_state = gr.State(value="")

        # ════════════════════════════════════════════════════════════
        # AUTH GATE — shown when the user has no valid session cookie.
        # Flask's /login page is the real login form; this is just a
        # placeholder that appears if someone navigates to /sb directly.
        # ════════════════════════════════════════════════════════════
        with gr.Column(visible=False, elem_id="auth-gate") as auth_gate:
            gr.Markdown("## Scenario Card Generator — Authentication Required")
            auth_message = gr.Markdown(
                'You are not logged in. Please <a href="/login">log in</a> '
                "to continue.",
                elem_id="auth-message",
            )

        # ════════════════════════════════════════════════════════════
        # TOP BAR — hidden until login (visible on all pages once logged in)
        # ════════════════════════════════════════════════════════════
        with gr.Row(visible=False, elem_id="top-bar") as top_bar_row:
            user_label = gr.Markdown(
                value="",
                elem_id="user-label",
            )
            profile_btn = gr.Button(
                "👤 Profile",
                variant="secondary",
                size="sm",
                elem_id="profile-btn",
            )
            logout_btn = gr.Button(
                "🚪 Logout",
                variant="secondary",
                size="sm",
                elem_id="logout-btn",
            )

        # ── Profile panel (hidden by default) ────────────────────
        with gr.Column(visible=False, elem_id="profile-panel") as profile_panel:
            gr.Markdown("### Profile")
            profile_username_display = gr.Textbox(
                label="Username",
                interactive=False,
                elem_id="profile-username",
            )
            profile_name_input = gr.Textbox(
                label="Display Name",
                elem_id="profile-name",
            )
            profile_email_input = gr.Textbox(
                label="Email",
                elem_id="profile-email",
            )
            with gr.Row():
                profile_save_btn = gr.Button(
                    "Save",
                    variant="primary",
                    size="sm",
                    elem_id="profile-save-btn",
                )
                profile_close_btn = gr.Button(
                    "Close",
                    variant="secondary",
                    size="sm",
                    elem_id="profile-close-btn",
                )
            profile_message = gr.Textbox(
                label="",
                interactive=False,
                visible=False,
                elem_id="profile-message",
            )

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

        # Home starts hidden — only shown after login
        home_container.visible = False

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
            _detail_delete_confirm_msg,
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
            actor_id = actor_section.build_actor_section("")

            scenario_name, mode, is_replicable, armies = (
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

        # ── Hidden mirror of detail_card_id_state for JS URL sync ─
        # Updated whenever detail_card_id_state changes so the JS
        # MutationObserver can include ?id=<card_id> in the URL.
        detail_card_id_mirror = gr.Textbox(
            value="",
            visible=False,
            elem_id="detail-card-id-mirror",
        )
        detail_card_id_state.change(
            fn=lambda cid: cid,
            inputs=[detail_card_id_state],
            outputs=[detail_card_id_mirror],
        )

        # ── Hidden mirror of editing_card_id for JS URL sync ─────
        # Updated whenever editing_card_id changes so the JS
        # can show /sb/edit/?id=<card_id> instead of /sb/create/.
        editing_card_id_mirror = gr.Textbox(
            value="",
            visible=False,
            elem_id="editing-card-id-mirror",
        )
        editing_card_id.change(
            fn=lambda cid: cid,
            inputs=[editing_card_id],
            outputs=[editing_card_id_mirror],
        )

        # ── Wire navigation ──────────────────────────────────────
        wire_navigation(
            page_state=page_state,
            previous_page_state=previous_page_state,
            page_containers=page_containers,
            home_create_btn=home_create_btn,
            list_back_btn=list_back_btn,
            detail_back_btn=detail_back_btn,
            create_back_btn=create_back_btn,
            edit_back_btn=edit_back_btn,
            favorites_back_btn=favorites_back_btn,
            session_id_state=session_id_state,
            actor_id_state=actor_id_state,
            login_panel=auth_gate,
            top_bar_row=top_bar_row,
            login_message=auth_message,
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
            actor_id_state=actor_id_state,
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
            actor_id_state=actor_id_state,
            session_id_state=session_id_state,
        )

        # ── Wire detail page (load card, fav, edit, delete) ─────
        wire_detail_page(
            page_state=page_state,
            page_containers=page_containers,
            previous_page_state=previous_page_state,
            detail_card_id_state=detail_card_id_state,
            detail_reload_trigger=detail_reload_trigger,
            editing_reload_trigger=editing_reload_trigger,
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
            is_replicable=is_replicable,
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
            actor_id_state=actor_id_state,
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
            actor_id_state=actor_id_state,
            session_id_state=session_id_state,
        )

        # ── Wire global favorite toggle (star clicks) ────────────
        wire_fav_toggle(
            fav_toggle_card_id=fav_toggle_card_id,
            fav_toggle_btn=fav_toggle_btn,
            actor_id_state=actor_id_state,
        )

        # ── Wire global View button (card View clicks) ──────────
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

        # ── Wire existing create-form events (unchanged) ─────────
        wire_events(
            actor_id=actor_id,
            scenario_name=scenario_name,
            mode=mode,
            is_replicable=is_replicable,
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
            preview_full_state=preview_full_state,
            create_scenario_btn=create_scenario_btn,
            create_scenario_status=create_scenario_status,
            page_state=page_state,
            page_containers=page_containers,
            home_recent_html=home_recent_html,
            editing_card_id=editing_card_id,
            create_heading_md=create_heading_md,
        )

        # ════════════════════════════════════════════════════════════
        # AUTH EVENT WIRING — logout (JS → Flask), profile
        # ════════════════════════════════════════════════════════════

        # Logout via JavaScript: POST /auth/logout (clears cookie on
        # Flask side), then redirect to /login.
        _LOGOUT_JS = """
        () => {
            const m = document.cookie.match(/sb_csrf=([^;]+)/);
            const csrf = m ? m[1] : "";
            fetch("/auth/logout", {
                method: "POST",
                headers: {"X-CSRF-Token": csrf},
                credentials: "same-origin"
            }).finally(() => { window.location.href = "/login"; });
        }
        """
        _event(logout_btn, "click")(fn=None, js=_LOGOUT_JS)

        def _open_profile(current_actor: str, sid: str):
            """Open profile panel and load data, with session guard."""
            if not is_session_valid(sid):
                return (
                    gr.update(visible=False),  # profile_panel stays hidden
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(value="", visible=False),
                    "",  # session_id_state
                    "",  # actor_id_state
                    gr.update(visible=True),  # auth_gate
                    gr.update(visible=False),  # top_bar_row
                    gr.update(
                        value='Session expired \u2014 please <a href="/login">log in</a> again.',
                    ),  # auth_message
                    *(gr.update(visible=False) for _ in page_containers),
                )
            result = get_profile(current_actor)
            no_change = (
                gr.update(),  # session_id_state
                gr.update(),  # actor_id_state
                gr.update(),  # auth_gate
                gr.update(),  # top_bar_row
                gr.update(),  # auth_message
                *(gr.update() for _ in page_containers),
            )
            if result["ok"]:
                profile = result["profile"]
                return (
                    gr.update(visible=True),  # profile_panel
                    gr.update(value=profile["username"]),
                    gr.update(value=profile["name"]),
                    gr.update(value=profile["email"]),
                    gr.update(value="", visible=False),
                    *no_change,
                )
            return (
                gr.update(visible=True),
                gr.update(value=current_actor),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value="User not found.", visible=True),
                *no_change,
            )

        _event(profile_btn, "click")(
            fn=_open_profile,
            inputs=[actor_id_state, session_id_state],
            outputs=[
                profile_panel,
                profile_username_display,
                profile_name_input,
                profile_email_input,
                profile_message,
                session_id_state,
                actor_id_state,
                auth_gate,
                top_bar_row,
                auth_message,
                *page_containers,
            ],
        )

        def _save_profile(current_actor: str, name: str, email: str, sid: str):
            """Save profile changes, with session guard."""
            if not is_session_valid(sid):
                return (
                    gr.update(
                        value='Session expired \u2014 please <a href="/login">log in</a> again.',
                        visible=True,
                    ),
                    "",  # session_id_state
                    "",  # actor_id_state
                    gr.update(visible=False),  # profile_panel
                    gr.update(visible=True),  # auth_gate
                    gr.update(visible=False),  # top_bar_row
                    *(gr.update(visible=False) for _ in page_containers),
                )
            result = update_profile(current_actor, name, email)
            no_change = (
                gr.update(),  # session_id_state
                gr.update(),  # actor_id_state
                gr.update(),  # profile_panel
                gr.update(),  # auth_gate
                gr.update(),  # top_bar_row
                *(gr.update() for _ in page_containers),
            )
            return (
                gr.update(value=str(result["message"]), visible=True),
                *no_change,
            )

        _event(profile_save_btn, "click")(
            fn=_save_profile,
            inputs=[
                actor_id_state,
                profile_name_input,
                profile_email_input,
                session_id_state,
            ],
            outputs=[
                profile_message,
                session_id_state,
                actor_id_state,
                profile_panel,
                auth_gate,
                top_bar_row,
                *page_containers,
            ],
        )

        _event(profile_close_btn, "click")(
            fn=_close_profile,
            inputs=[],
            outputs=[profile_panel],
        )

        # ── Auth check on page load (F5 / refresh) ──────────────
        # Reads the sb_session HttpOnly cookie (set by Flask /auth/login)
        # and either shows the main UI or the auth gate.
        # Also reads ?page= from Referer to show the correct page,
        # and ?id= to restore detail card view on F5.
        auth_load_event = _event(app, "load")(
            fn=_check_auth,
            inputs=[],
            outputs=[
                page_state,
                detail_card_id_state,
                detail_reload_trigger,
                editing_card_id,
                editing_reload_trigger,
                actor_id_state,
                session_id_state,
                actor_id,
                user_label,
                auth_gate,
                top_bar_row,
                *page_containers,
            ],
        )
        # After successful auth check, load home page content
        auth_load_event.then(
            fn=load_recent_cards,
            inputs=[
                home_mode_filter,
                home_preset_filter,
                home_unit_selector,
                home_page_state,
                home_search_box,
                home_per_page_dropdown,
                actor_id_state,
            ],
            outputs=[
                home_recent_html,
                home_page_info,
                home_page_state,
                home_cards_cache_state,
                home_fav_ids_cache_state,
            ],
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
