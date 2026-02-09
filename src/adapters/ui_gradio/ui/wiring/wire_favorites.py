"""Favorites-page wiring — loads favorite cards on page visit.

Fetches favorite IDs, then gets card data for each.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.scenario_card import render_card_list_html
from adapters.ui_gradio.ui.router import PAGE_FAVORITES, navigate_to


def wire_favorites_page(
    *,
    page_state: gr.State,
    page_containers: list[gr.Column],
    # Favorites page widgets
    favorites_unit_selector: gr.Radio,
    favorites_reload_btn: gr.Button,
    favorites_cards_html: gr.HTML,
    # Home favorites button (trigger load on click)
    home_favorites_btn: gr.Button,
    # Cache states
    favorites_cards_cache_state: gr.State,
    favorites_fav_ids_cache_state: gr.State,
    favorites_loaded_state: gr.State,
) -> None:
    """Wire the favorites page interactions."""

    def _refresh_cache(
        unit: str = "cm",
    ) -> tuple[str, list[dict[str, Any]], list[str], bool]:
        """Fetch favorites and render as HTML.

        Args:
            unit: Unit for displaying dimensions ('cm', 'in', 'ft').

        Returns:
            Tuple of (html, cards_cache, fav_ids_cache).
        """
        actor_id = get_default_actor_id()
        fav_result = nav_svc.list_favorites(actor_id)

        if fav_result.get("status") == "error":
            return (
                (
                    f'<div style="color:red;padding:20px;">'
                    f'Error: {fav_result.get("message", "Unknown error")}</div>'
                ),
                [],
                [],
                True,
            )

        card_ids = fav_result.get("card_ids", [])
        if not card_ids:
            return (
                (
                    '<div style="text-align:center;color:#999;padding:40px 0;">'
                    "No favorites yet. Browse scenarios and ⭐ your favorites!"
                    "</div>"
                ),
                [],
                [],
                True,
            )

        # Fetch card data for each favorite
        cards: list[dict[str, Any]] = []
        for cid in card_ids:
            card_data = nav_svc.get_card(actor_id, cid)
            if card_data.get("status") != "error":
                cards.append(card_data)

        # Render cards with selected unit
        fav_ids = set(card_ids)
        html: str = render_card_list_html(cards, favorite_ids=fav_ids, unit=unit)
        return html, cards, list(fav_ids), True

    def _render_from_cache(
        unit: str,
        cards_cache: list[dict[str, Any]],
        fav_ids_cache: list[str],
    ) -> str:
        return str(
            render_card_list_html(
                cards_cache, favorite_ids=set(fav_ids_cache), unit=unit
            )
        )

    # Reload favorites when unit changes
    favorites_unit_selector.change(
        fn=_render_from_cache,
        inputs=[
            favorites_unit_selector,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
        ],
        outputs=[favorites_cards_html],
    )

    # Reload favorites on demand
    favorites_reload_btn.click(
        fn=_refresh_cache,
        inputs=[favorites_unit_selector],
        outputs=[
            favorites_cards_html,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
            favorites_loaded_state,
        ],
    )

    # Load favorites when navigating to favorites page
    def _navigate_and_load(
        loaded: bool,
        unit: str,
        cards_cache: list[dict[str, Any]],
        fav_ids: list[str],
    ):
        nav = navigate_to(PAGE_FAVORITES)
        if loaded:
            html = _render_from_cache(unit, cards_cache, fav_ids)
            return (*nav, html, cards_cache, fav_ids, loaded)
        html, new_cards, new_fav_ids, loaded_flag = _refresh_cache("cm")
        return (*nav, html, new_cards, new_fav_ids, loaded_flag)

    home_favorites_btn.click(
        fn=_navigate_and_load,
        inputs=[
            favorites_loaded_state,
            favorites_unit_selector,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
        ],
        outputs=[
            page_state,
            *page_containers,
            favorites_cards_html,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
            favorites_loaded_state,
        ],
    )
