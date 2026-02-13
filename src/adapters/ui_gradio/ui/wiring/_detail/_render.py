"""Pure HTML rendering helpers for the scenario detail page.

Every function here is a **pure function** — no Gradio, no API calls.
Only dependency: ``escape_html`` for XSS safety.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.ui.components.search_helpers import escape_html

# ============================================================================
# Low-level row / section helpers
# ============================================================================


def _field_row(label: str, value: str) -> str:
    """Render a single label: value row."""
    safe_label = escape_html(label)
    safe_value = escape_html(value)
    return (
        f'<div style="display:flex;gap:8px;padding:6px 0;'
        f'border-bottom:1px solid #f0f0f0;">'
        f'<span style="font-weight:600;color:#555;min-width:150px;'
        f'flex-shrink:0;">{safe_label}:</span>'
        f'<span style="color:#333;">{safe_value}</span>'
        f"</div>"
    )


def _section_title(title: str) -> str:
    """Render a section title."""
    safe_title = escape_html(title)
    return (
        f'<div style="font-size:16px;font-weight:700;color:#222;'
        f"margin-top:20px;margin-bottom:8px;padding-bottom:4px;"
        f'border-bottom:2px solid #e0e0e0;">{safe_title}</div>'
    )


# ============================================================================
# Composite renderers
# ============================================================================


def _render_shared_with(shared_list: list[str]) -> str:
    """Render shared_with as a list."""
    if not shared_list:
        return ""
    items = "".join(
        f'<li style="padding:2px 0;color:#333;">{escape_html(user)}</li>'
        for user in shared_list
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
        f'<li style="padding:3px 0;color:#333;font-size:14px;">'
        f"{escape_html(str(vp))}</li>"
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
            f'<strong>{escape_html(r.get("name", "Unknown"))}</strong>'
            for r in source_only
        )
        html_parts.append(
            f'<div style="padding:6px 0;color:#333;font-size:14px;">'
            f"{names_html}</div>"
        )

    # 2) Description rules: Name: Description
    if with_description:
        for rule in with_description:
            name = escape_html(rule.get("name", "Unknown"))
            desc = escape_html(rule.get("description", ""))
            html_parts.append(
                f'<div style="padding:4px 0;color:#333;font-size:14px;">'
                f"<strong>{name}</strong>: {desc}</div>"
            )

    # 3) Collapsible Source accordion (closed by default)
    rules_with_source = [r for r in rules if r.get("source")]
    if rules_with_source:
        source_items = "".join(
            f'<div style="padding:3px 0;font-size:13px;color:#555;">'
            f'<strong>{escape_html(r.get("name", "Unknown"))}</strong>: '
            f'{escape_html(r.get("source", ""))}</div>'
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


# ============================================================================
# Table / objectives display
# ============================================================================


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


# ============================================================================
# High-level card renderers
# ============================================================================


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
        return f"## {escape_html(name)}"
    mode = card_data.get("mode", "casual")
    seed = card_data.get("seed", 1)
    mode_display = mode.capitalize() if isinstance(mode, str) else "Scenario"
    seed_display = f"#{seed}" if seed else ""
    return f"## {escape_html(mode_display)} Scenario {seed_display}".strip()


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
