"""CONTROL BAR — compact filter + refresh strip for list pages.

Renders a unified panel with segmented radio filters and a circular
refresh button.  Reused across Home, My Scenarios and Favorites.

Each page passes only the filters it needs; unused filters are omitted
without visual gaps thanks to the CSS grid layout.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Sequence

import gradio as gr


# ── public builder ──────────────────────────────────────────────────────
def build_control_bar(
    *,
    page_prefix: str,
    mode_choices: Sequence[str] | None = None,
    mode_default: str = "All",
    preset_choices: Sequence[str] | None = None,
    preset_default: str = "All",
    unit_choices: Sequence[str] = ("cm", "in", "ft"),
    unit_default: str = "cm",
    filter_choices: Sequence[str] | None = None,
    filter_default: str | None = None,
) -> SimpleNamespace:
    """Build a CONTROL BAR and return its Gradio components.

    Parameters
    ----------
    page_prefix:
        Used for ``elem_id`` namespacing (e.g. ``"home"``, ``"list"``).
    mode_choices / preset_choices:
        Pass ``None`` to omit Game Mode or Table Preset filters entirely.
    filter_choices / filter_default:
        Generic radio filter (used by List Scenarios for mine/shared).
    """
    mode_filter = None
    preset_filter = None
    filter_radio = None
    unit_selector = None
    reload_btn = None

    with gr.Group(elem_classes=["sb-controlbar"]) as bar:
        # Header
        gr.HTML(
            '<div class="sb-controlbar__header">'
            '<span class="sb-controlbar__indicator"></span>'
            "CONTROL BAR"
            "</div>",
        )

        # Top row: Game Mode + Table Preset  (or generic filter)
        with gr.Row(elem_classes=["sb-controlbar__row"]):
            if mode_choices is not None:
                mode_filter = gr.Radio(
                    choices=list(mode_choices),
                    value=mode_default,
                    label="Game Mode",
                    elem_id=f"{page_prefix}-mode-filter",
                    elem_classes=["sb-controlbar__segment"],
                    scale=1,
                )
            if preset_choices is not None:
                preset_filter = gr.Radio(
                    choices=list(preset_choices),
                    value=preset_default,
                    label="Table Preset",
                    elem_id=f"{page_prefix}-preset-filter",
                    elem_classes=["sb-controlbar__segment"],
                    scale=1,
                )
            if filter_choices is not None:
                filter_radio = gr.Radio(
                    choices=list(filter_choices),
                    value=filter_default or filter_choices[0],
                    label="Filter",
                    elem_id=f"{page_prefix}-filter",
                    elem_classes=["sb-controlbar__segment"],
                    interactive=True,
                    scale=1,
                )

        # Bottom row: Units + Refresh
        with gr.Row(elem_classes=["sb-controlbar__row", "sb-controlbar__bottom"]):
            unit_selector = gr.Radio(
                choices=list(unit_choices),
                value=unit_default,
                label="Units",
                elem_id=f"{page_prefix}-unit-selector",
                elem_classes=["sb-controlbar__segment"],
                scale=1,
            )
            reload_btn = gr.Button(
                "⟳",
                variant="secondary",
                size="sm",
                elem_id=f"{page_prefix}-reload-btn",
                elem_classes=["sb-refresh-btn"],
                scale=0,
                min_width=48,
            )

    return SimpleNamespace(
        bar=bar,
        mode_filter=mode_filter,
        preset_filter=preset_filter,
        filter_radio=filter_radio,
        unit_selector=unit_selector,
        reload_btn=reload_btn,
    )
