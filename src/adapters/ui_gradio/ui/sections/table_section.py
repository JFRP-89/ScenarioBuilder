"""Table configuration section."""

from typing import Any

import gradio as gr


def build_table_section() -> tuple[Any, Any, Any, Any, Any, Any]:
    """Build table configuration UI components.

    Returns:
        Tuple of (table_preset, prev_unit_state, custom_table_row,
                 table_width, table_height, table_unit)
    """
    gr.Markdown("## Table Configuration")
    gr.Markdown(
        "_Standard: 120x120 cm | Massive: 180x120 cm | Custom: 60-300 cm (24-120 in, 2-10 ft)_"
    )
    with gr.Row():
        table_preset = gr.Radio(
            choices=["standard", "massive", "custom"],
            value="standard",
            label="Table Preset",
            elem_id="table-preset",
        )

    prev_unit_state = gr.State("cm")

    with gr.Row(visible=False) as custom_table_row:
        table_width = gr.Number(
            value=120, precision=2, label="Width", elem_id="table-width"
        )
        table_height = gr.Number(
            value=120, precision=2, label="Height", elem_id="table-height"
        )
        table_unit = gr.Radio(
            choices=["cm", "in", "ft"],
            value="cm",
            label="Unit",
            elem_id="table-unit",
        )

    return (
        table_preset,
        prev_unit_state,
        custom_table_row,
        table_width,
        table_height,
        table_unit,
    )
