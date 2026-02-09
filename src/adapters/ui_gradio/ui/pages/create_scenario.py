"""Create scenario page — wraps the existing card-creation form.

This page is a thin wrapper: it adds a "← Home" button and a container
around the existing ``build_app()`` form sections. The actual form
components are built in ``app.py`` and placed inside this container.
"""

from __future__ import annotations

import gradio as gr


def build_create_page_wrapper() -> tuple[gr.Column, gr.Button]:
    """Build the create-scenario page wrapper.

    The form sections will be injected into this column by ``app.py``.

    Returns:
        Tuple of (page_container, back_btn).
    """
    with (
        gr.Column(visible=False, elem_id="page-create-scenario") as container,
        gr.Row(),
    ):
        back_btn = gr.Button(
            "← Home",
            variant="secondary",
            size="sm",
            elem_id="create-back-btn",
        )
        gr.Markdown("## Create New Scenario")

    # The existing form sections will be placed here by app.py
    # (actor, meta, visibility, table, details, shapes, generate)

    return container, back_btn
