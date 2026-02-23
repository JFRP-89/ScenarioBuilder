"""Home page — landing screen with recent cards and quick actions.

Shows:
- Welcome header
- Quick-action buttons (Create New, Browse All, Favorites)
- CONTROL BAR with mode / preset / unit filters + circular refresh
- Recent cards list with pagination
"""

from __future__ import annotations

from types import SimpleNamespace

import gradio as gr

from adapters.ui_gradio.ui.components.control_bar import build_control_bar
from adapters.ui_gradio.ui.components.search_helpers import (
    DEFAULT_SORT,
    SORT_CHOICES,
)


def build_home_page() -> SimpleNamespace:
    """Build the home page layout.

    Returns:
        Tuple of (page_container, create_btn, browse_btn, favorites_btn,
                  mode_filter, preset_filter, unit_selector,
                  search_box, per_page_dropdown, reload_btn,
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

        gr.Markdown("### Community's Scenarios")

        # ── CONTROL BAR (filters + refresh) ──────────────────────────
        cb = build_control_bar(
            page_prefix="home",
            mode_choices=["All", "Casual", "Narrative", "Matched"],
            preset_choices=["All", "Standard", "Massive", "Custom"],
        )
        mode_filter = cb.mode_filter
        preset_filter = cb.preset_filter
        unit_selector = cb.unit_selector
        reload_btn = cb.reload_btn

        # Search, sort and per-page controls
        with gr.Row():
            search_box = gr.Textbox(
                label="Search by name",
                placeholder="e.g. Osgiliath",
                value="",
                elem_id="home-search-box",
                scale=3,
                max_lines=1,
            )
            sort_dropdown = gr.Dropdown(
                choices=SORT_CHOICES,
                value=DEFAULT_SORT,
                label="Sort by",
                elem_id="home-sort",
                scale=1,
            )
            per_page_dropdown = gr.Dropdown(
                choices=["5", "10", "20", "50", "100"],
                value="10",
                label="Per page",
                elem_id="home-per-page",
                scale=1,
            )

        recent_cards_html = gr.HTML(
            value=(
                '<div style="text-align:center;color:#5a7090;padding:30px 0;">'
                '<div style="font-size:2.5rem;margin-bottom:12px;opacity:.4;">\U0001f3b2</div>'
                "No community scenarios yet. Create your first one!</div>"
            ),
            elem_id="home-recent-cards",
        )

        # Pagination controls
        with gr.Row():
            prev_btn = gr.Button("← Previous", scale=1, size="sm")
            page_info = gr.HTML(
                value='<div style="text-align:center;padding:10px 0;color:#92a9c1;">Page 1</div>',
                elem_id="home-page-info",
            )
            next_btn = gr.Button("Next →", scale=1, size="sm")

        # Hidden state for current page
        page_state = gr.State(value=1)

        # Cached data for client-side paging
        cards_cache_state = gr.State(value=[])
        fav_ids_cache_state = gr.State(value=[])

    return SimpleNamespace(
        container=container,
        create_btn=create_btn,
        browse_btn=browse_btn,
        favorites_btn=favorites_btn,
        mode_filter=mode_filter,
        preset_filter=preset_filter,
        unit_selector=unit_selector,
        search_box=search_box,
        sort_dropdown=sort_dropdown,
        per_page_dropdown=per_page_dropdown,
        reload_btn=reload_btn,
        recent_cards_html=recent_cards_html,
        prev_btn=prev_btn,
        page_info=page_info,
        next_btn=next_btn,
        page_state=page_state,
        cards_cache_state=cards_cache_state,
        fav_ids_cache_state=fav_ids_cache_state,
    )
