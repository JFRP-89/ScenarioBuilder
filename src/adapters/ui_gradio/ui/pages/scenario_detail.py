"""Scenario detail page — read-only view of a single card.

Shows:
- Scenario name (title)
- SVG map preview
- All mandatory fields (owner, mode, seed, armies, visibility, table, etc.)
- Conditional sections: shared_with, victory_points, special_rules
- Back button
"""

from __future__ import annotations

import gradio as gr


def build_detail_page() -> tuple[
    gr.Column,
    gr.Markdown,
    gr.HTML,
    gr.HTML,
    gr.Button,
    gr.Button,
    gr.Button,
]:
    """Build the scenario-detail page layout.

    Returns:
        Tuple of (page_container, card_title_md, svg_preview,
                  detail_content_html, edit_btn, favorite_btn, back_btn).
    """
    with gr.Column(visible=False, elem_id="page-scenario-detail") as container:
        with gr.Row():
            back_btn = gr.Button(
                "← Back",
                variant="secondary",
                size="sm",
                elem_id="detail-back-btn",
            )
            card_title_md = gr.Markdown(
                "## Scenario Detail",
                elem_id="detail-title",
            )

        # SVG map preview (centered, styled)
        svg_preview = gr.HTML(
            value=(
                '<div style="display:flex;align-items:center;'
                "justify-content:center;height:300px;"
                "border:2px dashed #ccc;border-radius:8px;"
                'color:#999;font-size:14px;">'
                "Map preview</div>"
            ),
            elem_id="detail-svg-preview",
        )

        # Main content area — rendered as styled HTML
        detail_content_html = gr.HTML(
            value='<div style="color:#999;text-align:center;">Loading...</div>',
            elem_id="detail-content-html",
        )

        with gr.Row():
            edit_btn = gr.Button(
                "✏️ Edit",
                variant="secondary",
                elem_id="detail-edit-btn",
            )
            favorite_btn = gr.Button(
                "⭐ Toggle Favorite",
                variant="secondary",
                elem_id="detail-favorite-btn",
            )

    return (
        container,
        card_title_md,
        svg_preview,
        detail_content_html,
        edit_btn,
        favorite_btn,
        back_btn,
    )
