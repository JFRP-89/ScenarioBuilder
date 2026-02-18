"""Scenario detail page — read-only view of a single card.

Shows:
- Scenario name (title)
- SVG map preview
- All mandatory fields (owner, mode, seed, armies, visibility, table, etc.)
- Conditional sections: shared_with, victory_points, special_rules
- Back button
"""

from __future__ import annotations

from types import SimpleNamespace

import gradio as gr


def build_detail_page() -> SimpleNamespace:
    """Build the scenario-detail page layout.

    Returns:
        Tuple of (page_container, card_title_md, svg_preview,
                  detail_content_html, edit_btn, delete_btn,
                  delete_confirm_row, delete_confirm_msg,
                  delete_confirm_btn, delete_cancel_btn,
                  favorite_btn, back_btn).
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
                visible=False,
                elem_id="detail-edit-btn",
            )
            delete_btn = gr.Button(
                "🗑️ Delete",
                variant="stop",
                visible=False,
                elem_id="detail-delete-btn",
            )
            favorite_btn = gr.Button(
                "⭐ Toggle Favorite",
                variant="secondary",
                elem_id="detail-favorite-btn",
            )

        # Confirmation row (hidden by default)
        with gr.Row(visible=False, elem_id="delete-confirm-row") as delete_confirm_row:
            delete_confirm_msg = gr.Markdown(
                "⚠️ **Are you sure you want to delete this scenario? "
                "This action cannot be undone.**",
                elem_id="delete-confirm-msg",
            )
            delete_confirm_btn = gr.Button(
                "Yes, delete",
                variant="stop",
                size="sm",
                elem_id="delete-confirm-btn",
            )
            delete_cancel_btn = gr.Button(
                "Cancel",
                variant="secondary",
                size="sm",
                elem_id="delete-cancel-btn",
            )

    return SimpleNamespace(
        container=container,
        card_title_md=card_title_md,
        svg_preview=svg_preview,
        detail_content_html=detail_content_html,
        edit_btn=edit_btn,
        delete_btn=delete_btn,
        delete_confirm_row=delete_confirm_row,
        delete_confirm_msg=delete_confirm_msg,
        delete_confirm_btn=delete_confirm_btn,
        delete_cancel_btn=delete_cancel_btn,
        favorite_btn=favorite_btn,
        back_btn=back_btn,
    )
