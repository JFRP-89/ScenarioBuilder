"""Generate-button event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio.services.generate import handle_generate
from adapters.ui_gradio.ui.components.svg_preview import render_svg_from_card


def wire_generate(
    *,
    actor_id: gr.Textbox,
    scenario_name: gr.Textbox,
    mode: gr.Radio,
    seed: gr.Number,
    armies: gr.Textbox,
    table_preset: gr.Radio,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    deployment: gr.Textbox,
    layout: gr.Textbox,
    objectives: gr.Textbox,
    initial_priority: gr.Textbox,
    special_rules_state: gr.State,
    visibility: gr.Radio,
    shared_with: gr.Textbox,
    scenography_state: gr.State,
    deployment_zones_state: gr.State,
    objective_points_state: gr.State,
    objectives_with_vp_toggle: gr.Checkbox,
    vp_state: gr.State,
    generate_btn: gr.Button,
    svg_preview: gr.HTML,
    output: gr.JSON,
) -> None:
    """Wire generate button click."""

    def _generate_and_render(
        *args: Any,
    ) -> tuple[dict[str, Any], str]:
        """Generate card and render SVG preview."""
        card_data = handle_generate(*args)
        svg_html = render_svg_from_card(card_data)
        return card_data, svg_html

    generate_btn.click(
        fn=_generate_and_render,
        inputs=[
            actor_id,
            scenario_name,
            mode,
            seed,
            armies,
            table_preset,
            table_width,
            table_height,
            table_unit,
            deployment,
            layout,
            objectives,
            initial_priority,
            special_rules_state,
            visibility,
            shared_with,
            scenography_state,
            deployment_zones_state,
            objective_points_state,
            objectives_with_vp_toggle,
            vp_state,
        ],
        outputs=[output, svg_preview],
    )
