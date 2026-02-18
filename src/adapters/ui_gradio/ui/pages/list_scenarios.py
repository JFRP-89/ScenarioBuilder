"""List scenarios page — view your scenarios and shared collections.

Shows:
- Filter radio (mine / shared_with_me)
- Card list (HTML rendered)
- Back to Home button
"""

from __future__ import annotations

from types import SimpleNamespace

import gradio as gr


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

        with gr.Row():
            filter_radio = gr.Radio(
                choices=["mine", "shared_with_me"],
                value="mine",
                label="Filter",
                elem_id="list-filter",
                interactive=True,
            )
            unit_selector = gr.Radio(
                choices=["cm", "in", "ft"],
                value="cm",
                label="Units",
                elem_id="list-unit-selector",
                scale=0,
            )
            reload_btn = gr.Button(
                "Refresh",
                variant="secondary",
                size="sm",
                elem_id="list-reload-btn",
            )

        with gr.Row():
            search_box = gr.Textbox(
                label="Search by name",
                placeholder="e.g. Osgiliath",
                value="",
                elem_id="list-search-box",
                scale=3,
                max_lines=1,
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
                '<div style="text-align:center;color:#999;padding:40px 0;">'
                "Select a filter to load scenarios.</div>"
            ),
            elem_id="list-cards",
        )

        # Pagination controls
        with gr.Row():
            prev_btn = gr.Button("← Previous", scale=1, size="sm")
            page_info = gr.HTML(
                value='<div style="text-align:center;padding:10px 0;">Page 1</div>',
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
