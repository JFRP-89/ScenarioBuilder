"""Scenario metadata section (name, mode, seed, armies)."""

from typing import Any

import gradio as gr


def build_scenario_meta_section() -> tuple[Any, Any, Any, Any, Any, Any]:
    """Build scenario metadata UI components.

    Returns:
        Tuple of (scenario_name, mode, is_replicable, generate_from_seed,
                  apply_seed_btn, armies)
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
            info="Design every field manually from scratch",
            elem_id="is-replicable-checkbox",
        )

    # Generate Scenario From Seed (enabled when is_replicable is True)
    with gr.Row():
        generate_from_seed = gr.Number(
            label="Generate Scenario From Seed",
            value=None,
            precision=0,
            minimum=1,
            interactive=True,  # Starts enabled (is_replicable defaults True)
            info="Enter a seed number to auto-fill the scenario (requires Replicable Scenario)",
            elem_id="generate-from-seed-input",
        )
        apply_seed_btn = gr.Button(
            "\U0001f3b2 Apply Seed",
            variant="secondary",
            size="sm",
            interactive=True,
            elem_id="apply-seed-btn",
        )

    # Armies
    with gr.Row():
        armies = gr.Textbox(
            label="Armies",
            placeholder="e.g., Rules from core rulebook, or custom army points...",
            lines=2,
            elem_id="armies-input",
        )

    return (
        scenario_name,
        mode,
        is_replicable,
        generate_from_seed,
        apply_seed_btn,
        armies,
    )
