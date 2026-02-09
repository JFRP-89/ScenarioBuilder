"""Favorites page — shows cards the user has favorited.

Similar to the list page, but filtered to favorites only.
"""

from __future__ import annotations

import gradio as gr


def build_favorites_page() -> tuple[
    gr.Column,
    gr.Radio,
    gr.Button,
    gr.HTML,
    gr.Button,
    gr.State,
    gr.State,
    gr.State,
]:
    """Build the favorites page layout.

    Returns:
        Tuple of (page_container, unit_selector, reload_btn, cards_html, back_btn,
                  cards_cache_state, fav_ids_cache_state, loaded_state).
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

        cards_html = gr.HTML(
            value=(
                '<div style="text-align:center;color:#999;padding:40px 0;">'
                "Loading favorites…</div>"
            ),
            elem_id="favorites-cards",
        )

        cards_cache_state = gr.State(value=[])
        fav_ids_cache_state = gr.State(value=[])
        loaded_state = gr.State(value=False)

    return (
        container,
        unit_selector,
        reload_btn,
        cards_html,
        back_btn,
        cards_cache_state,
        fav_ids_cache_state,
        loaded_state,
    )
