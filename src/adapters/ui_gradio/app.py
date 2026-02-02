"""Gradio UI adapter for ScenarioBuilder."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

# Add src to path if running as script (not as module)
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

import gradio as gr

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None

from adapters.ui_gradio.constants import (
    DEFAULT_TABLE_PRESET,
    ENDPOINT_GENERATE_CARD,
    ERROR_API_FAILURE,
    ERROR_REQUEST_FAILED,
    ERROR_REQUESTS_NOT_AVAILABLE,
    ERROR_UNEXPECTED,
    FIELD_MODE,
    FIELD_SEED,
    FIELD_TABLE_PRESET,
    REQUEST_TIMEOUT_SECONDS,
    SUCCESS_STATUS_CODES,
)


# =============================================================================
# Helper functions
# =============================================================================
def _get_default_actor_id() -> str:
    """Get default actor ID from environment."""
    return os.environ.get("DEFAULT_ACTOR_ID", "demo-user")


def _get_api_base_url() -> str:
    """Get API base URL from environment and normalize (remove trailing slash).

    Returns:
        str: API base URL without trailing slash (e.g., "http://localhost:8000")
    """
    default = "http://localhost:8000"
    api_url = os.environ.get("API_BASE_URL", default)
    # Remove trailing slash if present
    return api_url.rstrip("/")


def _build_headers(actor_id: str) -> dict[str, str]:
    """Build HTTP headers for API requests.

    Args:
        actor_id: Actor ID to include in header

    Returns:
        dict: Headers dict with X-Actor-Id
    """
    return {"X-Actor-Id": actor_id}


def _build_payload(mode: str, seed: int | None) -> dict:
    """Build request payload for card generation.

    Args:
        mode: Game mode
        seed: Random seed (can be None)

    Returns:
        dict: Payload ready for POST
    """
    return {
        FIELD_MODE: mode,
        FIELD_SEED: int(seed) if seed else None,
        FIELD_TABLE_PRESET: DEFAULT_TABLE_PRESET,
    }


def _call_api_generate_card(
    base_url: str, headers: dict[str, str], payload: dict
) -> requests.Response | None:
    """Call the API to generate a card.

    Args:
        base_url: API base URL
        headers: HTTP headers
        payload: Request payload

    Returns:
        Response object or None if request failed
    """
    if not requests:
        return None

    try:
        response = requests.post(
            f"{base_url}{ENDPOINT_GENERATE_CARD}",
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return response
    except requests.RequestException:
        return None


def _normalize_error(response: requests.Response | None, exc: Exception | None = None) -> dict:
    """Normalize error response into consistent JSON format.

    Args:
        response: HTTP response (if available)
        exc: Exception (if available)

    Returns:
        dict: Error response with status and message
    """
    if exc is not None:
        if isinstance(exc, requests.RequestException):
            return {
                "status": "error",
                "message": f"{ERROR_REQUEST_FAILED}: {exc!s}",
            }
        return {"status": "error", "message": f"{ERROR_UNEXPECTED}: {exc!s}"}

    if response is None:
        return {"status": "error", "message": ERROR_REQUESTS_NOT_AVAILABLE}

    return {
        "status": "error",
        "message": f"{ERROR_API_FAILURE}: {response.status_code}",
    }


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
                elem_id="actor-id-input",
            )

        with gr.Row():
            mode = gr.Dropdown(
                choices=["casual", "narrative", "matched"],
                value="casual",
                label="Game Mode",
                elem_id="mode-dropdown",
            )
            seed = gr.Number(value=1, precision=0, label="Seed", elem_id="seed-input")

        generate_btn = gr.Button("Generate Card", variant="primary", elem_id="generate-button")
        output = gr.JSON(label="Generated Card", elem_id="result-json")

        def _handle_generate(actor: str, m: str, s: int) -> dict:
            """Generate a scenario card via HTTP API call."""
            try:
                api_url = _get_api_base_url()
                headers = _build_headers(actor.strip())
                payload = _build_payload(m, s)

                response = _call_api_generate_card(api_url, headers, payload)

                # Handle API call failure
                if response is None:
                    return _normalize_error(None)

                # Handle non-success HTTP status
                if response.status_code not in SUCCESS_STATUS_CODES:
                    return _normalize_error(response)

                # Return successful response
                return cast(dict[Any, Any], response.json())

            except requests.RequestException as exc:
                return _normalize_error(None, exc)
            except Exception as exc:
                return _normalize_error(None, exc)

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
        server_name=os.environ.get("UI_HOST", "0.0.0.0"),  # nosec B104 - container/local dev
        server_port=int(os.environ.get("UI_PORT", "7860")),
    )
