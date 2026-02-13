"""List-page wiring — loads cards when filter changes.

Calls the Flask API via ``services.navigation`` and renders results
using the ``scenario_card`` component.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.search_helpers import (
    render_filtered_page,
)
from adapters.ui_gradio.ui.router import (
    PAGE_LIST,
    navigate_to,
)


def wire_list_page(
    *,
    page_state: gr.State,
    page_containers: list[gr.Column],
    # List page widgets
    list_filter: gr.Radio,
    list_unit_selector: gr.Radio,
    list_search_box: gr.Textbox,
    list_per_page_dropdown: gr.Dropdown,
    list_reload_btn: gr.Button,
    list_cards_html: gr.HTML,
    list_page_info: gr.HTML,
    list_prev_btn: gr.Button,
    list_next_btn: gr.Button,
    list_page_state: gr.State,
    # Home buttons that also trigger list load
    home_browse_btn: gr.Button,
    # Cache states
    list_cards_cache_state: gr.State,
    list_fav_ids_cache_state: gr.State,
    list_loaded_state: gr.State,
) -> None:
    """Wire the list page interactions."""

    def _refresh_cache(
        filter_value: str,
        unit: str = "cm",
        search_raw: str = "",
        per_page_raw: str = "10",
    ) -> tuple[str, str, int, dict[str, list[dict[str, Any]]], list[str], bool]:
        actor_id = get_default_actor_id()
        cache: dict[str, list[dict[str, Any]]] = {}
        for key in ["mine", "shared_with_me"]:
            result = nav_svc.list_cards(actor_id, key)
            cache[key] = (
                result.get("cards", []) if result.get("status") != "error" else []
            )

        fav_result = nav_svc.list_favorites(actor_id)
        fav_ids = fav_result.get("card_ids", [])

        cards = cache.get(filter_value, [])
        html, page_info, new_page = render_filtered_page(
            cards, fav_ids, unit, 1, search_raw, per_page_raw
        )
        return html, page_info, new_page, cache, fav_ids, True

    def _render_from_cache(
        filter_value: str,
        unit: str,
        page: int,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
        search_raw: str = "",
        per_page_raw: str = "10",
    ) -> tuple[str, str, int]:
        cards = cache.get(filter_value, []) if isinstance(cache, dict) else []
        return render_filtered_page(  # type: ignore[no-any-return]
            cards, fav_ids, unit, page, search_raw, per_page_raw
        )

    _cache_inputs = [
        list_filter,
        list_unit_selector,
        list_page_state,
        list_cards_cache_state,
        list_fav_ids_cache_state,
        list_search_box,
        list_per_page_dropdown,
    ]
    _page_outputs = [list_cards_html, list_page_info, list_page_state]

    # Filter / search / per-page changes → reset to page 1
    def _cache_reset_page1(
        filter_value: str,
        unit: str,
        _page: int,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
        search_raw: str,
        per_page_raw: str,
    ) -> tuple[str, str, int]:
        return _render_from_cache(
            filter_value, unit, 1, cache, fav_ids, search_raw, per_page_raw
        )

    for widget in (list_filter, list_search_box, list_per_page_dropdown):
        widget.change(
            fn=_cache_reset_page1,
            inputs=_cache_inputs,
            outputs=_page_outputs,
        )

    # Unit change keeps current page
    list_unit_selector.change(
        fn=_render_from_cache,
        inputs=_cache_inputs,
        outputs=_page_outputs,
    )

    # Refresh button
    list_reload_btn.click(
        fn=_refresh_cache,
        inputs=[
            list_filter,
            list_unit_selector,
            list_search_box,
            list_per_page_dropdown,
        ],
        outputs=[
            list_cards_html,
            list_page_info,
            list_page_state,
            list_cards_cache_state,
            list_fav_ids_cache_state,
            list_loaded_state,
        ],
    )

    # Pagination
    def _go_prev(
        filter_value: str,
        unit: str,
        current_page: int,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
        search_raw: str,
        per_page_raw: str,
    ) -> tuple[str, str, int]:
        return _render_from_cache(
            filter_value,
            unit,
            max(1, current_page - 1),
            cache,
            fav_ids,
            search_raw,
            per_page_raw,
        )

    def _go_next(
        filter_value: str,
        unit: str,
        current_page: int,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
        search_raw: str,
        per_page_raw: str,
    ) -> tuple[str, str, int]:
        return _render_from_cache(
            filter_value,
            unit,
            current_page + 1,
            cache,
            fav_ids,
            search_raw,
            per_page_raw,
        )

    list_prev_btn.click(fn=_go_prev, inputs=_cache_inputs, outputs=_page_outputs)
    list_next_btn.click(fn=_go_next, inputs=_cache_inputs, outputs=_page_outputs)

    # Navigate from home → list page
    def _navigate_and_load(
        loaded: bool,
        filter_value: str,
        unit: str,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
    ):
        nav = navigate_to(PAGE_LIST)
        if loaded:
            html, page_info, new_page = _render_from_cache(
                filter_value, unit, 1, cache, fav_ids
            )
            return (
                *nav,
                filter_value,
                html,
                page_info,
                new_page,
                cache,
                fav_ids,
                loaded,
            )
        (
            html,
            page_info,
            new_page,
            new_cache,
            new_fav_ids,
            loaded_flag,
        ) = _refresh_cache("mine", "cm")
        return (
            *nav,
            "mine",
            html,
            page_info,
            new_page,
            new_cache,
            new_fav_ids,
            loaded_flag,
        )

    home_browse_btn.click(
        fn=_navigate_and_load,
        inputs=[
            list_loaded_state,
            list_filter,
            list_unit_selector,
            list_cards_cache_state,
            list_fav_ids_cache_state,
        ],
        outputs=[
            page_state,
            *page_containers,
            list_filter,
            list_cards_html,
            list_page_info,
            list_page_state,
            list_cards_cache_state,
            list_fav_ids_cache_state,
            list_loaded_state,
        ],
    )
