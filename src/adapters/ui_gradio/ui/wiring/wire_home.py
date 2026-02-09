"""Home-page wiring — loads recent cards on page arrival with pagination.

Calls the Flask API via ``services.navigation`` and renders results
using the ``scenario_card`` component.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.scenario_card import render_card_list_html

# Cards per page
CARDS_PER_PAGE = 6


def _filter_cards(
    cards: list[dict[str, Any]],
    mode_filter: str,
    preset_filter: str,
) -> list[dict[str, Any]]:
    filtered = cards
    if mode_filter != "All":
        filtered = [
            c for c in filtered if c.get("mode", "").lower() == mode_filter.lower()
        ]
    if preset_filter != "All":
        filtered = [
            c
            for c in filtered
            if c.get("table_preset", "").lower() == preset_filter.lower()
        ]
    return filtered


def _render_page(
    cards: list[dict[str, Any]],
    fav_ids: list[str],
    unit: str,
    page: int,
) -> tuple[str, str, int]:
    if not cards:
        empty_html = (
            '<div style="text-align:center;color:#999;padding:30px 0;">'
            "No scenarios match the selected filters.</div>"
        )
        return empty_html, '<div style="text-align:center">Page 1 of 1</div>', 1

    total_cards = len(cards)
    total_pages = (total_cards + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * CARDS_PER_PAGE
    end_idx = start_idx + CARDS_PER_PAGE
    page_cards = cards[start_idx:end_idx]

    html: str = render_card_list_html(page_cards, favorite_ids=set(fav_ids), unit=unit)
    page_info = (
        f'<div style="text-align:center;padding:10px 0;">'
        f"Page {page} of {total_pages} ({total_cards} scenarios)"
        f"</div>"
    )
    return html, page_info, page


def load_recent_cards(
    mode_filter: str = "All",
    preset_filter: str = "All",
    unit: str = "cm",
    page: int = 1,
) -> tuple[str, str, int, list[dict[str, Any]], list[str]]:
    """Fetch cards from Flask and render as HTML with pagination.

    Args:
        mode_filter: Game mode filter ("All", "Casual", "Narrative", "Matched").
        preset_filter: Table preset filter ("All", "Standard", "Massive", "Custom").
        unit: Unit for displaying dimensions ('cm', 'in', 'ft').
        page: Current page number (1-indexed).

    Returns:
        Tuple of (html, page_info, new_page) where:
        - html: HTML string with the card list
        - page_info: HTML with page information
        - new_page: Updated page number
    """
    actor_id = get_default_actor_id()
    result = nav_svc.list_cards(actor_id, "public")

    if result.get("status") == "error":
        error_html = (
            '<div style="color:red;padding:20px;">'
            f'Error: {result.get("message", "Unknown error")}</div>'
        )
        return error_html, '<div style="text-align:center">Page 1</div>', 1, [], []

    cards: list[dict[str, Any]] = result.get("cards", [])
    fav_result = nav_svc.list_favorites(actor_id)
    fav_ids = fav_result.get("card_ids", [])

    filtered = _filter_cards(cards, mode_filter, preset_filter)
    html, page_info, new_page = _render_page(filtered, fav_ids, unit, page)
    return html, page_info, new_page, cards, fav_ids


def render_from_cache(
    mode_filter: str,
    preset_filter: str,
    unit: str,
    page: int,
    cards_cache: list[dict[str, Any]],
    fav_ids_cache: list[str],
) -> tuple[str, str, int]:
    filtered = _filter_cards(cards_cache, mode_filter, preset_filter)
    return _render_page(filtered, fav_ids_cache, unit, page)


def go_to_previous_page(
    mode_filter: str,
    preset_filter: str,
    unit: str,
    current_page: int,
    cards_cache: list[dict[str, Any]],
    fav_ids_cache: list[str],
) -> tuple[str, str, int]:
    """Navigate to previous page.

    Args:
        mode_filter: Game mode filter
        preset_filter: Table preset filter
        unit: Display unit for dimensions
        current_page: Current page number

    Returns:
        Tuple of (html, page_info, new_page)
    """
    new_page = max(1, current_page - 1)
    return render_from_cache(
        mode_filter, preset_filter, unit, new_page, cards_cache, fav_ids_cache
    )


def go_to_next_page(
    mode_filter: str,
    preset_filter: str,
    unit: str,
    current_page: int,
    cards_cache: list[dict[str, Any]],
    fav_ids_cache: list[str],
) -> tuple[str, str, int]:
    """Navigate to next page.

    Args:
        mode_filter: Game mode filter
        preset_filter: Table preset filter
        unit: Display unit for dimensions
        current_page: Current page number

    Returns:
        Tuple of (html, page_info, new_page)
    """
    new_page = current_page + 1
    return render_from_cache(
        mode_filter, preset_filter, unit, new_page, cards_cache, fav_ids_cache
    )


def wire_home_page(
    *,
    home_recent_html: gr.HTML,
    home_mode_filter: gr.Radio,
    home_preset_filter: gr.Radio,
    home_unit_selector: gr.Radio,
    home_reload_btn: gr.Button,
    home_prev_btn: gr.Button,
    home_page_info: gr.HTML,
    home_next_btn: gr.Button,
    home_page_state: gr.State,
    home_cards_cache_state: gr.State,
    home_fav_ids_cache_state: gr.State,
    app: gr.Blocks,
) -> None:
    """Wire the home page to load recent cards with pagination and filters."""
    # Load cards on initial page load
    app.load(
        fn=load_recent_cards,
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_page_state,
        ],
        outputs=[
            home_recent_html,
            home_page_info,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
    )

    # Reload cards when mode filter changes (reset to page 1)
    home_mode_filter.change(
        fn=lambda mode, preset, unit, cards, fav_ids: render_from_cache(
            mode, preset, unit, 1, cards, fav_ids
        ),
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
        outputs=[home_recent_html, home_page_info, home_page_state],
    )

    # Reload cards when preset filter changes (reset to page 1)
    home_preset_filter.change(
        fn=lambda mode, preset, unit, cards, fav_ids: render_from_cache(
            mode, preset, unit, 1, cards, fav_ids
        ),
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
        outputs=[home_recent_html, home_page_info, home_page_state],
    )

    # Reload cards when unit changes (reset to page 1)
    home_unit_selector.change(
        fn=lambda mode, preset, unit, page, cards, fav_ids: render_from_cache(
            mode, preset, unit, page, cards, fav_ids
        ),
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
        outputs=[home_recent_html, home_page_info, home_page_state],
    )

    # Reload cards on demand (keep current page)
    home_reload_btn.click(
        fn=load_recent_cards,
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_page_state,
        ],
        outputs=[
            home_recent_html,
            home_page_info,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
    )

    # Previous page button
    home_prev_btn.click(
        fn=go_to_previous_page,
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
        outputs=[home_recent_html, home_page_info, home_page_state],
    )

    # Next page button
    home_next_btn.click(
        fn=go_to_next_page,
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
        outputs=[home_recent_html, home_page_info, home_page_state],
    )
