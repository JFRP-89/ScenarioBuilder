"""Pure validation logic for the create-scenario flow."""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio._messages import MSG_NO_PREVIEW as _MSG_NO_PREVIEW


def validate_preview_data(preview_data: Any) -> tuple[bool, str]:
    """Validate preview_data before calling the API.

    Returns ``(True, "")`` when valid, or ``(False, error_message)``
    when the data should be rejected.

    This function is **pure** — no Gradio, no I/O — easy to unit-test.
    """
    if not preview_data or not isinstance(preview_data, dict):
        return False, _MSG_NO_PREVIEW

    if preview_data.get("status") == "error":
        msg = preview_data.get("message", "Generation failed")
        return False, f"Error: {msg}"

    if preview_data.get("status") != "preview":
        return False, _MSG_NO_PREVIEW

    return True, ""
