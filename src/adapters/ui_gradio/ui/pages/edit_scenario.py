"""Edit scenario page — placeholder for future editing functionality.

For now, opens as read-only with a note that editing is planned.
Re-uses the detail page layout plus an informational banner.
"""

from __future__ import annotations

import gradio as gr


def build_edit_page() -> tuple[
    gr.Column,
    gr.Markdown,
    gr.HTML,
    gr.JSON,
    gr.Button,
]:
    """Build the edit-scenario page layout.

    Returns:
        Tuple of (page_container, card_title_md, svg_preview,
                  card_json, back_btn).
    """
    with gr.Column(visible=False, elem_id="page-edit-scenario") as container:
        with gr.Row():
            back_btn = gr.Button(
                "← Back",
                variant="secondary",
                size="sm",
                elem_id="edit-back-btn",
            )
            card_title_md = gr.Markdown(
                "## Edit Scenario",
                elem_id="edit-title",
            )

        gr.Markdown(
            "> **Note:** Full editing is planned for a future release. "
            "Currently you can view the card details here."
        )

        svg_preview = gr.HTML(
            value=(
                '<div style="display:flex;align-items:center;'
                "justify-content:center;height:300px;"
                "border:2px dashed #ccc;border-radius:8px;"
                'color:#999;font-size:14px;">'
                "Map preview</div>"
            ),
            elem_id="edit-svg-preview",
        )
        card_json = gr.JSON(
            label="Card Data",
            elem_id="edit-card-json",
        )

    return container, card_title_md, svg_preview, card_json, back_btn
