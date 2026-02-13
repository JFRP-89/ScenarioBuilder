"""Home-page wiring — loads recent cards on page arrival with pagination.

Calls the Flask API via ``services.navigation`` and renders results
using the ``scenario_card`` component.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.search_helpers import (
    escape_html,
    filter_by_mode_preset,
    render_filtered_page,
)


def load_recent_cards(
    mode_filter: str = "All",
    preset_filter: str = "All",
    unit: str = "cm",
    page: int = 1,
    search_raw: str = "",
    per_page_raw: str = "10",
) -> tuple[str, str, int, list[dict[str, Any]], list[str]]:
    """Fetch cards from Flask and render as HTML with pagination."""
    actor_id = get_default_actor_id()
    result = nav_svc.list_cards(actor_id, "public")

    if result.get("status") == "error":
        safe_msg = escape_html(result.get("message", "Unknown error"))
        error_html = '<div style="color:red;padding:20px;">' f"Error: {safe_msg}</div>"
        return error_html, '<div style="text-align:center">Page 1</div>', 1, [], []

    cards: list[dict[str, Any]] = result.get("cards", [])
    fav_result = nav_svc.list_favorites(actor_id)
    fav_ids = fav_result.get("card_ids", [])

    filtered = filter_by_mode_preset(cards, mode_filter, preset_filter)
    html, page_info, new_page = render_filtered_page(
        filtered, fav_ids, unit, page, search_raw, per_page_raw
    )
    return html, page_info, new_page, cards, fav_ids


def render_from_cache(
    mode_filter: str,
    preset_filter: str,
    unit: str,
    page: int,
    cards_cache: list[dict[str, Any]],
    fav_ids_cache: list[str],
    search_raw: str = "",
    per_page_raw: str = "10",
) -> tuple[str, str, int]:
    """Re-render from cached cards without hitting the API."""
    filtered = filter_by_mode_preset(cards_cache, mode_filter, preset_filter)
    return render_filtered_page(  # type: ignore[no-any-return]
        filtered, fav_ids_cache, unit, page, search_raw, per_page_raw
    )


def go_to_previous_page(
    mode_filter: str,
    preset_filter: str,
    unit: str,
    current_page: int,
    cards_cache: list[dict[str, Any]],
    fav_ids_cache: list[str],
    search_raw: str = "",
    per_page_raw: str = "10",
) -> tuple[str, str, int]:
    """Navigate to the previous page."""
    return render_from_cache(
        mode_filter,
        preset_filter,
        unit,
        max(1, current_page - 1),
        cards_cache,
        fav_ids_cache,
        search_raw,
        per_page_raw,
    )


def go_to_next_page(
    mode_filter: str,
    preset_filter: str,
    unit: str,
    current_page: int,
    cards_cache: list[dict[str, Any]],
    fav_ids_cache: list[str],
    search_raw: str = "",
    per_page_raw: str = "10",
) -> tuple[str, str, int]:
    """Navigate to the next page."""
    return render_from_cache(
        mode_filter,
        preset_filter,
        unit,
        current_page + 1,
        cards_cache,
        fav_ids_cache,
        search_raw,
        per_page_raw,
    )


def wire_home_page(
    *,
    home_recent_html: gr.HTML,
    home_mode_filter: gr.Radio,
    home_preset_filter: gr.Radio,
    home_unit_selector: gr.Radio,
    home_search_box: gr.Textbox,
    home_per_page_dropdown: gr.Dropdown,
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
    _all_inputs = [
        home_mode_filter,
        home_preset_filter,
        home_unit_selector,
        home_page_state,
        home_search_box,
        home_per_page_dropdown,
    ]
    _cache_inputs = [
        home_mode_filter,
        home_preset_filter,
        home_unit_selector,
        home_page_state,
        home_cards_cache_state,
        home_fav_ids_cache_state,
        home_search_box,
        home_per_page_dropdown,
    ]
    _page_outputs = [home_recent_html, home_page_info, home_page_state]
    _full_outputs = [
        home_recent_html,
        home_page_info,
        home_page_state,
        home_cards_cache_state,
        home_fav_ids_cache_state,
    ]

    # Load cards on initial page load
    app.load(fn=load_recent_cards, inputs=_all_inputs, outputs=_full_outputs)

    # Filter changes → reset to page 1 from cache
    def _cache_reset_page1(
        mode: str,
        preset: str,
        unit: str,
        _page: int,
        cards: list[dict[str, Any]],
        fav_ids: list[str],
        search: str,
        per_page: str,
    ) -> tuple[str, str, int]:
        return render_from_cache(
            mode, preset, unit, 1, cards, fav_ids, search, per_page
        )

    for widget in (
        home_mode_filter,
        home_preset_filter,
        home_search_box,
        home_per_page_dropdown,
    ):
        widget.change(
            fn=_cache_reset_page1,
            inputs=_cache_inputs,
            outputs=_page_outputs,
        )

    # Unit change keeps current page
    home_unit_selector.change(
        fn=render_from_cache,
        inputs=_cache_inputs,
        outputs=_page_outputs,
    )

    # Reload from API
    home_reload_btn.click(
        fn=load_recent_cards,
        inputs=_all_inputs,
        outputs=_full_outputs,
    )

    # Pagination
    home_prev_btn.click(
        fn=go_to_previous_page,
        inputs=_cache_inputs,
        outputs=_page_outputs,
    )
    home_next_btn.click(
        fn=go_to_next_page,
        inputs=_cache_inputs,
        outputs=_page_outputs,
    )
