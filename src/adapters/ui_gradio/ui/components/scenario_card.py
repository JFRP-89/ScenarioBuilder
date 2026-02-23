"""Scenario card component for list views.

Renders a compact card summary with a mini SVG preview (always square)
and action buttons (View, Favorite). Used in home, list, and favorites pages.
"""

from __future__ import annotations

import html
from typing import Any

from adapters.ui_gradio.constants import CM_PER_FOOT, CM_PER_INCH


# ============================================================================
# Unit conversion helpers (simplified for game use)
# ============================================================================
def mm_to_cm(mm: float) -> float:
    """Convert millimeters to centimeters."""
    return mm / 10


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches (simplified: 1 inch = 2.5 cm = 25 mm)."""
    return float(mm / (CM_PER_INCH * 10))  # CM_PER_INCH * 10 = mm per inch


def mm_to_feet(mm: float) -> float:
    """Convert millimeters to feet (simplified: 1 foot = 30 cm = 300 mm)."""
    return float(mm / (CM_PER_FOOT * 10))  # CM_PER_FOOT * 10 = mm per foot


def format_dimensions(width_mm: int, height_mm: int, unit: str = "cm") -> str:
    """Format table dimensions in the specified unit.

    Uses simplified conversions for game purposes (from constants):
    - 1 inch = {CM_PER_INCH} cm
    - 1 foot = {CM_PER_FOOT} cm

    Args:
        width_mm: Width in millimeters.
        height_mm: Height in millimeters.
        unit: Target unit ('cm', 'in', 'ft').

    Returns:
        Formatted string like "120x120 cm" or "48x48 in".
    """
    if unit == "in":
        w = mm_to_inches(width_mm)
        h = mm_to_inches(height_mm)
        # Use integer if no decimals, otherwise 1 decimal
        if w == int(w) and h == int(h):
            return f"{int(w)}x{int(h)} in"
        return f"{w:.1f}x{h:.1f} in"
    elif unit == "ft":
        w = mm_to_feet(width_mm)
        h = mm_to_feet(height_mm)
        # Use integer if no decimals, otherwise 1 decimal
        if w == int(w) and h == int(h):
            return f"{int(w)}x{int(h)} ft"
        return f"{w:.1f}x{h:.1f} ft"
    else:  # default: cm
        w = mm_to_cm(width_mm)
        h = mm_to_cm(height_mm)
        # Always integer for cm (120 cm, not 120.0 cm)
        return f"{int(w)}x{int(h)} cm"


# ============================================================================
# Mini-SVG helper
# ============================================================================
def make_square_placeholder(size_px: int = 100) -> str:
    """Create a placeholder with a '?' icon for card previews.

    This placeholder will be used until custom images are implemented.

    Args:
        size_px: Side length (px) for the square container.

    Returns:
        HTML string with a placeholder icon.
    """
    return (
        f'<div class="sb-thumb" style="width:{size_px}px;height:{size_px}px;">'
        '<span class="sb-thumb__placeholder">?</span>'
        "</div>"
    )


def make_thumb_frame(svg_content: str, size_px: int = 100) -> str:
    """Wrap an SVG string in a fixed-size thumbnail frame.

    The SVG is scaled to fit within the square while preserving aspect ratio.

    Args:
        svg_content: Raw SVG markup to embed.
        size_px: Side length (px) for the square container.

    Returns:
        HTML string with the SVG embedded in a dark frame.
    """
    if not svg_content or not svg_content.strip():
        return make_square_placeholder(size_px)
    return (
        f'<div class="sb-thumb" style="width:{size_px}px;height:{size_px}px;">'
        f'<div class="sb-thumb__inner">'
        f"{svg_content}"
        "</div></div>"
    )


# ============================================================================
# Card HTML helpers (extracted to reduce cognitive complexity)
# ============================================================================
def _build_actions_html(card_id: str, fav_icon: str) -> str:
    """Build the View + Favorite action buttons HTML for a card."""
    fav_class = "sb-card__fav--active" if fav_icon == "★" else "sb-card__fav--inactive"
    toggle_js = (
        "(function(btn){"
        "var isFav=btn.textContent.trim()==='★';"
        "if(isFav){btn.textContent='☆';btn.className='sb-card__fav sb-card__fav--inactive';}"
        "else{btn.textContent='★';btn.className='sb-card__fav sb-card__fav--active';}"
        "var favPage=document.getElementById('page-favorites');"
        "if(favPage && favPage.contains(btn)){"
        "var style=window.getComputedStyle(favPage);"
        "if(style.display!=='none' && isFav){"
        "var card=btn.closest('[data-card-id]');if(card)card.remove();"
        "}}"
        "var inp=document.querySelector('#fav-toggle-card-id textarea,#fav-toggle-card-id input');"
        "if(inp){inp.value=btn.getAttribute('data-card-id')||'';"
        "inp.dispatchEvent(new Event('input',{bubbles:true}));}"
        "setTimeout(function(){var btn2=document.querySelector('#fav-toggle-btn');"
        "if(btn2)btn2.click();},0);"
        "})(this)"
    )
    return (
        '<div class="sb-card__actions">'
        f'<button class="sb-btn sb-btn--secondary sb-btn--sm card-view-btn" '
        f'data-card-id="{card_id}" '
        'onclick="(function(btn){'
        "var inp=document.querySelector('#view-card-id textarea,#view-card-id input');"
        "if(inp){inp.value=btn.getAttribute('data-card-id')||'';"
        "inp.dispatchEvent(new Event('input',{bubbles:true}));}"
        "setTimeout(function(){var btn2=document.querySelector('#view-card-btn');"
        "if(btn2)btn2.click();},0);"
        '})(this)">'
        "View</button>"
        f'<span class="sb-card__fav {fav_class}" data-card-id="{card_id}" '
        f'title="Toggle favorite" '
        f'onclick="{toggle_js}">{fav_icon}</span>'
        "</div>"
    )


def _build_display_name(name: str, mode: str, seed: str) -> str:
    """Derive the display name from card fields."""
    if name and name.strip():
        return name
    mode_display = mode.capitalize() if isinstance(mode, str) else "Scenario"
    seed_display = f"#{seed}" if seed and seed != "—" else ""
    return f"{mode_display} Scenario {seed_display}".strip()


def _extract_table_dimensions(
    card: dict[str, Any],
) -> tuple[int, int]:
    """Return (width_mm, height_mm) from card's table_mm dict."""
    table_mm = card.get("table_mm", {})
    if isinstance(table_mm, dict):
        return table_mm.get("width_mm", 0), table_mm.get("height_mm", 0)
    return 0, 0


