"""Favorites page — shows cards the user has favorited.

Similar to the list page, but filtered to favorites only.
"""

from __future__ import annotations

from types import SimpleNamespace

import gradio as gr


def build_favorites_page() -> SimpleNamespace:
    """Build the favorites page layout.

    Returns:
        Tuple of (page_container, unit_selector,
                  search_box, per_page_dropdown, reload_btn,
                  cards_html, back_btn, page_info, prev_btn,
                  next_btn,
                  cards_cache_state, fav_ids_cache_state,
                  loaded_state, page_state).
    """
    with gr.Column(visible=False, elem_id="page-favorites") as container:
        with gr.Row():
            back_btn = gr.Button(
                "← Home",
                variant="secondary",
                size="sm",
                elem_id="favorites-back-btn",
            )
            gr.Markdown("## ⭐ My Favorites")
            unit_selector = gr.Radio(
                choices=["cm", "in", "ft"],
                value="cm",
                label="Units",
                elem_id="favorites-unit-selector",
                scale=0,
            )
            reload_btn = gr.Button(
                "Refresh",
                variant="secondary",
                size="sm",
                elem_id="favorites-reload-btn",
            )

        with gr.Row():
            search_box = gr.Textbox(
                label="Search by name",
                placeholder="e.g. Osgiliath",
                value="",
                elem_id="favorites-search-box",
                scale=3,
                max_lines=1,
            )
            per_page_dropdown = gr.Dropdown(
                choices=["5", "10", "20", "50", "100"],
                value="10",
                label="Per page",
                elem_id="favorites-per-page",
                scale=1,
            )

        cards_html = gr.HTML(
            value=(
                '<div style="text-align:center;color:#999;padding:40px 0;">'
                "Loading favorites…</div>"
            ),
            elem_id="favorites-cards",
        )

        # Pagination controls
        with gr.Row():
            prev_btn = gr.Button("← Previous", scale=1, size="sm")
            page_info = gr.HTML(
                value='<div style="text-align:center;padding:10px 0;">Page 1</div>',
                elem_id="favorites-page-info",
            )
            next_btn = gr.Button("Next →", scale=1, size="sm")

        cards_cache_state = gr.State(value=[])
        fav_ids_cache_state = gr.State(value=[])
        loaded_state = gr.State(value=False)
        page_state = gr.State(value=1)

    return SimpleNamespace(
        container=container,
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
