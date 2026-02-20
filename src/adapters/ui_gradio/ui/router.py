"""Page router for multi-page Gradio navigation.

Manages page state transitions and visibility of page containers.
Navigation is implemented via gr.State + show/hide of gr.Column blocks.

No business logic — only UI page management.
"""

from __future__ import annotations

from typing import Any

import gradio as gr

# ============================================================================
# Page constants
# ============================================================================
PAGE_HOME = "home"
PAGE_LIST = "list_scenarios"
PAGE_DETAIL = "scenario_detail"
PAGE_CREATE = "create_scenario"
PAGE_EDIT = "edit_scenario"
PAGE_FAVORITES = "favorites"

ALL_PAGES: list[str] = [
    PAGE_HOME,
    PAGE_LIST,
    PAGE_DETAIL,
    PAGE_CREATE,
    PAGE_EDIT,
    PAGE_FAVORITES,
]

DEFAULT_PAGE = PAGE_HOME

# ============================================================================
# URL path ↔ page mapping (for browser URL sync)
# ============================================================================

#: Map from page constant → URL path served by the combined app.
PAGE_TO_URL: dict[str, str] = {
    PAGE_HOME: "/sb/",
    PAGE_CREATE: "/sb/create/",
    PAGE_EDIT: "/sb/edit/",
    PAGE_DETAIL: "/sb/view/",
    PAGE_LIST: "/sb/myscenarios/",
    PAGE_FAVORITES: "/sb/myfavorites/",
}

#: Reverse map: URL path → page constant.
URL_TO_PAGE: dict[str, str] = {v: k for k, v in PAGE_TO_URL.items()}


# ============================================================================
# Navigation helpers
# ============================================================================
def build_page_state() -> gr.State:
    """Create a State component to track the current page.

    Returns:
        gr.State initialized to the default page (home).
    """
    return gr.State(DEFAULT_PAGE)


def build_detail_card_id_state() -> gr.Textbox:
    """Create a hidden Textbox to hold the card_id being viewed/edited.

    Uses ``gr.Textbox(visible=False)`` instead of ``gr.State`` so that
    ``.change()`` is statically recognised by type-checkers and the
    value is available in the DOM for JS URL-sync.

    Returns:
        gr.Textbox initialized to empty string.
    """
    return gr.Textbox(value="", visible=False, elem_id="detail-card-id-mirror")


def build_detail_reload_trigger() -> gr.State:
    """Create a State to trigger reload of detail page content.

    Incremented each time a card is clicked to ensure reload happens
    even if clicking the same card multiple times.

    Returns:
        gr.State initialized to 0.
    """
    return gr.State(0)


def build_previous_page_state() -> gr.State:
    """Create a State to track where the user navigated from.

    Used by the Back button on detail page to return to the correct origin.

    Returns:
        gr.State initialized to PAGE_HOME.
    """
    return gr.State(PAGE_HOME)


def page_visibility(target_page: str) -> list[Any]:
    """Return a list of gr.update(visible=...) for each page container.

    Args:
        target_page: The page to show. All others are hidden.

    Returns:
        List of gr.update dicts, one per page in ALL_PAGES order.
    """
    # Edit mode reuses the create form container — show create_container
    # for both PAGE_CREATE and PAGE_EDIT.
    effective = PAGE_CREATE if target_page == PAGE_EDIT else target_page
    return [gr.update(visible=(p == effective)) for p in ALL_PAGES]


def navigate_to(target_page: str) -> tuple[Any, ...]:
    """Return outputs for a navigation event.

    Returns a tuple of:
      - new page state value
      - one visibility update per page container

    Args:
        target_page: Destination page name.

    Returns:
        Tuple: (page_state_value, *visibility_updates)
    """
    visibility = page_visibility(target_page)
    return (target_page, *visibility)


def navigate_to_detail(
    card_id: str, from_page: str = PAGE_HOME, reload_trigger: int = 0
) -> tuple[Any, ...]:
    """Navigate to the detail page for a specific card.

    Returns:
      - new page state
      - card_id state
      - previous page state (for Back button)
      - reload_trigger (incremented to force reload)
      - one visibility update per page container

    Args:
        card_id: ID of the card to show.
        from_page: Page the user is navigating from (for Back button).
        reload_trigger: Current trigger value (will be incremented).

    Returns:
        Tuple: (page_state, card_id_state, previous_page_state, reload_trigger+1, *visibility_updates)
    """
    visibility = page_visibility(PAGE_DETAIL)
    return (PAGE_DETAIL, card_id, from_page, reload_trigger + 1, *visibility)


def navigate_to_edit(card_id: str) -> tuple[Any, ...]:
    """Navigate to the edit page for a specific card.

    Returns:
      - new page state
      - card_id state
      - one visibility update per page container

    Args:
        card_id: ID of the card to edit.

    Returns:
        Tuple: (page_state, card_id_state, *visibility_updates)
    """
    visibility = page_visibility(PAGE_EDIT)
    return (PAGE_EDIT, card_id, *visibility)