# ============================================================================
# Card HTML renderer
# ============================================================================
def render_card_html(
    card: dict[str, Any],
    *,
    svg_preview: str = "",
    is_favorite: bool = False,
    show_actions: bool = True,
    unit: str = "cm",
) -> str:
    """Render a scenario card summary as styled HTML.

    Args:
        card: Card dict with at least ``card_id``, ``owner_id``, ``mode``.
        svg_preview: Pre-rendered SVG HTML (from ``make_square_svg_preview``).
        is_favorite: Whether the card is in the user's favorites.
        show_actions: Whether to show action buttons.
        unit: Unit for displaying dimensions ('cm', 'in', 'ft').

    Returns:
        HTML string for the card.
    """
    card_id = html.escape(str(card.get("card_id", "???")), quote=True)
    name = html.escape(str(card.get("name", "")), quote=True)
    mode = html.escape(str(card.get("mode", "—")), quote=True)
    owner = html.escape(str(card.get("owner_id", "—")), quote=True)
    visibility = html.escape(str(card.get("visibility", "private")), quote=True)
    seed = html.escape(str(card.get("seed", "—")), quote=True)

    width_mm, height_mm = _extract_table_dimensions(card)
    table_info = (
        format_dimensions(width_mm, height_mm, unit) if width_mm and height_mm else ""
    )

    fav_icon = "★" if is_favorite else "☆"

    preview_html = svg_preview or make_square_placeholder(100)
    actions_html = _build_actions_html(card_id, fav_icon) if show_actions else ""
    display_name = _build_display_name(name, mode, seed)

    return (
        f'<div data-card-id="{card_id}" class="sb-card">'
        f"{preview_html}"
        '<div class="sb-card__body">'
        f'<div class="sb-card__title">{display_name}</div>'
        f'<div class="sb-card__meta">'
        f"Mode: {mode} · Seed: "
        f'<span class="sb-card__seed">{seed}</span>'
        + (f" · Table: {table_info}" if table_info else "")
        + "</div>"
        + f'<div class="sb-card__sub">'
        f"Owner: {owner} · {visibility}</div>"
        f"{actions_html}"
        "</div>"
        "</div>"
    )


def render_card_list_html(
    cards: list[dict[str, Any]],
    *,
    favorite_ids: set[str] | None = None,
    unit: str = "cm",
    actor_id: str = "",
) -> str:
    """Render a list of scenario cards as HTML.

    Args:
        cards: List of card dicts.
        favorite_ids: Set of card IDs that are favorites.
        unit: Unit for displaying dimensions ('cm', 'in', 'ft').
        actor_id: Actor ID for SVG thumbnail rendering.

    Returns:
        Combined HTML for all cards, or an empty-state message.
    """
    if not cards:
        return (
            '<div class="sb-empty">'
            '<div class="sb-empty__icon">📭</div>'
            "No scenarios found.</div>"
        )
    fav_ids = favorite_ids or set()

    # Lazy-import to avoid circular dependency at module level
    from adapters.ui_gradio.services.navigation import get_card_svg_thumb

    fragments: list[str] = []
    for card in cards:
        cid = card.get("card_id", "")
        # Generate SVG thumbnail (falls back to placeholder on error)
        if actor_id and cid:
            svg_raw = get_card_svg_thumb(actor_id, cid)
            thumb = make_thumb_frame(svg_raw, 100)
        else:
            thumb = make_square_placeholder(100)
        fragments.append(
            render_card_html(
                card,
                svg_preview=thumb,
                is_favorite=cid in fav_ids,
                unit=unit,
            )
        )
    return "\n".join(fragments)
