"""List-page wiring — loads cards when filter changes.

Calls the Flask API via ``services.navigation`` and renders results
using the ``scenario_card`` component.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import is_session_valid
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id
from adapters.ui_gradio.ui.components.search_helpers import (
    render_filtered_page,
)
from adapters.ui_gradio.ui.router import (
    PAGE_LIST,
    navigate_to,
)

# Set by wire_list_page(); used by _navigate_and_load() for no-op sizing.
_N_CONTAINERS: int = 6


def _refresh_cache(
    filter_value: str,
    unit: str = "cm",
    search_raw: str = "",
    per_page_raw: str = "10",
    actor_id: str = "",
) -> tuple[str, str, int, dict[str, list[dict[str, Any]]], list[str], bool]:
    """Fetch cards from API and return rendered first page plus cache."""
    if not actor_id:
        actor_id = get_default_actor_id()
    cache: dict[str, list[dict[str, Any]]] = {}
    for key in ["mine", "shared_with_me"]:
        result = nav_svc.list_cards(actor_id, key)
        cache[key] = result.get("cards", []) if result.get("status") != "error" else []

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
    """Render a page from the in-memory cache."""
    cards = cache.get(filter_value, []) if isinstance(cache, dict) else []
    return render_filtered_page(  # type: ignore[no-any-return]
        cards, fav_ids, unit, page, search_raw, per_page_raw
    )


def _cache_reset_page1(
    filter_value: str,
    unit: str,
    _page: int,
    cache: dict[str, list[dict[str, Any]]],
    fav_ids: list[str],
    search_raw: str,
    per_page_raw: str,
) -> tuple[str, str, int]:
    """Re-render from cache starting at page 1."""
    return _render_from_cache(
        filter_value, unit, 1, cache, fav_ids, search_raw, per_page_raw
    )


def _go_prev(
    filter_value: str,
    unit: str,
    current_page: int,
    cache: dict[str, list[dict[str, Any]]],
    fav_ids: list[str],
    search_raw: str,
    per_page_raw: str,
) -> tuple[str, str, int]:
    """Navigate to the previous page."""
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
    """Navigate to the next page."""
    return _render_from_cache(
        filter_value,
        unit,
        current_page + 1,
        cache,
        fav_ids,
        search_raw,
        per_page_raw,
    )


def _navigate_and_load(
    loaded: bool,
    filter_value: str,
    unit: str,
    cache: dict[str, list[dict[str, Any]]],
    fav_ids: list[str],
    sid: str = "",
):
    """Navigate to list page, loading data if not cached.

    If the session has been invalidated (e.g. by a concurrent logout),
    returns a full no-op to avoid re-showing page containers after
    the login panel is already displayed.
    """
    # page_state + containers + 7 data outputs
    _n_out = 1 + _N_CONTAINERS + 7

    # Fast check: if the session is already gone, skip everything.
    if sid and not is_session_valid(sid):
        return tuple(gr.update() for _ in range(_n_out))

    nav = navigate_to(PAGE_LIST)
    if loaded:
        html, page_info, new_page = _render_from_cache(
            filter_value, unit, 1, cache, fav_ids
        )
        result = (
            *nav,
            filter_value,
            html,
            page_info,
            new_page,
            cache,
            fav_ids,
            loaded,
        )
    else:
        (
            html,
            page_info,
            new_page,
            new_cache,
            new_fav_ids,
            loaded_flag,
        ) = _refresh_cache("mine", "cm")
        result = (
            *nav,
            "mine",
            html,
            page_info,
            new_page,
            new_cache,
            new_fav_ids,
            loaded_flag,
        )

    # Re-check AFTER the (potentially slow) API call so that a
    # concurrent logout that invalidated the session while we were
    # loading data does NOT re-show page containers.
    if sid and not is_session_valid(sid):
        return tuple(gr.update() for _ in range(_n_out))

    return result


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
    actor_id_state: gr.State | None = None,
    session_id_state: gr.State | None = None,
) -> Any:
    """Wire the list page interactions.

    Returns:
        The ``home_browse_btn.click`` event ``Dependency``.
    """
    global _N_CONTAINERS
    _N_CONTAINERS = len(page_containers)

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
    _refresh_inputs: list[gr.components.Component] = list(
        filter(
            None,
            [
                list_filter,
                list_unit_selector,
                list_search_box,
                list_per_page_dropdown,
                actor_id_state,
            ],
        )
    )

    list_reload_btn.click(
        fn=_refresh_cache,
        inputs=_refresh_inputs,
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
    list_prev_btn.click(fn=_go_prev, inputs=_cache_inputs, outputs=_page_outputs)
    list_next_btn.click(fn=_go_next, inputs=_cache_inputs, outputs=_page_outputs)

    # Navigate from home → list page
    _nav_inputs: list[gr.components.Component] = [
        list_loaded_state,
        list_filter,
        list_unit_selector,
        list_cards_cache_state,
        list_fav_ids_cache_state,
    ]
    if session_id_state is not None:
        _nav_inputs.append(session_id_state)

    browse_event = home_browse_btn.click(
        fn=_navigate_and_load,
        inputs=_nav_inputs,
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

    return browse_event
