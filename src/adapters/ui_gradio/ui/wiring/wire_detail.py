"""Detail-page wiring — loads a card when detail page is shown.

Fetches card data and SVG from the Flask API.
Renders a rich read-only view with all scenario fields.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.router import PAGE_EDIT, navigate_to

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


def wire_detail_page(
    *,
    page_state: gr.State,
    page_containers: list[gr.Column],
    detail_card_id_state: gr.State,
    # Detail page widgets
    detail_title_md: gr.Markdown,
    detail_svg_preview: gr.HTML,
    detail_content_html: gr.HTML,
    detail_edit_btn: gr.Button,
    detail_favorite_btn: gr.Button,
    # Edit page widgets (for navigation to edit)
    edit_title_md: gr.Markdown,
    edit_svg_preview: gr.HTML,
    edit_card_json: gr.JSON,
) -> None:
    """Wire the detail page interactions."""

    def _load_card_detail(card_id: str) -> tuple[str, str, str]:
        """Fetch card data and render detail view."""
        if not card_id:
            return (
                "## Scenario Detail",
                '<div style="color:#999;">No card selected</div>',
                '<div style="color:#999;text-align:center;">No data</div>',
            )
        card_data, svg_wrapped = _fetch_card_and_svg(card_id)

        if card_data.get("status") == "error":
            msg = card_data.get("message", "Unknown error")
            return (
                "## Error",
                f'<div style="color:red;">{msg}</div>',
                f'<div style="color:red;">{msg}</div>',
            )

        title = _build_card_title(card_data)
        content_html = _render_detail_content(card_data)
        return title, svg_wrapped, content_html

    # When card_id changes, load the detail
    detail_card_id_state.change(
        fn=_load_card_detail,
        inputs=[detail_card_id_state],
        outputs=[detail_title_md, detail_svg_preview, detail_content_html],
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

    # Edit button → navigate to edit page and load data
    def _go_edit(card_id: str) -> tuple:
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
