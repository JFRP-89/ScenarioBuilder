"""List scenarios page — view your scenarios and shared collections.

Shows:
- Filter radio (mine / shared_with_me)
- Card list (HTML rendered)
- Back to Home button
"""

from __future__ import annotations

import gradio as gr


def build_list_page() -> tuple[
    gr.Column,
    gr.Radio,
    gr.Radio,
    gr.Button,
    gr.HTML,
    gr.Button,
    gr.State,
    gr.State,
    gr.State,
]:
    """Build the list-scenarios page layout.

    Returns:
        Tuple of (page_container, filter_radio, unit_selector, reload_btn,
                  cards_html, back_btn, cards_cache_state, fav_ids_cache_state,
                  loaded_state).
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

        cards_html = gr.HTML(
            value=(
                '<div style="text-align:center;color:#999;padding:40px 0;">'
                "Select a filter to load scenarios.</div>"
            ),
            elem_id="list-cards",
        )

        cards_cache_state = gr.State(value={})
        fav_ids_cache_state = gr.State(value=[])
        loaded_state = gr.State(value=False)

    return (
        container,
        filter_radio,
        unit_selector,
        reload_btn,
        cards_html,
        back_btn,
        cards_cache_state,
        fav_ids_cache_state,
        loaded_state,
    )
