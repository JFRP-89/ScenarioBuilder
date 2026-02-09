"""List-page wiring — loads cards when filter changes.

Calls the Flask API via ``services.navigation`` and renders results
using the ``scenario_card`` component.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.scenario_card import render_card_list_html
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
    list_reload_btn: gr.Button,
    list_cards_html: gr.HTML,
    # Home buttons that also trigger list load
    home_browse_btn: gr.Button,
    # Cache states
    list_cards_cache_state: gr.State,
    list_fav_ids_cache_state: gr.State,
    list_loaded_state: gr.State,
) -> None:
    """Wire the list page interactions."""

    def _refresh_cache(
        filter_value: str, unit: str = "cm"
    ) -> tuple[str, dict[str, list[dict[str, Any]]], list[str], bool]:
        """Fetch cards for all filters and render current filter.

        Returns:
            Tuple of (html, cache, fav_ids).
        """
        actor_id = get_default_actor_id()
        cache: dict[str, list[dict[str, Any]]] = {}
        for key in ["mine", "shared_with_me"]:
            result = nav_svc.list_cards(actor_id, key)
            cache[key] = (
                result.get("cards", []) if result.get("status") != "error" else []
            )

        fav_result = nav_svc.list_favorites(actor_id)
        fav_ids = fav_result.get("card_ids", [])

        html: str = render_card_list_html(
            cache.get(filter_value, []), favorite_ids=set(fav_ids), unit=unit
        )
        return html, cache, fav_ids, True

    def _render_from_cache(
        filter_value: str,
        unit: str,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
    ) -> str:
        cards = cache.get(filter_value, []) if isinstance(cache, dict) else []
        return str(render_card_list_html(cards, favorite_ids=set(fav_ids), unit=unit))

    # Reload cards when filter changes
    list_filter.change(
        fn=_render_from_cache,
        inputs=[
            list_filter,
            list_unit_selector,
            list_cards_cache_state,
            list_fav_ids_cache_state,
        ],
        outputs=[list_cards_html],
    )

    # Reload cards when unit changes
    list_unit_selector.change(
        fn=_render_from_cache,
        inputs=[
            list_filter,
            list_unit_selector,
            list_cards_cache_state,
            list_fav_ids_cache_state,
        ],
        outputs=[list_cards_html],
    )

    # Reload cards on demand
    list_reload_btn.click(
        fn=_refresh_cache,
        inputs=[list_filter, list_unit_selector],
        outputs=[
            list_cards_html,
            list_cards_cache_state,
            list_fav_ids_cache_state,
            list_loaded_state,
        ],
    )

    # Also load cards when navigating to list page from home
    def _navigate_and_load(
        loaded: bool,
        filter_value: str,
        unit: str,
        cache: dict[str, list[dict[str, Any]]],
        fav_ids: list[str],
    ):
        nav = navigate_to(PAGE_LIST)
        if loaded:
            html = _render_from_cache(filter_value, unit, cache, fav_ids)
            return (*nav, filter_value, html, cache, fav_ids, loaded)
        html, new_cache, new_fav_ids, loaded_flag = _refresh_cache("mine", "cm")
        return (*nav, "mine", html, new_cache, new_fav_ids, loaded_flag)

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
            list_cards_cache_state,
            list_fav_ids_cache_state,
            list_loaded_state,
        ],
    )
