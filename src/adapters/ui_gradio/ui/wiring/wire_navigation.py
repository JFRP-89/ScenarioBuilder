"""Navigation wiring — hooks up all inter-page navigation buttons.

Handles Home, Browse, Create, Favorites, Back buttons across every page.
Each navigation action first checks that the server-side session is still
valid (idle timeout, max lifetime). If expired, the user is returned to
the login screen.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import is_session_valid
from adapters.ui_gradio.ui.router import (
    PAGE_CREATE,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
)


def _expired_result(
    n_page_containers: int,
) -> tuple[Any, ...]:
    """Return outputs that hide everything and show the login panel.

    Output order matches ``nav_outputs_with_session``:
    ``[page_state, *page_containers, session_id_state, actor_id_state,
       login_panel, top_bar_row, login_message]``
    """
    return (
        PAGE_HOME,  # page_state → reset
        # hide every page container
        *(gr.update(visible=False) for _ in range(n_page_containers)),
        "",  # session_id_state → cleared
        "",  # actor_id_state → cleared
        gr.update(visible=True),  # login_panel / auth_gate → show
        gr.update(visible=False),  # top_bar_row → hide
        gr.update(
            value='Session expired \u2014 please <a href="/login">log in</a> again.',
        ),  # login_message / auth_message
    )


def wire_navigation(
    *,
    page_state: gr.State,
    previous_page_state: gr.State,
    page_containers: list[gr.Column],
    # Home page buttons
    home_create_btn: gr.Button,
    # Back buttons on each page
    list_back_btn: gr.Button,
    detail_back_btn: gr.Button,
    create_back_btn: gr.Button,
    edit_back_btn: gr.Button,
    favorites_back_btn: gr.Button,
    # Session-guard components
    session_id_state: gr.State,
    actor_id_state: gr.State,
    login_panel: gr.Column,
    top_bar_row: gr.Row,
    login_message: gr.Textbox,
) -> None:
    """Wire all navigation buttons with session-expiry guard.

    If the session has expired (idle > 15 min or max lifetime > 12 h),
    the user is returned to the login screen instead of navigating.

    Note: ``home_browse_btn`` and ``home_favorites_btn`` are **not**
    wired here.  Their click handlers live in ``wire_list_page`` and
    ``wire_favorites_page`` respectively, which combine navigation with
    data loading in a single callback to avoid race conditions on
    logout.
    """
    n = len(page_containers)

    # Outputs that every guarded button writes to
    nav_outputs_with_session = [
        page_state,
        *page_containers,
        session_id_state,
        actor_id_state,
        login_panel,
        top_bar_row,
        login_message,
    ]

    def _guarded_nav(target_page: str, sid: str) -> tuple[Any, ...]:
        """Navigate to *target_page* if session is valid, else expire."""
        if not is_session_valid(sid):
            return _expired_result(n)
        page_val, *vis = navigate_to(target_page)
        return (
            page_val,
            *vis,
            gr.update(),  # session_id_state unchanged
            gr.update(),  # actor_id_state unchanged
            gr.update(),  # login_panel unchanged
            gr.update(),  # top_bar_row unchanged
            gr.update(),  # login_message unchanged
        )

    # Home → Create (Browse and Favorites are handled by their
    # respective wire_*_page functions to avoid dual-handler races.)
    home_create_btn.click(
        fn=lambda sid: _guarded_nav(PAGE_CREATE, sid),
        inputs=[session_id_state],
        outputs=nav_outputs_with_session,
    )

    # Back → Home
    list_back_btn.click(
        fn=lambda sid: _guarded_nav(PAGE_HOME, sid),
        inputs=[session_id_state],
        outputs=nav_outputs_with_session,
    )
    create_back_btn.click(
        fn=lambda sid: _guarded_nav(PAGE_HOME, sid),
        inputs=[session_id_state],
        outputs=nav_outputs_with_session,
    )
    favorites_back_btn.click(
        fn=lambda sid: _guarded_nav(PAGE_HOME, sid),
        inputs=[session_id_state],
        outputs=nav_outputs_with_session,
    )

    # Back from detail/edit → previous page
    def _guarded_detail_back(from_page: str, sid: str) -> tuple[Any, ...]:
        if not is_session_valid(sid):
            return _expired_result(n)
        target = (
            from_page
            if from_page in (PAGE_HOME, PAGE_LIST, PAGE_FAVORITES)
            else PAGE_LIST
        )
        page_val, *vis = navigate_to(target)
        return (
            page_val,
            *vis,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    detail_back_btn.click(
        fn=_guarded_detail_back,
        inputs=[previous_page_state, session_id_state],
        outputs=nav_outputs_with_session,
    )
    edit_back_btn.click(
        fn=_guarded_detail_back,
        inputs=[previous_page_state, session_id_state],
        outputs=nav_outputs_with_session,
    )
