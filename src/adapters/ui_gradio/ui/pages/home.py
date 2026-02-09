"""Home page — landing screen with recent cards and quick actions.

Shows:
- Welcome header
- Quick-action buttons (Create New, Browse All, Favorites)
- Recent cards list with pagination
"""

from __future__ import annotations

import gradio as gr


def build_home_page() -> tuple[
    gr.Column,
    gr.Button,
    gr.Button,
    gr.Button,
    gr.Radio,
    gr.Radio,
    gr.Radio,
    gr.Button,
    gr.HTML,
    gr.Button,
    gr.HTML,
    gr.Button,
    gr.State,
    gr.State,
    gr.State,
]:
    """Build the home page layout.

    Returns:
        Tuple of (page_container, create_btn, browse_btn, favorites_btn,
                  mode_filter, preset_filter, unit_selector, reload_btn,
                  recent_cards_html, prev_btn, page_info, next_btn, page_state,
                  cards_cache_state, fav_ids_cache_state).
    """
    with gr.Column(visible=True, elem_id="page-home") as container:
        gr.Markdown("# 🎲 Scenario Builder")
        gr.Markdown("Welcome! Create, browse, and manage your scenario cards.")

        with gr.Row():
            create_btn = gr.Button(
                "+ Create New Scenario",
                variant="primary",
                elem_id="home-create-btn",
            )
            browse_btn = gr.Button(
                "📋 Your Scenarios",
                variant="secondary",
                elem_id="home-browse-btn",
            )
            favorites_btn = gr.Button(
                "⭐ Favorites",
                variant="secondary",
                elem_id="home-favorites-btn",
            )

        gr.Markdown("### Recent Scenarios")

        # Filters row
        with gr.Row():
            mode_filter = gr.Radio(
                choices=["All", "Casual", "Narrative", "Matched"],
                value="All",
                label="Game Mode",
                elem_id="home-mode-filter",
                scale=1,
            )
            preset_filter = gr.Radio(
                choices=["All", "Standard", "Massive", "Custom"],
                value="All",
                label="Table Preset",
                elem_id="home-preset-filter",
                scale=1,
            )
            unit_selector = gr.Radio(
                choices=["cm", "in", "ft"],
                value="cm",
                label="Units",
                elem_id="home-unit-selector",
                scale=0,
            )
            reload_btn = gr.Button(
                "Refresh",
                variant="secondary",
                size="sm",
                elem_id="home-reload-btn",
            )

        recent_cards_html = gr.HTML(
            value=(
                '<div style="text-align:center;color:#999;padding:30px 0;">'
                "No recent scenarios. Create your first one!</div>"
            ),
            elem_id="home-recent-cards",
        )

        # Pagination controls
        with gr.Row():
            prev_btn = gr.Button("← Previous", scale=1, size="sm")
            page_info = gr.HTML(
                value='<div style="text-align:center;padding:10px 0;">Page 1</div>',
                elem_id="home-page-info",
            )
            next_btn = gr.Button("Next →", scale=1, size="sm")

        # Hidden state for current page
        page_state = gr.State(value=1)

        # Cached data for client-side paging
        cards_cache_state = gr.State(value=[])
        fav_ids_cache_state = gr.State(value=[])

    return (
        container,
        create_btn,
        browse_btn,
        favorites_btn,
        mode_filter,
        preset_filter,
        unit_selector,
        reload_btn,
        recent_cards_html,
        prev_btn,
        page_info,
        next_btn,
        page_state,
        cards_cache_state,
        fav_ids_cache_state,
    )
