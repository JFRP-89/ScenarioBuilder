"""Generate service for Gradio UI adapter — FACADE.

Keeps ``_prepare_payload``, ``handle_preview`` and ``handle_generate`` here
(they are the core orchestrators).  Delegates card-result helpers to
``_generate._card_result`` and submission handlers to ``_generate._submission``.

All existing imports continue to work unchanged.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import requests
else:
    try:
        import requests  # type: ignore[import-untyped]
    except ImportError:
        requests = None  # type: ignore[assignment]

from adapters.ui_gradio import api_client
from adapters.ui_gradio.builders import payload as payload_builder
from adapters.ui_gradio.builders import shapes as shapes_builder
from adapters.ui_gradio.constants import (
    FIELD_MODE,
    FIELD_SEED,
    SUCCESS_STATUS_CODES,
)

# ── re-exports from internal modules ─────────────────────────────────────────
from adapters.ui_gradio.services._generate._card_result import (
    augment_generated_card as _augment_generated_card,
)
from adapters.ui_gradio.services._generate._card_result import (
    build_table_mm_from_cm as _build_table_mm_from_cm,
)
from adapters.ui_gradio.services._generate._card_result import (
    table_cm_from_preset as _table_cm_from_preset,
)
from adapters.ui_gradio.services._generate._submission import (  # noqa: F401
    handle_create_scenario,
    handle_update_scenario,
)


def _prepare_payload(  # noqa: C901
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
    """Validate inputs and build the card payload (shared by preview & generate).

    Returns a dict with ``"status": "error"`` on validation failure, or
    a dict with ``"status": "ok"`` containing:

    - ``payload``: the fully-built API payload dict.
    - ``actor_id``: resolved actor identifier.
    - ``custom_table``: custom table cm dict (or ``None``).
    - ``preset``: table preset string.
    - ``shapes``: dict with deployment_shapes, objective_shapes, scenography_specs.
    """
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
        normalized_vps, error_msg = payload_builder.validate_victory_points(vp_state)
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

    # -- Build shapes ---------------------------------------------------
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

    return {
        "status": "ok",
        "payload": payload,
        "actor_id": actor_id,
        "custom_table": custom_table,
        "preset": preset,
        "shapes": {
            "deployment_shapes": deployment_shapes,
            "objective_shapes": objective_shapes,
            "scenography_specs": scenography_specs,
        },
    }


def handle_preview(
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
        prepared = _prepare_payload(
            actor,
            name,
            m,
            s,
            armies_val,
            preset,
            width,
            height,
            unit,
            depl,
            lay,
            obj,
            init_priority,
            rules_state,
            vis,
            shared,
            scenography_state_val,
            deployment_zones_state_val,
            objective_points_state_val,
            objectives_with_vp_enabled,
            vp_state,
        )
        if prepared.get("status") == "error":
            return prepared

        payload = prepared["payload"]
        actor_id = prepared["actor_id"]
        custom_table = prepared["custom_table"]

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
            "shapes": prepared["shapes"],
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


def handle_generate(
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
        prepared = _prepare_payload(
            actor,
            name,
            m,
            s,
            armies_val,
            preset,
            width,
            height,
            unit,
            depl,
            lay,
            obj,
            init_priority,
            rules_state,
            vis,
            shared,
            scenography_state_val,
            deployment_zones_state_val,
            objective_points_state_val,
            objectives_with_vp_enabled,
            vp_state,
        )
        if prepared.get("status") == "error":
            return prepared

        payload = prepared["payload"]
        actor_id = prepared["actor_id"]
        custom_table = prepared["custom_table"]
        preset = prepared["preset"]

        api_url = api_client.get_api_base_url()
        headers = api_client.build_headers(actor_id)
        response = api_client.post_generate_card(api_url, headers, payload)

        if response is None:
            return cast(dict[str, Any], api_client.normalize_error(None))

        if response.status_code not in SUCCESS_STATUS_CODES:
            return cast(dict[str, Any], api_client.normalize_error(response))

        response_json = cast(dict[Any, Any], response.json())
        return _augment_generated_card(response_json, payload, preset, custom_table)  # type: ignore[no-any-return]

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
