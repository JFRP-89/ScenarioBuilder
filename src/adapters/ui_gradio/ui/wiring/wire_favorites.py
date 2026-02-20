"""Favorites-page wiring — loads favorite cards on page visit.

Fetches favorite IDs, then gets card data for each.
"""

from __future__ import annotations

from dataclasses import dataclass
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

# Type alias for the 6-tuple returned by _refresh_cache
_CacheResult = tuple[str, str, int, list[dict[str, Any]], list[str], bool]


def _build_error_html(message: str) -> str:
    """Build an error HTML block for the favorites page."""
    return f'<div style="color:red;padding:20px;">Error: {message}</div>'


_EMPTY_FAVORITES_HTML = (
    '<div style="text-align:center;color:#999;padding:40px 0;">'
    "No favorites yet. Browse scenarios and ⭐ your favorites!"
    "</div>"
)

_ONE_PAGE_INFO = '<div style="text-align:center">Page 1 of 1</div>'


def _fetch_favorite_cards(
    actor_id: str,
) -> tuple[list[dict[str, Any]], list[str], str | None]:
    """Return ``(cards, fav_ids, error_html | None)``."""
    fav_result = nav_svc.list_favorites(actor_id)
    if fav_result.get("status") == "error":
        msg = escape_html(fav_result.get("message", "Unknown error"))
        return [], [], _build_error_html(msg)

    card_ids = fav_result.get("card_ids", [])
    if not card_ids:
        return [], [], None  # caller checks empty list

    cards: list[dict[str, Any]] = []
    for cid in card_ids:
        card_data = nav_svc.get_card(actor_id, cid)
        if card_data.get("status") != "error":
            cards.append(card_data)

    return cards, list(card_ids), None


def _refresh_cache(
    unit: str = "cm",
    search_raw: str = "",
    per_page_raw: str = "10",
    actor_id: str = "",
) -> _CacheResult:
    """Fetch fresh favorites data from API and render first page."""
    if not actor_id:
        actor_id = get_default_actor_id()

    cards, fav_ids, error_html = _fetch_favorite_cards(actor_id)
    if error_html:
        return error_html, _ONE_PAGE_INFO, 1, [], [], True

    if not cards and not fav_ids:
        return _EMPTY_FAVORITES_HTML, _ONE_PAGE_INFO, 1, [], [], True

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
    """Render a page from the cached cards/fav_ids."""
    return render_filtered_page(
        cards_cache,
        fav_ids_cache,
        unit,
        page,
        search_raw,
        per_page_raw,
        count_label="favorites",
    )


@dataclass(frozen=True)
class FavoritesPageCtx:
    """Widget references for favorites-page wiring."""

    page_state: gr.State
    page_containers: list[gr.Column]
    favorites_unit_selector: gr.Radio
    favorites_search_box: gr.Textbox
    favorites_per_page_dropdown: gr.Dropdown
    favorites_reload_btn: gr.Button
    favorites_cards_html: gr.HTML
    favorites_page_info: gr.HTML
    favorites_prev_btn: gr.Button
    favorites_next_btn: gr.Button
    favorites_page_state: gr.State
    home_favorites_btn: gr.Button
    favorites_cards_cache_state: gr.State
    favorites_fav_ids_cache_state: gr.State
    favorites_loaded_state: gr.State
    actor_id_state: gr.State | None = None
    session_id_state: gr.State | None = None


def wire_favorites_page(*, ctx: FavoritesPageCtx) -> Any:  # noqa: C901
    """Wire the favorites page interactions.

    Returns:
        The ``home_favorites_btn.click`` event ``Dependency``.
    """
    c = ctx
    n_containers = len(c.page_containers)

    _cache_inputs = [
        c.favorites_unit_selector,
        c.favorites_page_state,
        c.favorites_cards_cache_state,
        c.favorites_fav_ids_cache_state,
        c.favorites_search_box,
        c.favorites_per_page_dropdown,
    ]
    _page_outputs = [
        c.favorites_cards_html,
        c.favorites_page_info,
        c.favorites_page_state,
    ]

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

    for widget in (c.favorites_search_box, c.favorites_per_page_dropdown):
        widget.change(
            fn=_cache_reset_page1,
            inputs=_cache_inputs,
            outputs=_page_outputs,
        )

    # Unit change keeps current page
    c.favorites_unit_selector.change(
        fn=_render_from_cache,
        inputs=_cache_inputs,
        outputs=_page_outputs,
    )

    # Reload favorites on demand
    _refresh_inputs: list[gr.components.Component] = [
        c.favorites_unit_selector,
        c.favorites_search_box,
        c.favorites_per_page_dropdown,
    ]
    if c.actor_id_state is not None:
        _refresh_inputs.append(c.actor_id_state)

    c.favorites_reload_btn.click(
        fn=_refresh_cache,
        inputs=_refresh_inputs,
        outputs=[
            c.favorites_cards_html,
            c.favorites_page_info,
            c.favorites_page_state,
            c.favorites_cards_cache_state,
            c.favorites_fav_ids_cache_state,
            c.favorites_loaded_state,
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

    c.favorites_prev_btn.click(fn=_go_prev, inputs=_cache_inputs, outputs=_page_outputs)
    c.favorites_next_btn.click(fn=_go_next, inputs=_cache_inputs, outputs=_page_outputs)

    # Load favorites when navigating to favorites page
    _n_out = 1 + n_containers + 6

    def _session_expired_noop() -> tuple[Any, ...]:
        return tuple(gr.update() for _ in range(_n_out))

    def _navigate_and_load(
        unit: str,
        sid: str = "",
        actor_id: str = "",
    ):
        """Navigate to favorites, always loading fresh data from the API."""
        if sid and not is_session_valid(sid):
            return _session_expired_noop()

        nav = navigate_to(PAGE_FAVORITES)
        cache = _refresh_cache(unit, actor_id=actor_id)
        result = (*nav, *cache)

        if sid and not is_session_valid(sid):
            return _session_expired_noop()

        return result

    _nav_inputs: list[gr.components.Component] = [
        c.favorites_unit_selector,
    ]
    if c.session_id_state is not None:
        _nav_inputs.append(c.session_id_state)
    if c.actor_id_state is not None:
        _nav_inputs.append(c.actor_id_state)

    favorites_event = c.home_favorites_btn.click(
        fn=_navigate_and_load,
        inputs=_nav_inputs,
        outputs=[
            c.page_state,
            *c.page_containers,
            c.favorites_cards_html,
            c.favorites_page_info,
            c.favorites_page_state,
            c.favorites_cards_cache_state,
            c.favorites_fav_ids_cache_state,
            c.favorites_loaded_state,
        ],
    )

    return favorites_event
