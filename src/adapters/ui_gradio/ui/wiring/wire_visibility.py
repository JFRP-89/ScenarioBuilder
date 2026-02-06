"""Visibility-section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers


def _update_shared_with_visibility(vis: str) -> dict[str, Any]:
    result: dict[str, Any] = handlers.update_shared_with_visibility(vis)
    return result


def wire_visibility(
    *,
    visibility: gr.Radio,
    shared_with_row: gr.Row,
) -> None:
    """Wire visibility radio to shared_with row toggle."""

    visibility.change(
        fn=_update_shared_with_visibility,
        inputs=[visibility],
        outputs=[shared_with_row],
    )
