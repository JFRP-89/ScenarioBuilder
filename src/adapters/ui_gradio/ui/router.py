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
# Navigation helpers
# ============================================================================
def build_page_state() -> gr.State:
    """Create a State component to track the current page.

    Returns:
        gr.State initialized to the default page (home).
    """
    return gr.State(DEFAULT_PAGE)


def build_detail_card_id_state() -> gr.State:
    """Create a State to hold the card_id being viewed/edited.

    Returns:
        gr.State initialized to empty string.
    """
    return gr.State("")


def page_visibility(target_page: str) -> list[Any]:
    """Return a list of gr.update(visible=...) for each page container.

    Args:
        target_page: The page to show. All others are hidden.

    Returns:
        List of gr.update dicts, one per page in ALL_PAGES order.
    """
    return [gr.update(visible=(p == target_page)) for p in ALL_PAGES]


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


def navigate_to_detail(card_id: str) -> tuple[Any, ...]:
    """Navigate to the detail page for a specific card.

    Returns:
      - new page state
      - card_id state
      - one visibility update per page container

    Args:
        card_id: ID of the card to show.

    Returns:
        Tuple: (page_state, card_id_state, *visibility_updates)
    """
    visibility = page_visibility(PAGE_DETAIL)
    return (PAGE_DETAIL, card_id, *visibility)


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
