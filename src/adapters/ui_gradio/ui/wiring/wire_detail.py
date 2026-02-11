"""Detail-page wiring — loads a card when detail page is shown.

Fetches card data and SVG from the Flask API.
Renders a rich read-only view with all scenario fields.
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
from adapters.ui_gradio.ui.router import (
    PAGE_CREATE,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
)

# ============================================================================
# HTML rendering helpers
# ============================================================================


def _field_row(label: str, value: str) -> str:
    """Render a single label: value row."""
    return (
        f'<div style="display:flex;gap:8px;padding:6px 0;'
        f'border-bottom:1px solid #f0f0f0;">'
        f'<span style="font-weight:600;color:#555;min-width:150px;'
        f'flex-shrink:0;">{label}:</span>'
        f'<span style="color:#333;">{value}</span>'
        f"</div>"
    )


def _section_title(title: str) -> str:
    """Render a section title."""
    return (
        f'<div style="font-size:16px;font-weight:700;color:#222;'
        f"margin-top:20px;margin-bottom:8px;padding-bottom:4px;"
        f'border-bottom:2px solid #e0e0e0;">{title}</div>'
    )


def _render_shared_with(shared_list: list[str]) -> str:
    """Render shared_with as a list."""
    if not shared_list:
        return ""
    items = "".join(
        f'<li style="padding:2px 0;color:#333;">{user}</li>' for user in shared_list
    )
    return (
        f'{_section_title("Shared With")}'
        f'<ul style="margin:4px 0 0 16px;padding:0;list-style:disc;">'
        f"{items}</ul>"
    )


def _render_victory_points(vp_list: list[str]) -> str:
    """Render victory points as a bullet list."""
    if not vp_list:
        return ""
    items = "".join(
        f'<li style="padding:3px 0;color:#333;font-size:14px;">{vp}</li>'
        for vp in vp_list
    )
    return (
        f'<div style="margin-top:8px;">'
        f'<span style="font-weight:600;color:#555;">Victory Points:</span>'
        f'<ul style="margin:4px 0 0 16px;padding:0;'
        f'list-style:disc;">{items}</ul>'
        f"</div>"
    )


def _render_special_rules(rules: list[dict[str, Any]]) -> str:
    """Render special rules with source-only, description, and sources accordion."""
    if not rules:
        return ""

    # Separate rules by type
    source_only: list[dict[str, Any]] = []
    with_description: list[dict[str, Any]] = []

    for rule in rules:
        desc = rule.get("description", "")
        source = rule.get("source", "")
        if source and not desc:
            source_only.append(rule)
        elif desc:
            with_description.append(rule)
        else:
            source_only.append(rule)

    html_parts = [_section_title("Special Rules")]

    # 1) Source-only rules: bold names, comma-separated
    if source_only:
        names_html = ", ".join(
            f'<strong>{r.get("name", "Unknown")}</strong>' for r in source_only
        )
        html_parts.append(
            f'<div style="padding:6px 0;color:#333;font-size:14px;">'
            f"{names_html}</div>"
        )

    # 2) Description rules: Name: Description
    if with_description:
        for rule in with_description:
            name = rule.get("name", "Unknown")
            desc = rule.get("description", "")
            html_parts.append(
                f'<div style="padding:4px 0;color:#333;font-size:14px;">'
                f"<strong>{name}</strong>: {desc}</div>"
            )

    # 3) Collapsible Source accordion (closed by default)
    rules_with_source = [r for r in rules if r.get("source")]
    if rules_with_source:
        source_items = "".join(
            f'<div style="padding:3px 0;font-size:13px;color:#555;">'
            f'<strong>{r.get("name", "Unknown")}</strong>: '
            f'{r.get("source", "")}</div>'
            for r in rules_with_source
        )
        html_parts.append(
            f'<details style="margin-top:8px;border:1px solid #e0e0e0;'
            f'border-radius:6px;padding:8px;">'
            f'<summary style="cursor:pointer;font-weight:600;color:#555;'
            f'font-size:14px;">Sources</summary>'
            f'<div style="margin-top:8px;">{source_items}</div>'
            f"</details>"
        )

    return "\n".join(html_parts)


def _format_table_display(card_data: dict[str, Any]) -> str:
    """Format table preset display with dimensions."""
    table_preset = card_data.get("table_preset", "—")
    table_mm = card_data.get("table_mm", {})
    w_mm = table_mm.get("width_mm", 0) if isinstance(table_mm, dict) else 0
    h_mm = table_mm.get("height_mm", 0) if isinstance(table_mm, dict) else 0
    table_display = table_preset.capitalize()
    if w_mm and h_mm:
        w_cm = w_mm / 10
        h_cm = h_mm / 10
        table_display += f" ({int(w_cm)}x{int(h_cm)} cm / {w_mm}x{h_mm} mm)"
    return str(table_display)


def _extract_objectives_text(objectives: Any) -> str:
    """Extract objectives display text from str or dict."""
    if isinstance(objectives, dict):
        return str(objectives.get("objective", "—"))
    if isinstance(objectives, str):
        return objectives
    return "—"


def _render_mandatory_fields(card_data: dict[str, Any]) -> list[str]:
    """Render all mandatory scenario detail fields."""
    parts: list[str] = []
    parts.append(_section_title("Scenario Details"))
    parts.append(_field_row("Author / Owner", card_data.get("owner_id", "—")))
    parts.append(_field_row("Scenario Name", card_data.get("name", "—") or "—"))
    parts.append(_field_row("Game Mode", card_data.get("mode", "—").capitalize()))
    parts.append(_field_row("Seed", str(card_data.get("seed", "—"))))

    armies = card_data.get("armies")
    parts.append(_field_row("Armies", armies if armies else "—"))
    parts.append(
        _field_row("Visibility", card_data.get("visibility", "—").capitalize())
    )
    parts.append(_field_row("Table Preset", _format_table_display(card_data)))

    deployment = card_data.get("deployment")
    parts.append(_field_row("Deployment", deployment if deployment else "—"))

    layout = card_data.get("layout")
    parts.append(_field_row("Layout", layout if layout else "—"))

    objectives = card_data.get("objectives")
    parts.append(_field_row("Objectives", _extract_objectives_text(objectives)))

    # Victory points right below objectives
    if isinstance(objectives, dict):
        vp_list = objectives.get("victory_points", [])
        if vp_list:
            parts.append(_render_victory_points(vp_list))

    initial_priority = card_data.get("initial_priority")
    parts.append(
        _field_row("Initial Priority", initial_priority if initial_priority else "—")
    )
    return parts


def _render_detail_content(card_data: dict[str, Any]) -> str:
    """Render the full detail content HTML for a card."""
    parts: list[str] = [
        '<div style="max-width:700px;margin:0 auto;padding:16px;'
        'font-family:system-ui,-apple-system,sans-serif;">'
    ]

    parts.extend(_render_mandatory_fields(card_data))

    # Conditional: shared_with
    if card_data.get("visibility") == "shared":
        shared_with = card_data.get("shared_with", [])
        if shared_with:
            parts.append(_render_shared_with(shared_with))

    # Special Rules
    special_rules = card_data.get("special_rules")
    if special_rules and isinstance(special_rules, list):
        parts.append(_render_special_rules(special_rules))

    parts.append("</div>")
    return "\n".join(parts)


def _build_card_title(card_data: dict[str, Any]) -> str:
    """Build the title markdown from card data."""
    name = card_data.get("name", "")
    if name and name.strip():
        return f"## {name}"
    mode = card_data.get("mode", "casual")
    seed = card_data.get("seed", 1)
    mode_display = mode.capitalize() if isinstance(mode, str) else "Scenario"
    seed_display = f"#{seed}" if seed else ""
    return f"## {mode_display} Scenario {seed_display}".strip()


def _wrap_svg(svg_html: str) -> str:
    """Wrap raw SVG HTML in a styled container."""
    if "<svg" in svg_html.lower():
        return (
            '<div style="display:flex;justify-content:center;'
            "align-items:center;padding:16px;background:#fafafa;"
            'border:1px solid #e0e0e0;border-radius:8px;">'
            f"{svg_html}</div>"
        )
    return svg_html


def _fetch_card_and_svg(
    card_id: str,
) -> tuple[dict[str, Any], str]:
    """Fetch card data and SVG preview."""
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
    seed: gr.Number | None = None,
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
    def _load_card_detail(card_id: str) -> tuple:
        """Fetch card data, render detail view, and check ownership."""
        if not card_id:
            return (
                "## Scenario Detail",
                '<div style="color:#999;">No card selected</div>',
                '<div style="color:#999;text-align:center;">No data</div>',
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )
        card_data, svg_wrapped = _fetch_card_and_svg(card_id)

        if card_data.get("status") == "error":
            msg = card_data.get("message", "Unknown error")
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
        actor_id = get_default_actor_id()
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

    # When card_id changes: reset immediately → then load real data
    detail_card_id_state.change(
        fn=_reset_detail_for_loading,
        inputs=[detail_card_id_state],
        outputs=_detail_outputs,
    ).then(
        fn=_load_card_detail,
        inputs=[detail_card_id_state],
        outputs=_detail_outputs,
    )

    # Toggle favorite button
    def _toggle_fav(card_id: str) -> str:
        if not card_id:
            return "⭐ Toggle Favorite"
        actor_id = get_default_actor_id()
        result = nav_svc.toggle_favorite(actor_id, card_id)
        if result.get("is_favorite"):
            return "★ Favorited"
        return "☆ Toggle Favorite"

    detail_favorite_btn.click(
        fn=_toggle_fav,
        inputs=[detail_card_id_state],
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

    def _confirm_delete(card_id: str, from_page: str) -> tuple:
        """Delete the card via API and navigate to previous page."""
        if not card_id:
            return (gr.update(visible=False), *navigate_to(PAGE_HOME))

        actor_id = get_default_actor_id()
        result = nav_svc.delete_card(actor_id, card_id)

        if result.get("status") == "error":
            # Stay on page, hide confirmation
            return (gr.update(visible=False), *(gr.update(),) * len(nav_outputs))

        # Navigate back to where user came from
        if from_page not in [PAGE_HOME, PAGE_LIST, PAGE_FAVORITES]:
            from_page = PAGE_HOME
        return (gr.update(visible=False), *navigate_to(from_page))

    detail_delete_confirm_btn.click(
        fn=_confirm_delete,
        inputs=[detail_card_id_state, previous_page_state],
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
            from adapters.ui_gradio.ui.router import PAGE_EDIT

            nav = navigate_to(PAGE_EDIT)
            if not card_id:
                return (*nav, card_id, "## Edit", "", {})
            card_data, svg_wrapped = _fetch_card_and_svg(card_id)
            name = card_data.get("name", "")
            edit_title = f"## Edit: {name}" if name else "## Edit Scenario"
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


def _extract_objectives_text_for_form(
    objectives: Any,
) -> tuple[str, bool, list[dict[str, Any]]]:
    """Extract form values from objectives data.

    Returns (objectives_text, vp_enabled, vp_state_list).
    The vp_state_list uses the UI state format: {id, description}.
    """
    import uuid

    if isinstance(objectives, dict):
        obj_text = str(objectives.get("objective", ""))
        vp_items = objectives.get("victory_points", [])
        vp_enabled = bool(vp_items)
        vp_list = (
            [{"id": str(uuid.uuid4())[:8], "description": str(vp)} for vp in vp_items]
            if isinstance(vp_items, list) and vp_items
            else []
        )
        return obj_text, vp_enabled, vp_list
    if isinstance(objectives, str):
        return objectives, False, []
    return "", False, []


def _api_special_rules_to_state(
    api_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API special rules to UI state format.

    API format: {"name": "...", "description": "..."} or {"name": "...", "source": "..."}
    State format: {"id": "xxx", "name": "...", "rule_type": "description|source", "value": "..."}
    """
    import uuid

    result: list[dict[str, Any]] = []
    for rule in api_rules:
        if not isinstance(rule, dict):
            continue
        sid = str(uuid.uuid4())[:8]
        name = rule.get("name", "")
        # Determine rule_type and value from API format
        if "source" in rule:
            rule_type = "source"
            value = rule.get("source", "")
        else:
            rule_type = "description"
            value = rule.get("description", "")
        result.append(
            {
                "id": sid,
                "name": name,
                "rule_type": rule_type,
                "value": value,
            }
        )
    return result


