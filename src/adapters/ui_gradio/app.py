"""Gradio UI adapter for ScenarioBuilder."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to path if running as script (not as module)
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

import gradio as gr

from application.use_cases.generate_scenario_card import GenerateScenarioCardRequest
from domain.errors import ValidationError
from infrastructure.bootstrap import build_services


# =============================================================================
# Helper functions
# =============================================================================
def _get_default_actor_id() -> str:
    """Get default actor ID from environment."""
    return os.environ.get("DEFAULT_ACTOR_ID", "demo-user")


# =============================================================================
# App builder
# =============================================================================
def build_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app.

    This function constructs the UI without making any HTTP calls.
    HTTP calls only happen when user interacts with the UI.

    Returns:
        A gradio.Blocks instance ready to launch
    """
    with gr.Blocks(title="Scenario Card Generator") as app:
        gr.Markdown("# Scenario Card Generator")

        with gr.Row():
            actor_id = gr.Textbox(
                label="Actor ID",
                value=_get_default_actor_id(),
                placeholder="Enter your actor ID",
            )

        with gr.Row():
            mode = gr.Dropdown(
                choices=["casual", "narrative", "matched"],
                value="casual",
                label="Game Mode",
            )
            seed = gr.Number(value=1, precision=0, label="Seed")

        generate_btn = gr.Button("Generate Card", variant="primary")
        output = gr.JSON(label="Generated Card")

        # Initialize services once at app creation
        services = build_services()

        def _handle_generate(actor: str, m: str, s: int) -> dict:
            """Generate a scenario card using the real use case."""
            try:
                # Build request DTO with all required fields
                request = GenerateScenarioCardRequest(
                    actor_id=actor.strip(),
                    mode=m,
                    seed=int(s) if s else None,
                    visibility="private",
                    table_preset="standard",
                    shared_with=[],
                )

                # Execute use case
                response = services.generate_scenario_card.execute(request)

                # GenerateScenarioCardResponse only has: card_id, mode, seed, table_mm
                return {
                    "card_id": response.card_id,
                    "mode": response.mode,
                    "seed": response.seed,
                    "table_mm": response.table_mm,
                }
            except ValidationError as e:
                return {
                    "status": "error",
                    "error": str(e),
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Unexpected error: {str(e)}",
                }

        generate_btn.click(
            fn=_handle_generate,
            inputs=[actor_id, mode, seed],
            outputs=output,
        )

    return app


# =============================================================================
# Main entry point
# =============================================================================
if __name__ == "__main__":
    build_app().launch(
        server_name=os.environ.get("UI_HOST", "0.0.0.0"),
        server_port=int(os.environ.get("UI_PORT", "7860")),
    )
