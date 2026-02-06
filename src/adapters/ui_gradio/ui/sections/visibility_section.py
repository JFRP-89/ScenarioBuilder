"""Visibility section."""

from typing import Any

import gradio as gr


def build_visibility_section() -> tuple[Any, Any, Any]:
    """Build visibility UI components.

    Returns:
        Tuple of (visibility, shared_with_row, shared_with)
    """
    gr.Markdown("## Visibility")
    with gr.Row():
        visibility = gr.Radio(
            choices=["private", "public", "shared"],
            value="private",
            label="Visibility",
            elem_id="visibility",
        )

    with gr.Row(visible=False) as shared_with_row:
        shared_with = gr.Textbox(
            label="Shared With (comma-separated user IDs)",
            placeholder="e.g., user1, user2, user3",
            elem_id="shared-with",
        )

    return visibility, shared_with_row, shared_with
