"""View-button wiring — navigates to detail page when View is clicked.

The View button in card lists writes a card_id to a hidden textbox,
then clicks a hidden button. This module handles that hidden button click
to navigate to the detail page.

Includes a session-expiry guard: if the session has expired, the user
is returned to the login screen instead of viewing the card.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import is_session_valid
from adapters.ui_gradio.ui.router import PAGE_HOME, navigate_to_detail
from adapters.ui_gradio.ui.wiring.wire_navigation import _expired_result


def wire_view_navigation(
    *,
    view_card_id: gr.Textbox,
    view_card_btn: gr.Button,
    page_state: gr.State,
    detail_card_id_state: gr.State,
    previous_page_state: gr.State,
    page_containers: list[gr.Column],
    session_id_state: gr.State,
    actor_id_state: gr.State,
    login_panel: gr.Column,
    top_bar_row: gr.Row,
    login_message: gr.Textbox,
) -> Any:
    """Wire the global View button handler with session guard.

    When JS writes a card_id to the hidden textbox and clicks the hidden
    button, validate the session first.  If expired → show login screen.
    Otherwise navigate to the detail page.

    Returns:
        The ``view_card_btn.click`` event ``Dependency`` so it can be
        cancelled on logout to prevent stale page visibility.
    """
    n = len(page_containers)

    def _navigate_to_detail(
        card_id: str, current_page: str, sid: str
    ) -> tuple[Any, ...]:
        """Navigate to detail page if session is valid, else expire."""
        if not is_session_valid(sid):
            # _expired_result produces:
            # (page_state, *containers, session_id, actor_id,
            #  login_panel, top_bar_row, login_message)
            exp = _expired_result(n)
            # Pad with detail_card_id_state, previous_page_state, view_card_id
            return (
                exp[0],  # page_state
                exp[1 : 1 + n],  # containers (unpacked below)
                "",  # detail_card_id_state
                PAGE_HOME,  # previous_page_state
                *exp[1 + n :],  # session, actor, login_panel, top_bar, msg
                "",  # view_card_id
            )

        if not card_id or not card_id.strip():
            no_op = (gr.update(),) * (3 + n + 5) + ("",)
            return no_op
        nav = navigate_to_detail(card_id.strip(), from_page=current_page)
        # nav = (page_state, card_id_state, prev_page_state, *vis)
        return (
            *nav,  # page_state, card_id, prev_page, *vis
            gr.update(),  # session_id_state
            gr.update(),  # actor_id_state
            gr.update(),  # login_panel
            gr.update(),  # top_bar_row
            gr.update(),  # login_message
            "",  # view_card_id
        )

    # Actually, let me flatten this properly.
    def _guarded_view(card_id: str, current_page: str, sid: str) -> tuple[Any, ...]:
        """View a card with session guard."""
        if not is_session_valid(sid):
            return (
                PAGE_HOME,  # page_state
                "",  # detail_card_id_state
                PAGE_HOME,  # previous_page_state
                *(gr.update(visible=False) for _ in range(n)),  # containers
                "",  # session_id_state
                "",  # actor_id_state
                gr.update(visible=True),  # login_panel
                gr.update(visible=False),  # top_bar_row
                gr.update(
                    value="Session expired — please log in again.",
                    visible=True,
                ),  # login_message
                "",  # view_card_id
            )

        if not card_id or not card_id.strip():
            return (
                gr.update(),  # page_state
                gr.update(),  # detail_card_id_state
                gr.update(),  # previous_page_state
                *(gr.update() for _ in range(n)),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                "",
            )

        nav = navigate_to_detail(card_id.strip(), from_page=current_page)
        # nav = (page_state, card_id, prev_page, *visibility)
        return (
            *nav,
            gr.update(),  # session_id_state
            gr.update(),  # actor_id_state
            gr.update(),  # login_panel
            gr.update(),  # top_bar_row
            gr.update(),  # login_message
            "",  # view_card_id
        )

    view_event = view_card_btn.click(
        fn=_guarded_view,
        inputs=[view_card_id, page_state, session_id_state],
        outputs=[
            page_state,
            detail_card_id_state,
            previous_page_state,
            *page_containers,
            session_id_state,
            actor_id_state,
            login_panel,
            top_bar_row,
            login_message,
            view_card_id,
        ],
    )

    return view_event
