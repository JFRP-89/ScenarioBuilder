"""Navigation wiring — hooks up all inter-page navigation buttons.

Handles Home, Browse, Create, Favorites, Back buttons across every page.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.ui.router import (
    PAGE_CREATE,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
)


def wire_navigation(
    *,
    page_state: gr.State,
    page_containers: list[gr.Column],
    # Home page buttons
    home_create_btn: gr.Button,
    home_browse_btn: gr.Button,
    home_favorites_btn: gr.Button,
    # Back buttons on each page
    list_back_btn: gr.Button,
    detail_back_btn: gr.Button,
    create_back_btn: gr.Button,
    edit_back_btn: gr.Button,
    favorites_back_btn: gr.Button,
) -> None:
    """Wire all navigation buttons to page transitions.

    When navigating back to Home, recent cards are reloaded from Flask
    so newly created or changed cards appear immediately.
    """
    nav_outputs = [page_state, *page_containers]

    def _go_home():
        return navigate_to(PAGE_HOME)

    def _go_create():
        return navigate_to(PAGE_CREATE)

    def _go_list():
        return navigate_to(PAGE_LIST)

    def _go_favorites():
        return navigate_to(PAGE_FAVORITES)

    # Home → other pages
    home_create_btn.click(fn=_go_create, inputs=[], outputs=nav_outputs)
    home_browse_btn.click(fn=_go_list, inputs=[], outputs=nav_outputs)
    home_favorites_btn.click(fn=_go_favorites, inputs=[], outputs=nav_outputs)

    # Back → Home (from list, create, favorites)
    list_back_btn.click(fn=_go_home, inputs=[], outputs=nav_outputs)
    create_back_btn.click(fn=_go_home, inputs=[], outputs=nav_outputs)
    favorites_back_btn.click(fn=_go_home, inputs=[], outputs=nav_outputs)

    # Back from detail → list
    def _detail_back():
        return navigate_to(PAGE_LIST)

    detail_back_btn.click(fn=_detail_back, inputs=[], outputs=nav_outputs)

    # Back from edit → detail (or list)
    edit_back_btn.click(fn=_detail_back, inputs=[], outputs=nav_outputs)
