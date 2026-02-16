"""Form/dropdown/extra reset builders for create-scenario success path."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.ui.components.svg_preview import _PLACEHOLDER_HTML


def build_form_resets() -> list[Any]:
    """Return the 19-element list that resets every form component.

    Order must match ``_form_components`` in ``wire_generate``.
    """
    return [
        gr.update(value=""),  # scenario_name
        gr.update(value="casual"),  # mode
        gr.update(value=True),  # is_replicable
        gr.update(
            value=None, interactive=True
        ),  # generate_from_seed (enabled: replicable defaults True)
        gr.update(value=""),  # armies
        gr.update(value=""),  # deployment
        gr.update(value=""),  # layout
        gr.update(value=""),  # objectives
        gr.update(value=""),  # initial_priority
        gr.update(value="public"),  # visibility
        gr.update(value=""),  # shared_with
        [],  # special_rules_state
        gr.update(value=False),  # objectives_with_vp_toggle
        [],  # vp_state
        [],  # scenography_state
        [],  # deployment_zones_state
        [],  # objective_points_state
        gr.update(value=_PLACEHOLDER_HTML),  # svg_preview
        gr.update(value=None),  # output
    ]


def build_dropdown_resets(
    dropdown_lists: list[gr.components.Component],
) -> list[Any]:
    """Return one ``gr.update`` per dropdown component."""
    return [
        (
            gr.update(value="")
            if isinstance(c, gr.Textbox)
            else gr.update(value=None, choices=[])
        )
        for c in dropdown_lists
    ]


def build_extra_resets(
    *,
    has_editing_card_id: bool,
    has_create_heading_md: bool,
) -> list[Any]:
    """Return reset values for edit-mode state components."""
    resets: list[Any] = []
    if has_editing_card_id:
        resets.append("")  # clear editing_card_id
    if has_create_heading_md:
        resets.append(gr.update(value="## Create New Scenario"))
    return resets
