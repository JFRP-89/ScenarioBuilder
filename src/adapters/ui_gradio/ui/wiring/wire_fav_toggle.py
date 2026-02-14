"""Global favorite-toggle wiring — handles star clicks from any page.

When a user clicks a ☆/★ star in the card HTML (home, list, or favorites),
JavaScript writes the card_id into a hidden textbox and triggers a hidden
button. This module wires that button to call the Flask API toggle.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.services import navigation as nav_svc
from adapters.ui_gradio.state_helpers import get_default_actor_id


def wire_fav_toggle(
    *,
    fav_toggle_card_id: gr.Textbox,
    fav_toggle_btn: gr.Button,
    actor_id_state: gr.State | None = None,
) -> None:
    """Wire the global hidden toggle button to handle star clicks."""

    def _handle_toggle(card_id: str, actor_id: str = "") -> str:
        """Toggle favorite and clear the hidden input."""
        if card_id:
            if not actor_id:
                actor_id = get_default_actor_id()
            nav_svc.toggle_favorite(actor_id, card_id)
        return ""

    _toggle_inputs: list[gr.components.Component] = [fav_toggle_card_id]
    if actor_id_state is not None:
        _toggle_inputs.append(actor_id_state)

    fav_toggle_btn.click(
        fn=_handle_toggle,
        inputs=_toggle_inputs,
        outputs=[fav_toggle_card_id],
    )
