"""Scenario metadata section (name, mode, seed, armies)."""

from typing import Any

import gradio as gr


def build_scenario_meta_section() -> tuple[Any, Any, Any, Any]:
    """Build scenario metadata UI components.

    Returns:
        Tuple of (scenario_name, mode, is_replicable, armies)
    """
    # Scenario Name
    with gr.Row():
        scenario_name = gr.Textbox(
            label="Scenario Name",
            placeholder="Enter scenario name",
            elem_id="scenario-name-input",
        )

    # Game Mode and Replicable
    with gr.Row():
        mode = gr.Dropdown(
            choices=["casual", "narrative", "matched"],
            value="casual",
            label="Game Mode",
            elem_id="mode-dropdown",
        )
        is_replicable = gr.Checkbox(
            value=True,
            label="Replicable Scenario",
            info="Generate reproducible scenario with deterministic seed",
            elem_id="is-replicable-checkbox",
        )

    # Armies
    with gr.Row():
        armies = gr.Textbox(
            label="Armies",
            placeholder="e.g., Rules from core rulebook, or custom army points...",
            lines=2,
            elem_id="armies-input",
        )

    return scenario_name, mode, is_replicable, armies
