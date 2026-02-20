"""Detail-page wiring — loads a card when detail page is shown.

Fetches card data and SVG from the Flask API.
Renders a rich read-only view with all scenario fields.

Internal modules
~~~~~~~~~~~~~~~~
- ``_detail._render``      - pure HTML rendering helpers (no Gradio).
- ``_detail._converters``  - API->UI state converters (no Gradio).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import (
    get_default_actor_id,
)
from adapters.ui_gradio.ui.components.search_helpers import escape_html
from adapters.ui_gradio.ui.router import (
    PAGE_EDIT,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
)
from adapters.ui_gradio.ui.wiring._detail._converters import (
    _api_deployment_to_state,
    _api_objectives_to_state,
    _api_scenography_to_state,
    _api_special_rules_to_state,
    _extract_objectives_text_for_form,
)
from adapters.ui_gradio.ui.wiring._detail._edit_button import (
    EditButtonCtx,
)
from adapters.ui_gradio.ui.wiring._detail._edit_button import (
    wire_edit_button as _wire_edit_button,
)
from adapters.ui_gradio.ui.wiring._detail._render import (
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

# Re-exports for tests — keep in __all__ so linters treat them as public.
__all__ = [
    "wire_detail_page",
    "DetailPageCtx",
    "EditButtonCtx",
    "_fetch_card_and_svg",
    "_get_reset_detail_for_loading",
    "_load_card_detail",
    "_toggle_fav",
    "_confirm_delete",
    "_go_edit_fallback",
    "_build_inputs",
    # _detail._converters
    "_api_deployment_to_state",
    "_api_objectives_to_state",
    "_api_scenography_to_state",
    "_api_special_rules_to_state",
    "_extract_objectives_text_for_form",
    # _detail._render
    "_build_card_title",
    "_extract_objectives_text",
    "_field_row",
    "_format_table_display",
    "_render_detail_content",
    "_render_mandatory_fields",
    "_render_shared_with",
    "_render_special_rules",
    "_render_victory_points",
    "_section_title",
    "_wrap_svg",
]

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


# ── Module-level handlers (avoids nesting CC penalty) ────────────


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


def _toggle_fav(card_id: str, actor_id: str = "") -> str:
    """Toggle favorite status for the given card."""
    if not card_id:
        return "⭐ Toggle Favorite"
    if not actor_id:
        actor_id = get_default_actor_id()
    result = nav_svc.toggle_favorite(actor_id, card_id)
    if result.get("is_favorite"):
        return "★ Favorited"
    return "☆ Toggle Favorite"


def _confirm_delete(
    card_id: str,
    from_page: str,
    actor_id: str = "",
    *,
    n_nav_outputs: int,
) -> tuple:
    """Delete the card via API and navigate to previous page."""
    if not card_id:
        return (gr.update(visible=False), *navigate_to(PAGE_HOME))

    if not actor_id:
        actor_id = get_default_actor_id()
    result = nav_svc.delete_card(actor_id, card_id)

    if result.get("status") == "error":
        return (gr.update(visible=False), *(gr.update(),) * n_nav_outputs)

    if from_page not in [PAGE_HOME, PAGE_LIST, PAGE_FAVORITES]:
        from_page = PAGE_HOME
    return (gr.update(visible=False), *navigate_to(from_page))


def _go_edit_fallback(card_id: str) -> tuple:
    """Fallback edit: navigate to old edit page."""
    nav = navigate_to(PAGE_EDIT)
    if not card_id:
        return (*nav, card_id, "## Edit", "", {})
    card_data, svg_wrapped = _fetch_card_and_svg(card_id)
    name = card_data.get("name", "")
    edit_title = f"## Edit: {escape_html(name)}" if name else "## Edit Scenario"
    return (*nav, card_id, edit_title, svg_wrapped, card_data)


def _build_inputs(
    base: list[gr.components.Component],
    actor_id_state: gr.State | None,
) -> list[gr.components.Component]:
    """Append actor_id_state to inputs if present."""
    if actor_id_state is not None:
        return [*base, actor_id_state]
    return list(base)


@dataclass(frozen=True)
class DetailPageCtx:
    """Widget references for detail-page wiring."""

    page_state: gr.State
    page_containers: list[gr.Column]
    previous_page_state: gr.State
    detail_card_id_state: gr.Textbox
    detail_reload_trigger: gr.State
    # Detail page widgets
    detail_title_md: gr.Markdown
    detail_svg_preview: gr.HTML
    detail_content_html: gr.HTML
    detail_edit_btn: gr.Button
    detail_delete_btn: gr.Button
    detail_delete_confirm_row: gr.Row
    detail_delete_confirm_btn: gr.Button
    detail_delete_cancel_btn: gr.Button
    detail_favorite_btn: gr.Button
    # Edit page widgets (kept for backward compat)
    edit_title_md: gr.Markdown
    edit_svg_preview: gr.HTML
    edit_card_json: gr.JSON
    # Create-form fields for populate-on-edit
    editing_card_id: gr.Textbox | None = None
    editing_reload_trigger: gr.State | None = None
    create_heading_md: gr.Markdown | None = None
    scenario_name: gr.Textbox | None = None
    mode: gr.Radio | None = None
    is_replicable: gr.Checkbox | None = None
    armies: gr.Textbox | None = None
    table_preset: gr.Radio | None = None
    deployment: gr.Textbox | None = None
    layout: gr.Textbox | None = None
    objectives: gr.Textbox | None = None
    initial_priority: gr.Textbox | None = None
    objectives_with_vp_toggle: gr.Checkbox | None = None
    vp_state: gr.State | None = None
    visibility: gr.Radio | None = None
    shared_with: gr.Textbox | None = None
    special_rules_state: gr.State | None = None
    scenography_state: gr.State | None = None
    deployment_zones_state: gr.State | None = None
    objective_points_state: gr.State | None = None
    svg_preview: gr.HTML | None = None
    output: gr.JSON | None = None
    deployment_zones_list: gr.Dropdown | None = None
    deployment_zones_toggle: gr.Checkbox | None = None
    zones_group: gr.Group | None = None
    objective_points_list: gr.Dropdown | None = None
    objective_points_toggle: gr.Checkbox | None = None
    objective_points_group: gr.Group | None = None
    scenography_list: gr.Dropdown | None = None
    scenography_toggle: gr.Checkbox | None = None
    scenography_group: gr.Group | None = None
    vp_list: gr.Dropdown | None = None
    vp_group: gr.Group | None = None
    rules_list: gr.Dropdown | None = None
    special_rules_toggle: gr.Checkbox | None = None
    rules_group: gr.Group | None = None
    actor_id_state: gr.State | None = None
    create_scenario_btn: gr.Button | None = None


def wire_detail_page(*, ctx: DetailPageCtx) -> None:
    """Wire the detail page interactions.

    * Loads card data when ``detail_card_id_state`` changes.
    * Shows/hides the Edit and Delete buttons based on ownership.
    * Delete button shows a confirmation prompt, then deletes via API.
    * Edit button navigates to the Create page in *edit mode*,
      populating all form fields and setting ``editing_card_id``.
    """
    c = ctx

    # ── Security: deny-by-default reset ────────────────────────────
    _reset_detail_for_loading = _get_reset_detail_for_loading()

    _detail_outputs = [
        c.detail_title_md,
        c.detail_svg_preview,
        c.detail_content_html,
        c.detail_edit_btn,
        c.detail_delete_btn,
        c.detail_delete_confirm_row,
    ]

    _load_inputs = _build_inputs([c.detail_card_id_state], c.actor_id_state)

    c.detail_card_id_state.change(
        fn=_reset_detail_for_loading,
        inputs=[c.detail_card_id_state],
        outputs=_detail_outputs,
    ).then(
        fn=_load_card_detail,
        inputs=_load_inputs,
        outputs=_detail_outputs,
    )

    c.detail_reload_trigger.change(
        fn=_reset_detail_for_loading,
        inputs=[c.detail_card_id_state],
        outputs=_detail_outputs,
    ).then(
        fn=_load_card_detail,
        inputs=_load_inputs,
        outputs=_detail_outputs,
    )

    # Toggle favorite button
    c.detail_favorite_btn.click(
        fn=_toggle_fav,
        inputs=_build_inputs([c.detail_card_id_state], c.actor_id_state),
        outputs=[c.detail_favorite_btn],
    )

    # ── Delete button → show/hide confirmation ────────────────────
    c.detail_delete_btn.click(
        fn=lambda: gr.update(visible=True),
        inputs=[],
        outputs=[c.detail_delete_confirm_row],
    )
    c.detail_delete_cancel_btn.click(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[c.detail_delete_confirm_row],
    )

    # ── Confirm Delete → call API and navigate back ───────────────
    nav_outputs = [c.page_state, *c.page_containers]

    c.detail_delete_confirm_btn.click(
        fn=partial(_confirm_delete, n_nav_outputs=len(nav_outputs)),
        inputs=_build_inputs(
            [c.detail_card_id_state, c.previous_page_state],
            c.actor_id_state,
        ),
        outputs=[c.detail_delete_confirm_row, *nav_outputs],
    )

    # ── Edit button → navigate to CREATE page + populate form ─────
    _can_edit_mode = (
        c.editing_card_id is not None
        and c.create_heading_md is not None
        and c.scenario_name is not None
    )

    if _can_edit_mode:
        _wire_edit_button(
            ctx=EditButtonCtx(
                fetch_card_and_svg=_fetch_card_and_svg,
                detail_edit_btn=c.detail_edit_btn,
                detail_card_id_state=c.detail_card_id_state,
                actor_id_state=c.actor_id_state,
                page_state=c.page_state,
                page_containers=c.page_containers,
                editing_card_id=c.editing_card_id,
                editing_reload_trigger=c.editing_reload_trigger,
                create_heading_md=c.create_heading_md,
                scenario_name=c.scenario_name,
                mode=c.mode,
                is_replicable=c.is_replicable,
                armies=c.armies,
                table_preset=c.table_preset,
                deployment=c.deployment,
                layout=c.layout,
                objectives=c.objectives,
                initial_priority=c.initial_priority,
                objectives_with_vp_toggle=c.objectives_with_vp_toggle,
                vp_state=c.vp_state,
                visibility=c.visibility,
                shared_with=c.shared_with,
                special_rules_state=c.special_rules_state,
                scenography_state=c.scenography_state,
                deployment_zones_state=c.deployment_zones_state,
                objective_points_state=c.objective_points_state,
                svg_preview=c.svg_preview,
                output=c.output,
                deployment_zones_list=c.deployment_zones_list,
                deployment_zones_toggle=c.deployment_zones_toggle,
                zones_group=c.zones_group,
                objective_points_list=c.objective_points_list,
                objective_points_toggle=c.objective_points_toggle,
                objective_points_group=c.objective_points_group,
                scenography_list=c.scenography_list,
                scenography_toggle=c.scenography_toggle,
                scenography_group=c.scenography_group,
                vp_list=c.vp_list,
                vp_group=c.vp_group,
                rules_list=c.rules_list,
                special_rules_toggle=c.special_rules_toggle,
                rules_group=c.rules_group,
                create_scenario_btn=c.create_scenario_btn,
            )
        )
    else:
        c.detail_edit_btn.click(
            fn=_go_edit_fallback,
            inputs=[c.detail_card_id_state],
            outputs=[
                c.page_state,
                *c.page_containers,
                c.detail_card_id_state,
                c.edit_title_md,
                c.edit_svg_preview,
                c.edit_card_json,
            ],
        )
