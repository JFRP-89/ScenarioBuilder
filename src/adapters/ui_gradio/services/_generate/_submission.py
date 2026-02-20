"""Scenario submission handlers (create & update via direct use-case calls)."""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio._messages import MSG_NO_PREVIEW
from adapters.ui_gradio.services._generate._card_result import augment_generated_card
from application.use_cases.generate_scenario_card import GenerateScenarioCardRequest
from application.use_cases.save_card import SaveCardRequest
from domain.errors import DomainError
from infrastructure.bootstrap import get_services


def _gen_response_to_dict(gen_resp: Any) -> dict[str, Any]:
    """Convert a GenerateScenarioCardResponse dataclass to a plain dict."""
    return {
        "card_id": gen_resp.card_id,
        "seed": gen_resp.seed,
        "owner_id": gen_resp.owner_id,
        "name": gen_resp.name,
        "mode": gen_resp.mode,
        "armies": gen_resp.armies,
        "table_preset": gen_resp.table_preset,
        "table_mm": gen_resp.table_mm,
        "layout": gen_resp.layout,
        "deployment": gen_resp.deployment,
        "initial_priority": gen_resp.initial_priority,
        "objectives": gen_resp.objectives,
        "special_rules": gen_resp.special_rules,
        "visibility": gen_resp.visibility,
        "shared_with": gen_resp.shared_with or [],
        "shapes": gen_resp.shapes,
    }


def handle_create_scenario(preview_data: dict[str, Any]) -> dict[str, Any]:
    """Save a previewed card via direct use-case call.

    Args:
        preview_data: The preview dict returned by ``handle_preview``.

    Returns:
        Augmented card dict with ``card_id`` on success, or error dict.
    """
    if not preview_data or not isinstance(preview_data, dict):
        return {"status": "error", "message": MSG_NO_PREVIEW}

    if preview_data.get("status") == "error":
        return {
            "status": "error",
            "message": preview_data.get("message", "Previous generation failed."),
        }

    if preview_data.get("status") != "preview":
        return {"status": "error", "message": MSG_NO_PREVIEW}

    payload = preview_data.get("_payload")
    actor_id = preview_data.get("_actor_id", "")

    if not payload or not isinstance(payload, dict):
        return {"status": "error", "message": "No payload found. Generate a preview."}
    if not actor_id:
        return {"status": "error", "message": "No actor ID. Generate a preview."}

    try:
        svc = get_services()
        gen_req = GenerateScenarioCardRequest(actor_id=actor_id, **payload)
        gen_resp = svc.generate_scenario_card.execute(gen_req)

        save_req = SaveCardRequest(actor_id=actor_id, card=gen_resp.card)
        svc.save_card.execute(save_req)

        response_json = _gen_response_to_dict(gen_resp)
        preset = preview_data.get("table_preset", "")
        custom_table = payload.get("table_cm")
        return augment_generated_card(response_json, payload, preset, custom_table)

    except DomainError as exc:
        return {"status": "error", "message": f"Create failed: {exc}"}
    except (
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        OSError,
    ) as exc:
        import logging

        logging.getLogger(__name__).exception(
            "Unexpected error in handle_create_scenario: %s", exc
        )
        return {"status": "error", "message": "An unexpected error occurred."}


def handle_update_scenario(
    preview_data: dict[str, Any],
    card_id: str,
) -> dict[str, Any]:
    """Update an existing card via direct use-case call.

    Args:
        preview_data: The preview dict returned by ``handle_preview``.
        card_id: The existing card ID to update.

    Returns:
        Augmented card dict with ``card_id`` on success, or error dict.
    """
    if not card_id:
        return {"status": "error", "message": "No card ID for update."}
    if not preview_data or not isinstance(preview_data, dict):
        return {"status": "error", "message": MSG_NO_PREVIEW}

    if preview_data.get("status") == "error":
        return {
            "status": "error",
            "message": preview_data.get("message", "Previous generation failed."),
        }

    if preview_data.get("status") != "preview":
        return {"status": "error", "message": MSG_NO_PREVIEW}

    payload = preview_data.get("_payload")
    actor_id = preview_data.get("_actor_id", "")

    if not payload or not isinstance(payload, dict):
        return {"status": "error", "message": "No payload found. Generate a preview."}
    if not actor_id:
        return {"status": "error", "message": "No actor ID. Generate a preview."}

    try:
        svc = get_services()

        # Retrieve existing card to preserve seed
        from application.use_cases.get_card import GetCardRequest

        existing = svc.get_card.execute(
            GetCardRequest(actor_id=actor_id, card_id=card_id)
        )
        payload_with_seed = dict(payload)
        payload_with_seed["seed"] = existing.seed
        payload_with_seed["card_id"] = card_id

        gen_req = GenerateScenarioCardRequest(actor_id=actor_id, **payload_with_seed)
        gen_resp = svc.generate_scenario_card.execute(gen_req)

        save_req = SaveCardRequest(actor_id=actor_id, card=gen_resp.card)
        svc.save_card.execute(save_req)

        response_json = _gen_response_to_dict(gen_resp)
        preset = preview_data.get("table_preset", "")
        custom_table = payload.get("table_cm")
        return augment_generated_card(response_json, payload, preset, custom_table)

    except DomainError as exc:
        return {"status": "error", "message": f"Update failed: {exc}"}
    except (
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        OSError,
    ) as exc:
        import logging

        logging.getLogger(__name__).exception(
            "Unexpected error in handle_update_scenario: %s", exc
        )
        return {"status": "error", "message": "An unexpected error occurred."}
