"""Scenario submission handlers (create & update via HTTP API)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import requests
else:
    try:
        import requests  # type: ignore[import-untyped]
    except ImportError:
        requests = None  # type: ignore[assignment]

from adapters.ui_gradio import api_client
from adapters.ui_gradio.constants import SUCCESS_STATUS_CODES
from adapters.ui_gradio.services._generate._card_result import augment_generated_card


def handle_create_scenario(preview_data: dict[str, Any]) -> dict[str, Any]:
    """Send a previewed card to the Flask API for actual creation.

    Args:
        preview_data: The preview dict returned by ``handle_preview``.

    Returns:
        API response dict with ``card_id`` on success, or error dict.
    """
    if not preview_data or not isinstance(preview_data, dict):
        return {"status": "error", "message": "Generate a card preview first."}

    if preview_data.get("status") == "error":
        return {
            "status": "error",
            "message": preview_data.get("message", "Previous generation failed."),
        }

    if preview_data.get("status") != "preview":
        return {"status": "error", "message": "Generate a card preview first."}

    payload = preview_data.get("_payload")
    actor_id = preview_data.get("_actor_id", "")

    if not payload or not isinstance(payload, dict):
        return {"status": "error", "message": "No payload found. Generate a preview."}
    if not actor_id:
        return {"status": "error", "message": "No actor ID. Generate a preview."}

    try:
        api_url = api_client.get_api_base_url()
        headers = api_client.build_headers(actor_id)
        response = api_client.post_generate_card(api_url, headers, payload)

        if response is None:
            return cast(dict[str, Any], api_client.normalize_error(None))

        if response.status_code not in SUCCESS_STATUS_CODES:
            return cast(dict[str, Any], api_client.normalize_error(response))

        response_json = cast(dict[Any, Any], response.json())
        preset = preview_data.get("table_preset", "")
        custom_table = payload.get("table_cm")
        return augment_generated_card(response_json, payload, preset, custom_table)  # type: ignore[no-any-return]

    except Exception as exc:
        return cast(dict[str, Any], api_client.normalize_error(None, exc))


def handle_update_scenario(
    preview_data: dict[str, Any],
    card_id: str,
) -> dict[str, Any]:
    """Send a previewed card to the Flask API as an update (PUT).

    Args:
        preview_data: The preview dict returned by ``handle_preview``.
        card_id: The existing card ID to update.

    Returns:
        API response dict with ``card_id`` on success, or error dict.
    """
    if not card_id:
        return {"status": "error", "message": "No card ID for update."}
    if not preview_data or not isinstance(preview_data, dict):
        return {"status": "error", "message": "Generate a card preview first."}

    if preview_data.get("status") == "error":
        return {
            "status": "error",
            "message": preview_data.get("message", "Previous generation failed."),
        }

    if preview_data.get("status") != "preview":
        return {"status": "error", "message": "Generate a card preview first."}

    payload = preview_data.get("_payload")
    actor_id = preview_data.get("_actor_id", "")

    if not payload or not isinstance(payload, dict):
        return {"status": "error", "message": "No payload found. Generate a preview."}
    if not actor_id:
        return {"status": "error", "message": "No actor ID. Generate a preview."}

    try:
        api_url = api_client.get_api_base_url()
        headers = api_client.build_headers(actor_id)
        response = api_client.put_update_card(api_url, headers, card_id, payload)

        if response is None:
            return cast(dict[str, Any], api_client.normalize_error(None))

        if response.status_code not in SUCCESS_STATUS_CODES:
            return cast(dict[str, Any], api_client.normalize_error(response))

        response_json = cast(dict[Any, Any], response.json())
        preset = preview_data.get("table_preset", "")
        custom_table = payload.get("table_cm")
        return augment_generated_card(response_json, payload, preset, custom_table)  # type: ignore[no-any-return]

    except Exception as exc:
        return cast(dict[str, Any], api_client.normalize_error(None, exc))
