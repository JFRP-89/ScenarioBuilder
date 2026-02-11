"""View-button wiring — navigates to detail page when View is clicked.

The View button in card lists writes a card_id to a hidden textbox,
then clicks a hidden button. This module handles that hidden button click
to navigate to the detail page.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.ui.router import navigate_to_detail


def wire_view_navigation(
    *,
    view_card_id: gr.Textbox,
    view_card_btn: gr.Button,
    page_state: gr.State,
    detail_card_id_state: gr.State,
    previous_page_state: gr.State,
    page_containers: list[gr.Column],
) -> None:
    """Wire the global View button handler.

    When JS writes a card_id to the hidden textbox and clicks the hidden
    button, navigate to the detail page and set the card_id state.
    Remembers the origin page so Back button can return there.
    """

    def _navigate_to_detail(card_id: str, current_page: str) -> tuple:
        """Navigate to detail page for the given card_id, then clear input."""
        if not card_id or not card_id.strip():
            return (gr.update(),) * (3 + len(page_containers)) + ("",)
        nav = navigate_to_detail(card_id.strip(), from_page=current_page)
        return (*nav, "")

    view_card_btn.click(
        fn=_navigate_to_detail,
        inputs=[view_card_id, page_state],
        outputs=[
            page_state,
            detail_card_id_state,
            previous_page_state,
            *page_containers,
            view_card_id,
        ],
    )
