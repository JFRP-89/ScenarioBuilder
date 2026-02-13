"""Shared helpers for search and pagination across listing pages.

Security: all user-supplied search strings are sanitized before use
to prevent XSS / injection in rendered HTML.
"""

from __future__ import annotations

import html
import re
from typing import Any

from adapters.ui_gradio.ui.components.scenario_card import render_card_list_html

# ── Per-page options ─────────────────────────────────────────────
ITEMS_PER_PAGE_CHOICES: list[int] = [5, 10, 20, 50, 100]
DEFAULT_ITEMS_PER_PAGE: int = 10
_ALLOWED_PER_PAGE: frozenset[int] = frozenset(ITEMS_PER_PAGE_CHOICES)

# Regex that strips both complete (<tag>) and incomplete (<tag) HTML fragments.
_HTML_TAG_RE = re.compile(r"<[^>]*>?")

_MAX_QUERY_LENGTH = 200


# ── Sanitization ─────────────────────────────────────────────────


def _coerce_to_str(value: object) -> str:
    """Safely coerce *value* to ``str`` for escaping.

    ``None``, ``bool``, ``list``, ``dict`` and other non-string types are
    converted without raising.  The result is always a plain ``str``.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def escape_html(text: str) -> str:
    """HTML-escape a string for safe rendering inside HTML elements.

    Thin wrapper around :func:`html.escape` to centralise the call-site
    and guarantee ``quote=True`` everywhere.
    """
    if not isinstance(text, str):
        return ""
    return html.escape(text, quote=True)


def escape_html_attr(value: object) -> str:
    """Escape *value* for safe use inside an HTML **attribute**.

    Handles ``None``, non-string types, and ensures ``"`` and ``'`` are
    encoded so the value cannot break out of a quoted attribute.
    """
    return html.escape(_coerce_to_str(value), quote=True)


def escape_svg_text(value: object) -> str:
    """Escape *value* for safe use inside an SVG ``<text>`` node.

    Equivalent to :func:`escape_html_attr` (XML escaping is identical)
    but named separately for semantic clarity at call-sites.
    """
    return html.escape(_coerce_to_str(value), quote=True)


def escape_svg_attr(value: object) -> str:
    """Escape *value* for safe use inside an SVG attribute.

    Prevents break-out of quoted attribute values in SVG tags.
    """
    return html.escape(_coerce_to_str(value), quote=True)


def sanitize_search_query(raw: str) -> str:
    """Sanitize user search input.

    - Strips leading/trailing whitespace
    - Removes any HTML tags (including incomplete fragments)
    - HTML-escapes special characters
    - Limits length to 200 chars
    """
    if not raw or not isinstance(raw, str):
        return ""
    text = raw.strip()
    # Remove HTML tags (complete and incomplete)
    text = _HTML_TAG_RE.sub("", text)
    # Escape remaining special HTML chars
    text = escape_html(text)
    # Limit length
    return text[:_MAX_QUERY_LENGTH]


def filter_cards_by_name(
    cards: list[dict[str, Any]],
    search_query: str,
) -> list[dict[str, Any]]:
    """Filter cards by name using case-insensitive substring match.

    The *search_query* should already be sanitized.  The match is done
    against the raw ``name`` field of each card (before HTML escaping)
    so we un-escape the query first for a fair comparison.
    """
    if not search_query:
        return cards

    # Un-escape for matching against raw card data
    query_lower = html.unescape(search_query).lower()

    return [c for c in cards if query_lower in (c.get("name") or "").lower()]


# ── Mode / preset filtering ──────────────────────────────────────


def filter_by_mode_preset(
    cards: list[dict[str, Any]],
    mode_filter: str = "All",
    preset_filter: str = "All",
) -> list[dict[str, Any]]:
    """Filter cards by game mode and/or table preset.

    Comparison is case-insensitive.  The sentinel ``"All"`` skips
    that filtering dimension.
    """
    filtered = cards
    if mode_filter != "All":
        mode_lower = mode_filter.lower()
        filtered = [c for c in filtered if c.get("mode", "").lower() == mode_lower]
    if preset_filter != "All":
        preset_lower = preset_filter.lower()
        filtered = [
            c for c in filtered if c.get("table_preset", "").lower() == preset_lower
        ]
    return filtered


# ── Per-page parsing ─────────────────────────────────────────────


def parse_per_page(raw: str | int) -> int:
    """Parse a per-page value with whitelist validation.

    Returns *DEFAULT_ITEMS_PER_PAGE* when the value is not in the
    allowed set ``ITEMS_PER_PAGE_CHOICES``.
    """
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_ITEMS_PER_PAGE
    return val if val in _ALLOWED_PER_PAGE else DEFAULT_ITEMS_PER_PAGE


# ── Page number validation ───────────────────────────────────────


def validate_page(raw: Any) -> int:
    """Coerce *raw* into a valid page number (≥ 1).

    Gradio ``gr.State`` can deliver ``None``, floats, or strings in edge
    cases (e.g. first load, corrupted state).  This function guarantees a
    safe ``int ≥ 1`` in every case.
    """
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return 1
    return max(1, val)


# ── Pagination rendering ─────────────────────────────────────────

_EMPTY_PAGE_INFO = '<div style="text-align:center">Page 1 of 1</div>'


def render_page(
    cards: list[dict[str, Any]],
    fav_ids: list[str],
    unit: str,
    page: int,
    per_page: int = DEFAULT_ITEMS_PER_PAGE,
    *,
    empty_message: str = "No scenarios match the selected filters.",
    count_label: str = "scenarios",
) -> tuple[str, str, int]:
    """Paginate *cards* and render the current page as HTML.

    Returns ``(cards_html, page_info_html, clamped_page_number)``.
    """
    if not cards:
        safe_msg = escape_html(empty_message)
        empty_html = (
            f'<div style="text-align:center;color:#999;padding:30px 0;">'
            f"{safe_msg}</div>"
        )
        return empty_html, _EMPTY_PAGE_INFO, 1

    total_cards = len(cards)
    total_pages = max(1, (total_cards + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_cards = cards[start_idx:end_idx]

    cards_html: str = render_card_list_html(
        page_cards, favorite_ids=set(fav_ids), unit=unit
    )
    safe_label = escape_html(count_label)
    page_info = (
        f'<div style="text-align:center;padding:10px 0;">'
        f"Page {page} of {total_pages} ({total_cards} {safe_label})"
        f"</div>"
    )
    return cards_html, page_info, page


# ── Composite pipeline ───────────────────────────────────────────


def render_filtered_page(
    cards: list[dict[str, Any]],
    fav_ids: list[str],
    unit: str,
    page: Any,
    search_raw: str = "",
    per_page_raw: str | int = "10",
    *,
    empty_message: str = "No scenarios match the selected filters.",
    count_label: str = "scenarios",
) -> tuple[str, str, int]:
    """Sanitise, filter, paginate and render cards in one call.

    Composes :func:`sanitize_search_query`, :func:`filter_cards_by_name`,
    :func:`parse_per_page`, :func:`validate_page` and :func:`render_page`
    so that wiring modules need a single function call instead of
    repeating the four-step pipeline.
    """
    query = sanitize_search_query(search_raw)
    filtered = filter_cards_by_name(cards, query)
    per_page = parse_per_page(per_page_raw)
    return render_page(
        filtered,
        fav_ids,
        unit,
        validate_page(page),
        per_page,
        empty_message=empty_message,
        count_label=count_label,
    )
