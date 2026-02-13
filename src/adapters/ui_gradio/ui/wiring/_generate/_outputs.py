"""Output-tuple builders for the create-scenario flow."""

from __future__ import annotations

from typing import Any

import gradio as gr


def build_stay_outputs(
    msg: str,
    *,
    n_nav: int,
    n_form: int,
    n_dropdowns: int,
    n_extra: int,
) -> tuple[Any, ...]:
    """Build the full output tuple that keeps the user on the current page.

    Every slot is ``gr.update()`` (no-op) except the final status textbox,
    which receives *msg* and becomes visible.
    """
    nav_noop = [gr.update()] * n_nav
    form_noop = [gr.update()] * n_form
    dropdowns_noop = [gr.update()] * n_dropdowns
    extra_noop = [gr.update()] * n_extra
    return (
        *nav_noop,
        gr.update(),  # home_recent_html
        *form_noop,
        *dropdowns_noop,
        *extra_noop,
        gr.update(value=msg, visible=True),
    )
