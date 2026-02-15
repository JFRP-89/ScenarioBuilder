"""Detail-page wiring — loads a card when detail page is shown.

Fetches card data and SVG from the Flask API.
Renders a rich read-only view with all scenario fields.

Internal modules
~~~~~~~~~~~~~~~~
- ``_detail._render``      - pure HTML rendering helpers (no Gradio).
- ``_detail._converters``  - API->UI state converters (no Gradio).
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import (
    get_default_actor_id,
    get_deployment_zones_choices,
    get_objective_points_choices,
    get_scenography_choices,
    get_special_rules_choices,
    get_victory_points_choices,
)
from adapters.ui_gradio.ui.components.search_helpers import escape_html
from adapters.ui_gradio.ui.router import (
    PAGE_EDIT,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
)

# ── Re-exports from internal modules (backward compat) ────────────
from adapters.ui_gradio.ui.wiring._detail._converters import (
    _api_deployment_to_state,
    _api_objectives_to_state,
    _api_scenography_to_state,
    _api_special_rules_to_state,
    _extract_objectives_text_for_form,
)
from adapters.ui_gradio.ui.wiring._detail._render import (  # noqa: F401
    _build_card_title,
    _extract_objectives_text,
    _field_row,
    _format_table_display,
    _render_detail_content,
    _render_mandatory_fields,
    _render_shared_with,
    _render_special_rules,
    _render_victory_points,
    _section_title,
    _wrap_svg,
)

# ============================================================================
# Service-dependent helpers (keep here — they need nav_svc / Gradio)
# ============================================================================


def _fetch_card_and_svg(
    card_id: str,
    actor_id: str = "",
) -> tuple[dict[str, Any], str]:
    """Fetch card data and SVG preview."""
    if not actor_id:
        actor_id = get_default_actor_id()
    card_data = nav_svc.get_card(actor_id, card_id)
    svg_html = nav_svc.get_card_svg(actor_id, card_id)
    return card_data, _wrap_svg(svg_html)


# ── Testable factory for the instant-reset function ──────────────
def _get_reset_detail_for_loading():
    """Return a function that immediately hides Edit/Delete and shows loading."""

    def _reset(_card_id: str) -> tuple:
        return (
            "## Loading…",
            '<div style="color:#999;text-align:center;">Loading…</div>',
            '<div style="color:#999;text-align:center;">Loading…</div>',
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    return _reset


def wire_detail_page(  # noqa: C901
    *,
    page_state: gr.State,
    page_containers: list[gr.Column],
    previous_page_state: gr.State,
    detail_card_id_state: gr.State,
    detail_reload_trigger: gr.State,
    editing_reload_trigger: gr.State | None = None,
    # Detail page widgets
    detail_title_md: gr.Markdown,
    detail_svg_preview: gr.HTML,
    detail_content_html: gr.HTML,
    detail_edit_btn: gr.Button,
    detail_delete_btn: gr.Button,
    detail_delete_confirm_row: gr.Row,
    detail_delete_confirm_btn: gr.Button,
    detail_delete_cancel_btn: gr.Button,
    detail_favorite_btn: gr.Button,
    # Edit page widgets (kept for backward compat)
    edit_title_md: gr.Markdown,
    edit_svg_preview: gr.HTML,
    edit_card_json: gr.JSON,
    # ── Create-form fields for populate-on-edit ────────────────
    editing_card_id: gr.State | None = None,
    create_heading_md: gr.Markdown | None = None,
    scenario_name: gr.Textbox | None = None,
    mode: gr.Radio | None = None,
    is_replicable: gr.Checkbox | None = None,
    armies: gr.Textbox | None = None,
    table_preset: gr.Radio | None = None,
    deployment: gr.Textbox | None = None,
    layout: gr.Textbox | None = None,
    objectives: gr.Textbox | None = None,
    initial_priority: gr.Textbox | None = None,
    objectives_with_vp_toggle: gr.Checkbox | None = None,
    vp_state: gr.State | None = None,
    visibility: gr.Radio | None = None,
    shared_with: gr.Textbox | None = None,
    special_rules_state: gr.State | None = None,
    scenography_state: gr.State | None = None,
    deployment_zones_state: gr.State | None = None,
    objective_points_state: gr.State | None = None,
    svg_preview: gr.HTML | None = None,
    output: gr.JSON | None = None,
    # Dropdowns, toggles, and groups for shape sections
    deployment_zones_list: gr.Dropdown | None = None,
    deployment_zones_toggle: gr.Checkbox | None = None,
    zones_group: gr.Group | None = None,
    objective_points_list: gr.Dropdown | None = None,
    objective_points_toggle: gr.Checkbox | None = None,
    objective_points_group: gr.Group | None = None,
    scenography_list: gr.Dropdown | None = None,
    scenography_toggle: gr.Checkbox | None = None,
    scenography_group: gr.Group | None = None,
    # VP section
    vp_list: gr.Dropdown | None = None,
    vp_group: gr.Group | None = None,
    # Special rules section
    rules_list: gr.Dropdown | None = None,
    special_rules_toggle: gr.Checkbox | None = None,
    rules_group: gr.Group | None = None,
    # Actor state for per-session auth
    actor_id_state: gr.State | None = None,
) -> None:
    """Wire the detail page interactions.

    * Loads card data when ``detail_card_id_state`` changes.
    * Shows/hides the Edit and Delete buttons based on ownership.
    * Delete button shows a confirmation prompt, then deletes via API.
    * Edit button navigates to the Create page in *edit mode*,
      populating all form fields and setting ``editing_card_id``.
    """

    # ── Security: deny-by-default reset ────────────────────────────
    # Step 1 (instant, no API call): hide the Edit button and show a
    # loading state so there is no window where the previous card's
    # Edit button is still clickable.
    _reset_detail_for_loading = _get_reset_detail_for_loading()

    # Step 2 (chained, calls API): fetch the real data and decide
    # whether to show Edit based on ownership.
    def _load_card_detail(card_id: str, actor_id: str = "") -> tuple:
        """Fetch card data, render detail view, and check ownership."""
        if not actor_id:
            actor_id = get_default_actor_id()
        if not card_id:
            return (
                "## Scenario Detail",
                '<div style="color:#999;">No card selected</div>',
                '<div style="color:#999;text-align:center;">No data</div>',
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )
        card_data, svg_wrapped = _fetch_card_and_svg(card_id, actor_id)

        if card_data.get("status") == "error":
            msg = escape_html(card_data.get("message", "Unknown error"))
            return (
                "## Error",
                f'<div style="color:red;">{msg}</div>',
                f'<div style="color:red;">{msg}</div>',
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        title = _build_card_title(card_data)
        content_html = _render_detail_content(card_data)

        # Ownership check: only show edit/delete if actor == owner
        is_owner = card_data.get("owner_id", "") == actor_id
        owner_visible = gr.update(visible=is_owner)

        return (
            title,
            svg_wrapped,
            content_html,
            owner_visible,
            owner_visible,
            gr.update(visible=False),
        )

    _detail_outputs = [
        detail_title_md,
        detail_svg_preview,
        detail_content_html,
        detail_edit_btn,
        detail_delete_btn,
        detail_delete_confirm_row,
    ]

    # When card_id or reload_trigger changes: reset immediately → then load real data
    _load_inputs: list[gr.components.Component] = [detail_card_id_state]
    if actor_id_state is not None:
        _load_inputs.append(actor_id_state)

    # Listen to both card_id changes AND reload_trigger changes
    # This ensures reload happens even if clicking the same card multiple times
    detail_card_id_state.change(
        fn=_reset_detail_for_loading,
        inputs=[detail_card_id_state],
        outputs=_detail_outputs,
    ).then(
        fn=_load_card_detail,
        inputs=_load_inputs,
        outputs=_detail_outputs,
    )

    # Also listen to reload_trigger to force reload even if card_id hasn't changed
    detail_reload_trigger.change(
        fn=_reset_detail_for_loading,
        inputs=[detail_card_id_state],
        outputs=_detail_outputs,
    ).then(
        fn=_load_card_detail,
        inputs=_load_inputs,
        outputs=_detail_outputs,
    )

    # Toggle favorite button
    def _toggle_fav(card_id: str, actor_id: str = "") -> str:
        if not card_id:
            return "⭐ Toggle Favorite"
        if not actor_id:
            actor_id = get_default_actor_id()
        result = nav_svc.toggle_favorite(actor_id, card_id)
        if result.get("is_favorite"):
            return "★ Favorited"
        return "☆ Toggle Favorite"

    _fav_inputs: list[gr.components.Component] = [detail_card_id_state]
    if actor_id_state is not None:
        _fav_inputs.append(actor_id_state)

    detail_favorite_btn.click(
        fn=_toggle_fav,
        inputs=_fav_inputs,
        outputs=[detail_favorite_btn],
    )

    # ── Delete button → show confirmation ─────────────────────────
    def _show_confirmation():
        """Show the delete confirmation row."""
        return gr.update(visible=True)

    def _hide_confirmation():
        """Hide the delete confirmation row."""
        return gr.update(visible=False)

    detail_delete_btn.click(
        fn=_show_confirmation,
        inputs=[],
        outputs=[detail_delete_confirm_row],
    )

    detail_delete_cancel_btn.click(
        fn=_hide_confirmation,
        inputs=[],
        outputs=[detail_delete_confirm_row],
    )

    # ── Confirm Delete → call API and navigate back ───────────────
    nav_outputs = [page_state, *page_containers]

    def _confirm_delete(card_id: str, from_page: str, actor_id: str = "") -> tuple:
        """Delete the card via API and navigate to previous page."""
        if not card_id:
            return (gr.update(visible=False), *navigate_to(PAGE_HOME))

        if not actor_id:
            actor_id = get_default_actor_id()
        result = nav_svc.delete_card(actor_id, card_id)

        if result.get("status") == "error":
            # Stay on page, hide confirmation
            return (gr.update(visible=False), *(gr.update(),) * len(nav_outputs))

        # Navigate back to where user came from
        if from_page not in [PAGE_HOME, PAGE_LIST, PAGE_FAVORITES]:
            from_page = PAGE_HOME
        return (gr.update(visible=False), *navigate_to(from_page))

    _delete_inputs: list[gr.components.Component] = [
        detail_card_id_state,
        previous_page_state,
    ]
    if actor_id_state is not None:
        _delete_inputs.append(actor_id_state)

    detail_delete_confirm_btn.click(
        fn=_confirm_delete,
        inputs=_delete_inputs,
        outputs=[detail_delete_confirm_row, *nav_outputs],
    )

    # ── Edit button → navigate to CREATE page + populate form ─────
    _can_edit_mode = (
        editing_card_id is not None
        and create_heading_md is not None
        and scenario_name is not None
    )

    if _can_edit_mode:
        _wire_edit_button(
            detail_edit_btn=detail_edit_btn,
            detail_card_id_state=detail_card_id_state,
            page_state=page_state,
            page_containers=page_containers,
            editing_card_id=editing_card_id,
            editing_reload_trigger=editing_reload_trigger,
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
            deployment_zones_list=deployment_zones_list,
            deployment_zones_toggle=deployment_zones_toggle,
            zones_group=zones_group,
            objective_points_list=objective_points_list,
            objective_points_toggle=objective_points_toggle,
            objective_points_group=objective_points_group,
            scenography_list=scenography_list,
            scenography_toggle=scenography_toggle,
            scenography_group=scenography_group,
            vp_list=vp_list,
            vp_group=vp_group,
            rules_list=rules_list,
            special_rules_toggle=special_rules_toggle,
            rules_group=rules_group,
        )
    else:
        # Fallback: navigate to old edit page (kept for compat)
        def _go_edit(card_id: str) -> tuple:
            nav = navigate_to(PAGE_EDIT)
            if not card_id:
                return (*nav, card_id, "## Edit", "", {})
            card_data, svg_wrapped = _fetch_card_and_svg(card_id)
            name = card_data.get("name", "")
            edit_title = f"## Edit: {escape_html(name)}" if name else "## Edit Scenario"
            return (*nav, card_id, edit_title, svg_wrapped, card_data)

        detail_edit_btn.click(
            fn=_go_edit,
            inputs=[detail_card_id_state],
            outputs=[
                page_state,
                *page_containers,
                detail_card_id_state,
                edit_title_md,
                edit_svg_preview,
                edit_card_json,
            ],
        )


def _wire_edit_button(  # noqa: C901
    *,
    detail_edit_btn: gr.Button,
    detail_card_id_state: gr.State,
    page_state: gr.State,
    page_containers: list[gr.Column],
    editing_card_id: gr.State,
    editing_reload_trigger: gr.State | None,
    create_heading_md: gr.Markdown,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    is_replicable: gr.Checkbox,
    armies: gr.Textbox,
    table_preset: gr.Radio | None,
    deployment: gr.Textbox,
    layout: gr.Textbox,
    objectives: gr.Textbox,
    initial_priority: gr.Textbox,
    objectives_with_vp_toggle: gr.Checkbox | None,
    vp_state: gr.State | None,
    visibility: gr.Radio | None,
    shared_with: gr.Textbox | None,
    special_rules_state: gr.State | None,
    scenography_state: gr.State | None,
    deployment_zones_state: gr.State | None,
    objective_points_state: gr.State | None,
    svg_preview: gr.HTML | None,
    output: gr.JSON | None,
    # Dropdowns, toggles, and groups for shape sections
    deployment_zones_list: gr.Dropdown | None = None,
    deployment_zones_toggle: gr.Checkbox | None = None,
    zones_group: gr.Group | None = None,
    objective_points_list: gr.Dropdown | None = None,
    objective_points_toggle: gr.Checkbox | None = None,
    objective_points_group: gr.Group | None = None,
    scenography_list: gr.Dropdown | None = None,
    scenography_toggle: gr.Checkbox | None = None,
    scenography_group: gr.Group | None = None,
    # VP section
    vp_list: gr.Dropdown | None = None,
    vp_group: gr.Group | None = None,
    # Special rules section
    rules_list: gr.Dropdown | None = None,
    special_rules_toggle: gr.Checkbox | None = None,
    rules_group: gr.Group | None = None,
) -> None:
    """Wire the Edit button to populate Create form and navigate there."""

    # Collect all outputs that will be populated
    _form_outputs: list[gr.components.Component] = [
        page_state,
        *page_containers,
        editing_card_id,
        create_heading_md,
        scenario_name,
        mode,
        is_replicable,
        armies,
    ]
    # Optional form fields
    _opt: list[gr.components.Component | None] = [
        table_preset,
        deployment,
        layout,
        objectives,
        initial_priority,
        objectives_with_vp_toggle,
        vp_state,
        visibility,
        shared_with,
        special_rules_state,
        scenography_state,
        deployment_zones_state,
        objective_points_state,
        svg_preview,
        output,
        # Dropdowns, toggles, groups
        deployment_zones_list,
        deployment_zones_toggle,
        zones_group,
        objective_points_list,
        objective_points_toggle,
        objective_points_group,
        scenography_list,
        scenography_toggle,
        scenography_group,
        # VP section
        vp_list,
        vp_group,
        # Special rules section
        rules_list,
        special_rules_toggle,
        rules_group,
    ]
    _all_outputs = _form_outputs + [c for c in _opt if c is not None]

    def _go_edit_form(card_id: str) -> tuple:  # noqa: C901
        """Fetch card data and navigate to Create page in edit mode."""
        # Navigate to EDIT page (shows create_container via page_visibility)
        nav = navigate_to(PAGE_EDIT)

        if not card_id:
            # No card selected — just navigate with defaults
            return (
                *nav,  # page_state + visibilities
                "",  # editing_card_id
                "## Create New Scenario",
                "",
                "casual",
                True,
                "",  # name, mode, is_replicable, armies
                *([gr.update()] * len([c for c in _opt if c is not None])),
            )

        card_data, svg_wrapped = _fetch_card_and_svg(card_id)
        if card_data.get("status") == "error":
            return (
                *nav,
                "",
                "## Create New Scenario",
                "",
                "casual",
                True,
                "",
                *([gr.update()] * len([c for c in _opt if c is not None])),
            )

        name = card_data.get("name", "")
        heading = f"## Edit: {escape_html(name)}" if name else "## Edit Scenario"

        # Extract objectives components
        obj_raw = card_data.get("objectives")
        obj_text, vp_enabled, vp_items = _extract_objectives_text_for_form(obj_raw)

        # Extract special rules
        rules_raw = card_data.get("special_rules")
        rules_state_val = (
            _api_special_rules_to_state(rules_raw)
            if isinstance(rules_raw, list) and rules_raw
            else []
        )

        # Extract shapes from card data
        shapes = card_data.get("shapes", {})
        if not isinstance(shapes, dict):
            shapes = {}
        scen_specs = shapes.get("scenography_specs", [])
        depl_shapes = shapes.get("deployment_shapes", [])
        obj_shapes = shapes.get("objective_shapes", [])

        # Shared with
        shared_list = card_data.get("shared_with", [])
        shared_val = ", ".join(shared_list) if isinstance(shared_list, list) else ""

        # Build the full return tuple
        values: list[Any] = [
            *nav,  # navigation
            card_id,  # editing_card_id
            heading,  # create_heading_md
            gr.update(value=name or ""),  # scenario_name
            gr.update(value=card_data.get("mode", "casual")),  # mode
            gr.update(value=card_data.get("is_replicable", True)),  # is_replicable
            gr.update(value=card_data.get("armies", "") or ""),  # armies
        ]
        # Optional fields (must match _opt order)
        opt_values: list[Any] = []
        if table_preset is not None:
            opt_values.append(
                gr.update(value=card_data.get("table_preset", "standard"))
            )
        if deployment is not None:
            opt_values.append(gr.update(value=card_data.get("deployment", "") or ""))
        if layout is not None:
            opt_values.append(gr.update(value=card_data.get("layout", "") or ""))
        if objectives is not None:
            opt_values.append(gr.update(value=obj_text))
        if initial_priority is not None:
            opt_values.append(
                gr.update(value=card_data.get("initial_priority", "") or "")
            )
        if objectives_with_vp_toggle is not None:
            opt_values.append(gr.update(value=vp_enabled))
        if vp_state is not None:
            opt_values.append(vp_items)
        if visibility is not None:
            opt_values.append(gr.update(value=card_data.get("visibility", "public")))
        if shared_with is not None:
            opt_values.append(gr.update(value=shared_val))
        if special_rules_state is not None:
            opt_values.append(rules_state_val)

        # Convert API shapes to UI state format
        scen_state_val: list[dict[str, Any]] = (
            _api_scenography_to_state(scen_specs) if scen_specs else []
        )
        depl_state_val: list[dict[str, Any]] = (
            _api_deployment_to_state(depl_shapes) if depl_shapes else []
        )
        obj_state_val: list[dict[str, Any]] = (
            _api_objectives_to_state(obj_shapes) if obj_shapes else []
        )

        if scenography_state is not None:
            opt_values.append(scen_state_val)
        if deployment_zones_state is not None:
            opt_values.append(depl_state_val)
        if objective_points_state is not None:
            opt_values.append(obj_state_val)
        if svg_preview is not None:
            opt_values.append(gr.update(value=svg_wrapped))
        if output is not None:
            opt_values.append(gr.update(value=None))

        # -- Dropdowns, toggles, and groups for shape sections --
        if deployment_zones_list is not None:
            choices = get_deployment_zones_choices(depl_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if deployment_zones_toggle is not None:
            has_depl = bool(depl_shapes)
            opt_values.append(gr.update(value=has_depl))
        if zones_group is not None:
            opt_values.append(gr.update(visible=bool(depl_shapes)))
        if objective_points_list is not None:
            choices = get_objective_points_choices(obj_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if objective_points_toggle is not None:
            has_obj = bool(obj_shapes)
            opt_values.append(gr.update(value=has_obj))
        if objective_points_group is not None:
            opt_values.append(gr.update(visible=bool(obj_shapes)))
        if scenography_list is not None:
            choices = get_scenography_choices(scen_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if scenography_toggle is not None:
            has_scen = bool(scen_specs)
            opt_values.append(gr.update(value=has_scen))
        if scenography_group is not None:
            opt_values.append(gr.update(visible=bool(scen_specs)))

        # -- Dropdowns, toggles, and groups for VP / special rules --
        if vp_list is not None:
            choices = get_victory_points_choices(vp_items)
            opt_values.append(gr.update(choices=choices, value=None))
        if vp_group is not None:
            opt_values.append(gr.update(visible=vp_enabled))
        if rules_list is not None:
            choices = get_special_rules_choices(rules_state_val)
            opt_values.append(gr.update(choices=choices, value=None))
        if special_rules_toggle is not None:
            opt_values.append(gr.update(value=bool(rules_state_val)))
        if rules_group is not None:
            opt_values.append(gr.update(visible=bool(rules_state_val)))

        values.extend(opt_values)
        return tuple(values)

    detail_edit_btn.click(
        fn=_go_edit_form,
        inputs=[detail_card_id_state],
        outputs=_all_outputs,
    )

    # ── F5 edit restore: when editing_reload_trigger fires, repopulate
    # the form from editing_card_id (set by _check_auth on page load).
    if editing_reload_trigger is not None:

        def _reload_edit_form(_trigger: int, card_id: str) -> tuple:
            """Repopulate edit form from card_id on page reload (F5)."""
            if not card_id:
                return tuple(gr.update() for _ in _all_outputs)
            return _go_edit_form(card_id)

        editing_reload_trigger.change(
            fn=_reload_edit_form,
            inputs=[editing_reload_trigger, editing_card_id],
            outputs=_all_outputs,
        )
