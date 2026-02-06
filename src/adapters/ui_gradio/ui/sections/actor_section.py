"""Actor ID section."""

from typing import Any

import gradio as gr


def build_actor_section(default_actor_id: str) -> Any:
    """Build Actor ID input section.

    Args:
        default_actor_id: Default value for actor ID

    Returns:
        actor_id textbox component
    """
    with gr.Row():
        actor_id = gr.Textbox(
            label="Actor ID",
            value=default_actor_id,
            placeholder="Enter your actor ID",
            elem_id="actor-id-input",
        )
    return actor_id
