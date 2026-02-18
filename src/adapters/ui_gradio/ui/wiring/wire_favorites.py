"""Favorites-page wiring — loads favorite cards on page visit.

Fetches favorite IDs, then gets card data for each.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import is_session_valid
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.search_helpers import (
    escape_html,
    render_filtered_page,
)
from adapters.ui_gradio.ui.router import PAGE_FAVORITES, navigate_to


def wire_favorites_page(  # noqa: C901
    *,
    page_state: gr.State,
    page_containers: list[gr.Column],
    # Favorites page widgets
    favorites_unit_selector: gr.Radio,
    favorites_search_box: gr.Textbox,
    favorites_per_page_dropdown: gr.Dropdown,
    favorites_reload_btn: gr.Button,
    favorites_cards_html: gr.HTML,
    favorites_page_info: gr.HTML,
    favorites_prev_btn: gr.Button,
    favorites_next_btn: gr.Button,
    favorites_page_state: gr.State,
    # Home favorites button (trigger load on click)
    home_favorites_btn: gr.Button,
    # Cache states
    favorites_cards_cache_state: gr.State,
    favorites_fav_ids_cache_state: gr.State,
    favorites_loaded_state: gr.State,
    actor_id_state: gr.State | None = None,
    session_id_state: gr.State | None = None,
) -> Any:
    """Wire the favorites page interactions.

    Returns:
        The ``home_favorites_btn.click`` event ``Dependency``.
    """
    n_containers = len(page_containers)

    def _refresh_cache(
        unit: str = "cm",
        search_raw: str = "",
        per_page_raw: str = "10",
        actor_id: str = "",
    ) -> tuple[str, str, int, list[dict[str, Any]], list[str], bool]:
        if not actor_id:
            actor_id = get_default_actor_id()
        fav_result = nav_svc.list_favorites(actor_id)

        if fav_result.get("status") == "error":
            safe_msg = escape_html(fav_result.get("message", "Unknown error"))
            err_html = (
                f'<div style="color:red;padding:20px;">' f"Error: {safe_msg}</div>"
            )
            return (
                err_html,
                '<div style="text-align:center">Page 1 of 1</div>',
                1,
                [],
                [],
                True,
            )

        card_ids = fav_result.get("card_ids", [])
        if not card_ids:
            empty_html = (
                '<div style="text-align:center;color:#999;padding:40px 0;">'
                "No favorites yet. Browse scenarios and ⭐ your favorites!"
                "</div>"
            )
            return (
                empty_html,
                '<div style="text-align:center">Page 1 of 1</div>',
                1,
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

        fav_ids = list(card_ids)
        html, page_info, new_page = render_filtered_page(
            cards,
            fav_ids,
            unit,
            1,
            search_raw,
            per_page_raw,
            count_label="favorites",
        )
        return html, page_info, new_page, cards, fav_ids, True

    def _render_from_cache(
        unit: str,
        page: int,
        cards_cache: list[dict[str, Any]],
        fav_ids_cache: list[str],
        search_raw: str = "",
        per_page_raw: str = "10",
    ) -> tuple[str, str, int]:
        return render_filtered_page(
            cards_cache,
            fav_ids_cache,
            unit,
            page,
            search_raw,
            per_page_raw,
            count_label="favorites",
        )

    _cache_inputs = [
        favorites_unit_selector,
        favorites_page_state,
        favorites_cards_cache_state,
        favorites_fav_ids_cache_state,
        favorites_search_box,
        favorites_per_page_dropdown,
    ]
    _page_outputs = [favorites_cards_html, favorites_page_info, favorites_page_state]

    # Search / per-page changes → reset to page 1
    def _cache_reset_page1(
        unit: str,
        _page: int,
        cards_cache: list[dict[str, Any]],
        fav_ids_cache: list[str],
        search_raw: str,
        per_page_raw: str,
    ) -> tuple[str, str, int]:
        return _render_from_cache(
            unit, 1, cards_cache, fav_ids_cache, search_raw, per_page_raw
        )

    for widget in (favorites_search_box, favorites_per_page_dropdown):
        widget.change(
            fn=_cache_reset_page1,
            inputs=_cache_inputs,
            outputs=_page_outputs,
        )

    # Unit change keeps current page
    favorites_unit_selector.change(
        fn=_render_from_cache,
        inputs=_cache_inputs,
        outputs=_page_outputs,
    )

    # Reload favorites on demand
    _refresh_inputs: list[gr.components.Component] = [
        favorites_unit_selector,
        favorites_search_box,
        favorites_per_page_dropdown,
    ]
    if actor_id_state is not None:
        _refresh_inputs.append(actor_id_state)

    favorites_reload_btn.click(
        fn=_refresh_cache,
        inputs=_refresh_inputs,
        outputs=[
            favorites_cards_html,
            favorites_page_info,
            favorites_page_state,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
            favorites_loaded_state,
        ],
    )

    # Pagination
    def _go_prev(
        unit: str,
        current_page: int,
        cards_cache: list[dict[str, Any]],
        fav_ids_cache: list[str],
        search_raw: str,
        per_page_raw: str,
    ) -> tuple[str, str, int]:
        return _render_from_cache(
            unit,
            max(1, current_page - 1),
            cards_cache,
            fav_ids_cache,
            search_raw,
            per_page_raw,
        )

    def _go_next(
        unit: str,
        current_page: int,
        cards_cache: list[dict[str, Any]],
        fav_ids_cache: list[str],
        search_raw: str,
        per_page_raw: str,
    ) -> tuple[str, str, int]:
        return _render_from_cache(
            unit,
            current_page + 1,
            cards_cache,
            fav_ids_cache,
            search_raw,
            per_page_raw,
        )

    favorites_prev_btn.click(fn=_go_prev, inputs=_cache_inputs, outputs=_page_outputs)
    favorites_next_btn.click(fn=_go_next, inputs=_cache_inputs, outputs=_page_outputs)

    # Load favorites when navigating to favorites page
    def _navigate_and_load(
        loaded: bool,
        unit: str,
        cards_cache: list[dict[str, Any]],
        fav_ids: list[str],
        sid: str = "",
    ):
        """Navigate to favorites, loading data if not cached.

        If the session has been invalidated (e.g. by a concurrent
        logout), returns a full no-op to avoid re-showing containers.
        """
        # page_state + containers + 6 data outputs
        _n_out = 1 + n_containers + 6

        # Fast check: if the session is already gone, skip everything.
        if sid and not is_session_valid(sid):
            return tuple(gr.update() for _ in range(_n_out))

        nav = navigate_to(PAGE_FAVORITES)
        if loaded:
            html, page_info, new_page = _render_from_cache(
                unit, 1, cards_cache, fav_ids
            )
            result = (
                *nav,
                html,
                page_info,
                new_page,
                cards_cache,
                fav_ids,
                loaded,
            )
        else:
            (
                html,
                page_info,
                new_page,
                new_cards,
                new_fav_ids,
                loaded_flag,
            ) = _refresh_cache("cm")
            result = (
                *nav,
                html,
                page_info,
                new_page,
                new_cards,
                new_fav_ids,
                loaded_flag,
            )

        # Re-check AFTER the (potentially slow) API call so that a
        # concurrent logout that invalidated the session while we
        # were loading data does NOT re-show page containers.
        if sid and not is_session_valid(sid):
            return tuple(gr.update() for _ in range(_n_out))

        return result

    _nav_inputs: list[gr.components.Component] = [
        favorites_loaded_state,
        favorites_unit_selector,
        favorites_cards_cache_state,
        favorites_fav_ids_cache_state,
    ]
    if session_id_state is not None:
        _nav_inputs.append(session_id_state)

    favorites_event = home_favorites_btn.click(
        fn=_navigate_and_load,
        inputs=_nav_inputs,
        outputs=[
            page_state,
            *page_containers,
            favorites_cards_html,
            favorites_page_info,
            favorites_page_state,
            favorites_cards_cache_state,
            favorites_fav_ids_cache_state,
            favorites_loaded_state,
        ],
    )

    return favorites_event
