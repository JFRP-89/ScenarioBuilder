"""Generate service for Gradio UI adapter — FACADE.

Keeps ``_prepare_payload``, ``handle_preview`` and ``handle_generate`` here
(they are the core orchestrators).  Delegates card-result helpers to
``_generate._card_result`` and submission handlers to ``_generate._submission``.

All existing imports continue to work unchanged.
"""

from __future__ import annotations

import os
from typing import Any, cast

from adapters.ui_gradio.builders import payload as payload_builder
from adapters.ui_gradio.builders import shapes as shapes_builder
from adapters.ui_gradio.constants import (
    FIELD_MODE,
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
from adapters.ui_gradio.services._generate._form_state import FormState
from adapters.ui_gradio.services._generate._submission import (
    handle_create_scenario,
    handle_update_scenario,
)
from adapters.ui_gradio.ui_types import ErrorDict
from domain.errors import DomainError

__all__ = [
    "handle_create_scenario",
    "handle_generate",
    "handle_preview",
    "handle_update_scenario",
]
from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


def _prepare_payload(
    fs: FormState,
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
        payload_builder.ValidationInput(
            actor=fs.actor,
            name=fs.name,
            mode=fs.mode,
            armies=fs.armies_val,
            preset=fs.preset,
            width=fs.width,
            height=fs.height,
            unit=fs.unit,
            deployment=fs.depl,
            layout=fs.lay,
            objectives=fs.obj,
            initial_priority=fs.init_priority,
            rules_state=fs.rules_state,
            vp_state=fs.vp_state,
            deployment_zones=fs.deployment_zones_state_val,
            objective_points=fs.objective_points_state_val,
            scenography=fs.scenography_state_val,
            default_actor_id=default_actor_id,
        )
    )
    if validation_error:
        return {"status": "error", "message": validation_error}

    actor_id = (fs.actor or "").strip() or default_actor_id
    if not actor_id:
        return {"status": "error", "message": "Actor ID is required."}

    payload = payload_builder.build_generate_payload(fs.mode, fs.is_replicable)

    # Attach generate_from_seed when provided
    if fs.generate_from_seed is not None and fs.generate_from_seed > 0:
        payload["generate_from_seed"] = int(fs.generate_from_seed)

    if fs.name.strip():
        payload["name"] = fs.name.strip()

    custom_table, error = payload_builder.apply_table_config(
        payload, fs.preset, fs.width, fs.height, fs.unit
    )
    if error:
        return error

    payload_builder.apply_optional_text_fields(
        payload,
        deployment=fs.depl,
        layout=fs.lay,
        objectives=fs.obj,
        armies=fs.armies_val,
    )

    vp_error = _apply_victory_points(payload, fs)
    if vp_error:
        return vp_error

    if fs.init_priority.strip():
        payload["initial_priority"] = fs.init_priority.strip()

    error_sr = _apply_special_rules(payload, fs.rules_state)
    if error_sr:
        return cast(dict[str, Any], error_sr)

    payload_builder.apply_visibility(payload, fs.vis, fs.shared)

    # -- Ensure required positional fields for GenerateScenarioCardRequest --
    payload.setdefault("seed", None)
    payload.setdefault("shared_with", None)

    shapes = _build_shapes(payload, fs)

    return {
        "status": "ok",
        "payload": payload,
        "actor_id": actor_id,
        "custom_table": custom_table,
        "preset": fs.preset,
        "shapes": shapes,
    }


def _apply_victory_points(
    payload: dict[str, Any],
    fs: FormState,
) -> dict[str, Any] | None:
    """Add victory-point data to payload.  Returns error dict or *None*."""
    if not (fs.objectives_with_vp_enabled and fs.vp_state):
        return None

    normalized_vps, error_msg = payload_builder.validate_victory_points(fs.vp_state)
    if error_msg:
        return {"status": "error", "message": error_msg}
    if normalized_vps is None:  # pragma: no cover
        return {"status": "error", "message": "Unexpected VP validation error"}

    objectives_dict: dict[str, Any] = {
        "objective": fs.obj.strip() if fs.obj.strip() else ""
    }
    if len(normalized_vps) > 0:
        objectives_dict["victory_points"] = normalized_vps
    if objectives_dict.get("objective"):
        payload["objectives"] = objectives_dict
    return None


def _build_shapes(
    payload: dict[str, Any],
    fs: FormState,
) -> dict[str, Any]:
    """Build shapes from form state and attach to payload.  Returns shapes dict."""
    scenography_specs: list[dict[str, Any]] = []
    if fs.scenography_state_val:
        scenography_specs = shapes_builder.build_map_specs_from_state(
            fs.scenography_state_val  # type: ignore[arg-type]
        )
        payload["map_specs"] = scenography_specs

    deployment_shapes: list[dict[str, Any]] = []
    if fs.deployment_zones_state_val:
        deployment_shapes = shapes_builder.build_deployment_shapes_from_state(
            fs.deployment_zones_state_val  # type: ignore[arg-type]
        )
        payload["deployment_shapes"] = deployment_shapes

    objective_shapes: list[dict[str, Any]] = []
    if fs.objective_points_state_val:
        objective_shapes = shapes_builder.build_objective_shapes_from_state(
            fs.objective_points_state_val  # type: ignore[arg-type]
        )
        payload["objective_shapes"] = objective_shapes

    return {
        "deployment_shapes": deployment_shapes,
        "objective_shapes": objective_shapes,
        "scenography_specs": scenography_specs,
    }


def _compute_preview_seed(fs: FormState, seed_config: dict[str, Any]) -> int:
    """Compute the seed value for a preview card.

    Rules:
    1. Not replicable → seed = 0
    2. GFS set and form matches seed theme → seed = gfs
    3. Otherwise → seed = hash(form)
    """
    if not fs.is_replicable:
        return 0

    actual_hash = calculate_seed_from_config(seed_config)
    gfs_int = (
        int(fs.generate_from_seed)
        if fs.generate_from_seed is not None and fs.generate_from_seed > 0
        else 0
    )
    if gfs_int > 0:
        from application.use_cases._generate._themes import (
            _resolve_full_seed_defaults,
        )

        expected_config = _resolve_full_seed_defaults(gfs_int)
        expected_hash = calculate_seed_from_config(expected_config)
        return gfs_int if actual_hash == expected_hash else actual_hash

    return actual_hash


def _build_seed_config(
    fs: FormState,
    payload: dict[str, Any],
    preset: str,
    table_mm: dict[str, int],
    shapes: dict[str, Any],
) -> dict[str, Any]:
    """Build the configuration dict used for deterministic seed calculation."""
    return {
        "mode": fs.mode,
        "table_preset": preset,
        "table_width_mm": table_mm.get("width_mm") if table_mm else None,
        "table_height_mm": table_mm.get("height_mm") if table_mm else None,
        "armies": fs.armies_val.strip() if fs.armies_val else None,
        "deployment": fs.depl.strip() if fs.depl else None,
        "layout": fs.lay.strip() if fs.lay else None,
        "objectives": payload.get("objectives"),
        "initial_priority": fs.init_priority.strip() if fs.init_priority else None,
        "special_rules": fs.rules_state if fs.rules_state else None,
        "deployment_shapes": shapes["deployment_shapes"],
        "objective_shapes": shapes["objective_shapes"],
        "scenography_specs": shapes["scenography_specs"],
    }


def _build_preview_dict(
    fs: FormState,
    payload: dict[str, Any],
    seed: int,
    preset: str,
    table_mm: dict[str, int],
    shapes: dict[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Assemble the preview result dict (NOT persisted)."""
    preview: dict[str, Any] = {
        "status": "preview",
        "name": fs.name.strip(),
        FIELD_MODE: fs.mode,
        "seed": seed,
        "is_replicable": fs.is_replicable,
        "armies": fs.armies_val.strip() if fs.armies_val else "",
        "table_preset": preset,
        "table_mm": table_mm,
        "deployment": fs.depl.strip() if fs.depl else "",
        "layout": fs.lay.strip() if fs.lay else "",
        "objectives": payload.get("objectives") or (fs.obj.strip() if fs.obj else ""),
        "initial_priority": fs.init_priority.strip() if fs.init_priority else "",
        "visibility": fs.vis,
        "shapes": shapes,
        "_payload": payload,
        "_actor_id": actor_id,
    }
    if payload.get("special_rules"):
        preview["special_rules"] = payload["special_rules"]
    if payload.get("shared_with"):
        preview["shared_with"] = payload["shared_with"]
    return preview


def handle_preview(fs: FormState) -> dict[str, Any]:
    """Build a preview card locally (validate + build payload + shapes).

    Does NOT call the Flask API. Returns a preview dict with all
    data needed for SVG rendering and for later submission via
    ``handle_create_scenario``.
    """
    try:
        prepared = _prepare_payload(fs)
        if prepared.get("status") == "error":
            return prepared

        payload = prepared["payload"]
        actor_id = prepared["actor_id"]
        preset = prepared["preset"]

        # -- Compute table_mm locally -----------------------------------
        if prepared["custom_table"]:
            table_mm = _build_table_mm_from_cm(prepared["custom_table"])
        else:
            table_mm = _build_table_mm_from_cm(_table_cm_from_preset(preset))

        shapes = prepared["shapes"]
        seed_config = _build_seed_config(fs, payload, preset, table_mm, shapes)
        seed = _compute_preview_seed(fs, seed_config)

        return _build_preview_dict(
            fs, payload, seed, preset, table_mm, shapes, actor_id
        )

    except DomainError as exc:
        return {"status": "error", "message": f"Preview failed: {exc}"}
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
            "Unexpected error in handle_preview: %s", exc
        )
        return {"status": "error", "message": "An unexpected error occurred."}


def handle_generate(fs: FormState) -> dict[str, Any]:
    """Generate a scenario card via direct use-case call."""
    try:
        prepared = _prepare_payload(fs)
        if prepared.get("status") == "error":
            return prepared

        payload = prepared["payload"]
        actor_id = prepared["actor_id"]
        custom_table = prepared["custom_table"]
        preset = prepared["preset"]

        from application.use_cases.generate_scenario_card import (
            GenerateScenarioCardRequest,
        )
        from application.use_cases.save_card import SaveCardRequest
        from infrastructure.bootstrap import get_services

        svc = get_services()
        gen_req = GenerateScenarioCardRequest(actor_id=actor_id, **payload)
        gen_resp = svc.generate_scenario_card.execute(gen_req)

        save_req = SaveCardRequest(actor_id=actor_id, card=gen_resp.card)
        svc.save_card.execute(save_req)

        response_json = {
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
        return _augment_generated_card(response_json, payload, preset, custom_table)

    except DomainError as exc:
        return {"status": "error", "message": f"Generate failed: {exc}"}
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
            "Unexpected error in handle_generate: %s", exc
        )
        return {"status": "error", "message": "An unexpected error occurred."}


def _get_default_actor_id() -> str:
    """Get default actor ID from environment."""
    return os.environ.get("DEFAULT_ACTOR_ID", "demo-user")


def _apply_special_rules(
    payload: dict[str, Any],
    rules_state: list[dict[str, Any]],
) -> ErrorDict | None:
    """Validate and add special_rules to payload with UI error prefix."""
    error = payload_builder.apply_special_rules(payload, rules_state)  # type: ignore[arg-type]
    if error and "message" in error:
        error["message"] = f"Special Rules: {error['message']}"
    return error
