"""List scenarios page — view your scenarios and shared collections.

Shows:
- Filter radio (mine / shared_with_me)
- CONTROL BAR with filter / unit selectors + circular refresh
- Card list (HTML rendered)
- Back to Home button
"""

from __future__ import annotations

from types import SimpleNamespace

import gradio as gr

from adapters.ui_gradio.ui.components.control_bar import build_control_bar
from adapters.ui_gradio.ui.components.search_helpers import (
    DEFAULT_SORT,
    SORT_CHOICES,
)


def build_list_page() -> SimpleNamespace:
    """Build the list-scenarios page layout.

    Returns:
        Tuple of (page_container, filter_radio, unit_selector,
                  search_box, per_page_dropdown, reload_btn,
                  cards_html, back_btn, page_info, prev_btn,
                  next_btn,
                  cards_cache_state, fav_ids_cache_state,
                  loaded_state, page_state).
    """
    with gr.Column(visible=False, elem_id="page-list-scenarios") as container:
        with gr.Row():
            back_btn = gr.Button(
                "← Home",
                variant="secondary",
                size="sm",
                elem_id="list-back-btn",
            )
            gr.Markdown("## Your Scenarios", elem_id="list-title")

        # ── CONTROL BAR (filter + units + refresh) ───────────────────
        cb = build_control_bar(
            page_prefix="list",
            filter_choices=["mine", "shared_with_me"],
            filter_default="mine",
        )
        filter_radio = cb.filter_radio
        unit_selector = cb.unit_selector
        reload_btn = cb.reload_btn

        with gr.Row():
            search_box = gr.Textbox(
                label="Search by name",
                placeholder="e.g. Osgiliath",
                value="",
                elem_id="list-search-box",
                scale=3,
                max_lines=1,
            )
            sort_dropdown = gr.Dropdown(
                choices=SORT_CHOICES,
                value=DEFAULT_SORT,
                label="Sort by",
                elem_id="list-sort",
                scale=1,
            )
            per_page_dropdown = gr.Dropdown(
                choices=["5", "10", "20", "50", "100"],
                value="10",
                label="Per page",
                elem_id="list-per-page",
                scale=1,
            )

        cards_html = gr.HTML(
            value=(
                '<div style="text-align:center;color:#5a7090;padding:40px 0;">'
                '<div style="font-size:2.5rem;margin-bottom:12px;opacity:.4;">\U0001f4cb</div>'
                "Select a filter to load scenarios.</div>"
            ),
            elem_id="list-cards",
        )

        # Pagination controls
        with gr.Row():
            prev_btn = gr.Button("← Previous", scale=1, size="sm")
            page_info = gr.HTML(
                value='<div style="text-align:center;padding:10px 0;color:#92a9c1;">Page 1</div>',
                elem_id="list-page-info",
            )
            next_btn = gr.Button("Next →", scale=1, size="sm")

        cards_cache_state = gr.State(value={})
        fav_ids_cache_state = gr.State(value=[])
        loaded_state = gr.State(value=False)
        page_state = gr.State(value=1)

    return SimpleNamespace(
        container=container,
        filter_radio=filter_radio,
        unit_selector=unit_selector,
        search_box=search_box,
        sort_dropdown=sort_dropdown,
        per_page_dropdown=per_page_dropdown,
        reload_btn=reload_btn,
        cards_html=cards_html,
        back_btn=back_btn,
        page_info=page_info,
        prev_btn=prev_btn,
        next_btn=next_btn,
        cards_cache_state=cards_cache_state,
        fav_ids_cache_state=fav_ids_cache_state,
        loaded_state=loaded_state,
        page_state=page_state,
    )
