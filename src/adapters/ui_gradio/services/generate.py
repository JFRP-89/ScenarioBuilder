"""Generate service for Gradio UI adapter.

Builds payload, validates inputs, calls API, and normalizes response.
"""

from __future__ import annotations

import os
from typing import Any, cast

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None

from adapters.ui_gradio import api_client
from adapters.ui_gradio.builders import payload as payload_builder
from adapters.ui_gradio.builders import shapes as shapes_builder
from adapters.ui_gradio.constants import (
    FIELD_MODE,
    FIELD_SEED,
    SUCCESS_STATUS_CODES,
    TABLE_MASSIVE_CM,
    TABLE_STANDARD_CM,
)


def handle_preview(  # noqa: C901
    actor: str,
    name: str,
    m: str,
    s: int,
    armies_val: str,
    preset: str,
    width: float,
    height: float,
    unit: str,
    depl: str,
    lay: str,
    obj: str,
    init_priority: str,
    rules_state: list[dict[str, Any]],
    vis: str,
    shared: str,
    scenography_state_val: list[dict[str, Any]],
    deployment_zones_state_val: list[dict[str, Any]],
    objective_points_state_val: list[dict[str, Any]],
    objectives_with_vp_enabled: bool,
    vp_state: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a preview card locally (validate + build payload + shapes).

    Does NOT call the Flask API. Returns a preview dict with all
    data needed for SVG rendering and for later submission via
    ``handle_create_scenario``.
    """
    try:
        default_actor_id = _get_default_actor_id()
        validation_error = payload_builder.validate_required_fields(
            actor=actor,
            name=name,
            m=m,
            armies_val=armies_val,
            preset=preset,
            width=width,
            height=height,
            unit=unit,
            depl=depl,
            lay=lay,
            obj=obj,
            init_priority=init_priority,
            rules_state=rules_state,
            vp_state=vp_state,
            deployment_zones_state_val=deployment_zones_state_val,
            objective_points_state_val=objective_points_state_val,
            scenography_state_val=scenography_state_val,
            default_actor_id=default_actor_id,
        )
        if validation_error:
            return {"status": "error", "message": validation_error}

        actor_id = (actor or "").strip() or default_actor_id
        if not actor_id:
            return {"status": "error", "message": "Actor ID is required."}

        payload = payload_builder.build_generate_payload(m, s)

        if name.strip():
            payload["name"] = name.strip()

        custom_table, error = payload_builder.apply_table_config(
            payload, preset, width, height, unit
        )
        if error:
            return cast(dict[str, Any], error)

        payload_builder.apply_optional_text_fields(
            payload,
            deployment=depl,
            layout=lay,
            objectives=obj,
            armies=armies_val,
        )

        if objectives_with_vp_enabled and vp_state:
            normalized_vps, error_msg = payload_builder.validate_victory_points(
                vp_state
            )
            if error_msg:
                return {"status": "error", "message": error_msg}
            assert normalized_vps is not None
            objectives_dict: dict[str, Any] = {
                "objective": obj.strip() if obj.strip() else ""
            }
            if len(normalized_vps) > 0:
                objectives_dict["victory_points"] = normalized_vps
            if objectives_dict.get("objective"):
                payload["objectives"] = objectives_dict

        if init_priority.strip():
            payload["initial_priority"] = init_priority.strip()

        error_sr = _apply_special_rules(payload, rules_state)
        if error_sr:
            return cast(dict[str, Any], error_sr)

        payload_builder.apply_visibility(payload, vis, shared)

        # -- Build shapes locally (for SVG preview) ---------------------
        scenography_specs: list[dict[str, Any]] = []
        if scenography_state_val:
            scenography_specs = shapes_builder.build_map_specs_from_state(
                scenography_state_val
            )
            payload["map_specs"] = scenography_specs

        deployment_shapes: list[dict[str, Any]] = []
        if deployment_zones_state_val:
            deployment_shapes = shapes_builder.build_deployment_shapes_from_state(
                deployment_zones_state_val
            )
            payload["deployment_shapes"] = deployment_shapes

        objective_shapes: list[dict[str, Any]] = []
        if objective_points_state_val:
            objective_shapes = shapes_builder.build_objective_shapes_from_state(
                objective_points_state_val
            )
            payload["objective_shapes"] = objective_shapes

        # -- Compute table_mm locally -----------------------------------
        if custom_table:
            table_mm = _build_table_mm_from_cm(custom_table)
        else:
            cm = _table_cm_from_preset(preset)
            table_mm = _build_table_mm_from_cm(cm)

        # -- Build preview result (NOT persisted) -----------------------
        preview: dict[str, Any] = {
            "status": "preview",
            "name": name.strip(),
            FIELD_MODE: m,
            FIELD_SEED: int(s) if s else None,
            "armies": armies_val.strip() if armies_val else "",
            "table_preset": preset,
            "table_mm": table_mm,
            "deployment": depl.strip() if depl else "",
            "layout": lay.strip() if lay else "",
            "objectives": obj.strip() if obj else "",
            "initial_priority": init_priority.strip() if init_priority else "",
            "visibility": vis,
            "shapes": {
                "deployment_shapes": deployment_shapes,
                "objective_shapes": objective_shapes,
                "scenography_specs": scenography_specs,
            },
            "_payload": payload,
            "_actor_id": actor_id,
        }
        if payload.get("special_rules"):
            preview["special_rules"] = payload["special_rules"]
        if payload.get("shared_with"):
            preview["shared_with"] = payload["shared_with"]

        return preview

    except Exception as exc:
        return {"status": "error", "message": f"Preview failed: {exc}"}


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
        return _augment_generated_card(response_json, payload, preset, custom_table)

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
        return _augment_generated_card(response_json, payload, preset, custom_table)

    except Exception as exc:
        return cast(dict[str, Any], api_client.normalize_error(None, exc))


def _table_cm_from_preset(preset: str) -> dict[str, float]:
    """Return table dimensions in cm for a known preset."""
    if preset == "massive":
        w, h = TABLE_MASSIVE_CM
    else:
        w, h = TABLE_STANDARD_CM
    return {"width_cm": float(w), "height_cm": float(h)}


def handle_generate(  # noqa: C901
    actor: str,
    name: str,
    m: str,
    s: int,
    armies_val: str,
    preset: str,
    width: float,
    height: float,
    unit: str,
    depl: str,
    lay: str,
    obj: str,
    init_priority: str,
    rules_state: list[dict[str, Any]],
    vis: str,
    shared: str,
    scenography_state_val: list[dict[str, Any]],
    deployment_zones_state_val: list[dict[str, Any]],
    objective_points_state_val: list[dict[str, Any]],
    objectives_with_vp_enabled: bool,
    vp_state: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a scenario card via HTTP API call."""
    try:
        default_actor_id = _get_default_actor_id()
        validation_error = payload_builder.validate_required_fields(
            actor=actor,
            name=name,
            m=m,
            armies_val=armies_val,
            preset=preset,
            width=width,
            height=height,
            unit=unit,
            depl=depl,
            lay=lay,
            obj=obj,
            init_priority=init_priority,
            rules_state=rules_state,
            vp_state=vp_state,
            deployment_zones_state_val=deployment_zones_state_val,
            objective_points_state_val=objective_points_state_val,
            scenography_state_val=scenography_state_val,
            default_actor_id=default_actor_id,
        )
        if validation_error:
            return {"status": "error", "message": validation_error}

        api_url = api_client.get_api_base_url()
        actor_id = (actor or "").strip()
        if not actor_id:
            actor_id = default_actor_id
        if not actor_id:
            return {"status": "error", "message": "Actor ID is required."}
        headers = api_client.build_headers(actor_id)

        payload = payload_builder.build_generate_payload(m, s)

        if name.strip():
            payload["name"] = name.strip()

        custom_table, error = payload_builder.apply_table_config(
            payload, preset, width, height, unit
        )
        if error:
            return cast(dict[str, Any], error)

        payload_builder.apply_optional_text_fields(
            payload,
            deployment=depl,
            layout=lay,
            objectives=obj,
            armies=armies_val,
        )

        if objectives_with_vp_enabled and vp_state:
            normalized_vps, error_msg = payload_builder.validate_victory_points(
                vp_state
            )
            if error_msg:
                return {"status": "error", "message": error_msg}

            assert (
                normalized_vps is not None
            ), "normalized_vps should not be None after validation"

            objectives_dict: dict[str, Any] = {
                "objective": obj.strip() if obj.strip() else ""
            }
            if len(normalized_vps) > 0:
                objectives_dict["victory_points"] = normalized_vps

            if objectives_dict.get("objective"):
                payload["objectives"] = objectives_dict

        if init_priority.strip():
            payload["initial_priority"] = init_priority.strip()

        error = _apply_special_rules(payload, rules_state)
        if error:
            return cast(dict[str, Any], error)

        payload_builder.apply_visibility(payload, vis, shared)

        if scenography_state_val:
            map_specs_payload = shapes_builder.build_map_specs_from_state(
                scenography_state_val
            )
            payload["map_specs"] = map_specs_payload

        if deployment_zones_state_val:
            deployment_shapes_payload = (
                shapes_builder.build_deployment_shapes_from_state(
                    deployment_zones_state_val
                )
            )
            payload["deployment_shapes"] = deployment_shapes_payload

        if objective_points_state_val:
            objective_shapes_payload = shapes_builder.build_objective_shapes_from_state(
                objective_points_state_val
            )
            payload["objective_shapes"] = objective_shapes_payload

        response = api_client.post_generate_card(api_url, headers, payload)

        if response is None:
            return cast(dict[str, Any], api_client.normalize_error(None))

        if response.status_code not in SUCCESS_STATUS_CODES:
            return cast(dict[str, Any], api_client.normalize_error(response))

        response_json = cast(dict[Any, Any], response.json())
        return _augment_generated_card(response_json, payload, preset, custom_table)

    except requests.RequestException as exc:
        return cast(dict[str, Any], api_client.normalize_error(None, exc))
    except Exception as exc:
        return cast(dict[str, Any], api_client.normalize_error(None, exc))


def _get_default_actor_id() -> str:
    """Get default actor ID from environment."""
    return os.environ.get("DEFAULT_ACTOR_ID", "demo-user")


def _apply_special_rules(
    payload: dict[str, Any],
    rules_state: list[dict[str, Any]],
) -> dict[str, str] | None:
    """Validate and add special_rules to payload with UI error prefix."""
    error = payload_builder.apply_special_rules(payload, rules_state)
    if error and "message" in error:
        error["message"] = f"Special Rules: {error['message']}"
    return cast(dict[str, str] | None, error)


def _build_table_mm_from_cm(table_cm: dict[str, float]) -> dict[str, int]:
    """Convert table sizes from cm to mm."""
    return {
        "width_mm": int(round(table_cm["width_cm"] * 10)),
        "height_mm": int(round(table_cm["height_cm"] * 10)),
    }


def _reorder_table_dimensions(table: Any, width_key: str, height_key: str) -> Any:
    """Return table dict with width key before height key."""
    if not isinstance(table, dict):
        return table

    ordered: dict[str, Any] = {}
    if width_key in table:
        ordered[width_key] = table[width_key]
    if height_key in table:
        ordered[height_key] = table[height_key]
    return ordered or table


def _augment_generated_card(  # noqa: C901
    response_json: dict[str, Any],
    payload: dict[str, Any],
    preset: str,
    custom_table: dict[str, float] | None,
) -> dict[str, Any]:
    """Ensure displayed card includes UI fields and returns in exact order."""
    result = dict(response_json)

    if preset:
        result.setdefault("table_preset", preset)

    if custom_table:
        result["table_mm"] = _build_table_mm_from_cm(custom_table)
        if "table_cm" in result:
            result.pop("table_cm")

    for key in (
        FIELD_MODE,
        FIELD_SEED,
        "armies",
        "deployment",
        "layout",
        "objectives",
        "special_rules",
        "visibility",
        "shared_with",
    ):
        if key in payload and key not in result:
            result[key] = payload[key]

    if "table_mm" in result:
        result["table_mm"] = _reorder_table_dimensions(
            result["table_mm"], "width_mm", "height_mm"
        )
    if "table_cm" in result:
        result["table_cm"] = _reorder_table_dimensions(
            result["table_cm"], "width_cm", "height_cm"
        )

    result.pop("map_specs", None)
    result.pop("deployment_shapes", None)

    ordered: dict[str, Any] = {}
    keys_order = [
        "card_id",
        "seed",
        "owner_id",
        "name",
        "mode",
        "armies",
        "table_preset",
        "table_mm",
        "layout",
        "deployment",
        "initial_priority",
        "objectives",
        "special_rules",
        "visibility",
        "shared_with",
        "shapes",
    ]

    for key in keys_order:
        if key in result:
            ordered[key] = result[key]

    for key in result:
        if key not in ordered and key not in ("map_specs", "deployment_shapes"):
            ordered[key] = result[key]

    return ordered
