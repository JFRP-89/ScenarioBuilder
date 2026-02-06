"""Scenario metadata section (name, mode, seed, armies)."""

from typing import Any

import gradio as gr


def build_scenario_meta_section() -> tuple[Any, Any, Any, Any]:
    """Build scenario metadata UI components.

    Returns:
        Tuple of (scenario_name, mode, seed, armies)
    """
    # Scenario Name
    with gr.Row():
        scenario_name = gr.Textbox(
            label="Scenario Name",
            placeholder="Enter scenario name",
            elem_id="scenario-name-input",
        )

    # Game Mode and Seed
    with gr.Row():
        mode = gr.Dropdown(
            choices=["casual", "narrative", "matched"],
            value="casual",
            label="Game Mode",
            elem_id="mode-dropdown",
        )
        seed = gr.Number(value=1, precision=0, label="Seed", elem_id="seed-input")

    # Armies
    with gr.Row():
        armies = gr.Textbox(
            label="Armies",
            placeholder="e.g., Rules from core rulebook, or custom army points...",
            lines=2,
            elem_id="armies-input",
        )

    return scenario_name, mode, seed, armies
