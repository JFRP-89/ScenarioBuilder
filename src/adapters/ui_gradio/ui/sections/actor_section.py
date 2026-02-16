"""Actor ID section."""

from typing import Any

import gradio as gr


def build_actor_section(default_actor_id: str) -> Any:
    """Build Actor ID input section.

    The actor ID is derived from the logged-in session and is NOT
    user-editable (security: deny IDOR).  The textbox is hidden so
    that auth wiring can still populate it on page load.

    Args:
        default_actor_id: Default value for actor ID

    Returns:
        actor_id textbox component (hidden)
    """
    actor_id = gr.Textbox(
        label="Actor ID",
        value=default_actor_id,
        visible=False,
        elem_id="actor-id-input",
    )
    return actor_id