# ============================================================================
# API → UI state format converters
# ============================================================================


def _api_deployment_to_state(api_shapes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert API deployment shapes to UI state format.

    API: {"type": "rect", "description": "D", "x": 0, ...}
    State: {"id": "xxx", "label": "D (Zone xxx)", "data": {...}, "form_type": "rectangle"}
    """
    import uuid

    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        if not isinstance(shape, dict):
            continue
        sid = str(uuid.uuid4())[:8]
        desc = shape.get("description", "") or ""
        shape_type = shape.get("type", "rect")

        # Determine form_type from shape type
        if shape_type == "rect":
            form_type = "rectangle"
        elif shape_type == "polygon":
            # Could be triangle or circle — guess from point count
            points = shape.get("points", [])
            form_type = "triangle" if len(points) <= 4 else "circle"
        else:
            form_type = "rectangle"

        label = f"{desc} (Zone {sid})" if desc else f"Zone {sid}"
        entry: dict[str, Any] = {
            "id": sid,
            "label": label,
            "data": dict(shape),  # copy the full API shape as data
            "form_type": form_type,
        }
        result.append(entry)
    return result


def _api_scenography_to_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API scenography shapes to UI state format.

    API: {"type": "circle", "cx": 300, "cy": 400, "r": 150, ...}
    State: {"id": "xxx", "type": "circle", "label": "desc (Circle xxx)",
            "data": {...}, "allow_overlap": false}
    """
    import uuid

    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        if not isinstance(shape, dict):
            continue
        sid = str(uuid.uuid4())[:8]
        shape_type = shape.get("type", "rect")
        desc = shape.get("description", "") or ""
        allow_overlap = shape.get("allow_overlap", False)

        type_label = shape_type.capitalize()
        label = f"{desc} ({type_label} {sid})" if desc else f"{type_label} {sid}"

        # Build data without the allow_overlap key (it lives on the outer entry)
        data = {k: v for k, v in shape.items() if k != "allow_overlap"}

        entry: dict[str, Any] = {
            "id": sid,
            "type": shape_type,
            "label": label,
            "data": data,
            "allow_overlap": allow_overlap,
        }
        result.append(entry)
    return result


def _api_objectives_to_state(
    api_shapes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert API objective shapes to UI state format.

    API: {"type": "objective_point", "cx": 600, "cy": 600, "description": "T"}
    State: {"id": "xxx", "cx": 600, "cy": 600, "description": "T"}
    """
    import uuid

    result: list[dict[str, Any]] = []
    for shape in api_shapes:
        if not isinstance(shape, dict):
            continue
        sid = str(uuid.uuid4())[:8]
        entry: dict[str, Any] = {
            "id": sid,
            "cx": shape.get("cx", 0),
            "cy": shape.get("cy", 0),
        }
        desc = shape.get("description", "")
        if desc:
            entry["description"] = desc
        result.append(entry)
    return result


def _wire_edit_button(  # noqa: C901
    *,
    detail_edit_btn: gr.Button,
    detail_card_id_state: gr.State,
    page_state: gr.State,
    page_containers: list[gr.Column],
    editing_card_id: gr.State,
    create_heading_md: gr.Markdown,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    seed: gr.Number,
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
        seed,
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
        # Navigate to CREATE page
        nav = navigate_to(PAGE_CREATE)

        if not card_id:
            # No card selected — just navigate with defaults
            return (
                *nav,  # page_state + visibilities
                "",  # editing_card_id
                "## Create New Scenario",
                "",
                "casual",
                1,
                "",  # name, mode, seed, armies
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
                1,
                "",
                *([gr.update()] * len([c for c in _opt if c is not None])),
            )

        name = card_data.get("name", "")
        heading = f"## Edit: {name}" if name else "## Edit Scenario"

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
            gr.update(value=card_data.get("seed", 1)),  # seed
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
