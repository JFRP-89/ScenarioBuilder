"""Gradio UI adapter for ScenarioBuilder."""

from __future__ import annotations

import os

import gradio as gr


# =============================================================================
# Helper functions
# =============================================================================
def _get_api_base_url() -> str:
    """Get API base URL from environment, with normalization.

    Returns:
        URL string without trailing slash, defaults to http://localhost:5000
    """
    url = os.environ.get("API_BASE_URL", "http://localhost:5000")
    return url.rstrip("/")


def _build_headers(actor_id: str) -> dict[str, str]:
    """Build HTTP headers with actor identification.

    Args:
        actor_id: The actor/user identifier

    Returns:
        Dict with X-Actor-Id header
    """
    return {"X-Actor-Id": actor_id}


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

        # Placeholder handler - actual HTTP logic to be added later
        def _placeholder_generate(actor: str, m: str, s: int) -> dict:
            """Placeholder that returns local data without HTTP calls."""
            return {
                "status": "placeholder",
                "actor_id": actor,
                "mode": m,
                "seed": int(s),
                "message": "Real generation requires API connection",
            }

        generate_btn.click(
            fn=_placeholder_generate,
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
