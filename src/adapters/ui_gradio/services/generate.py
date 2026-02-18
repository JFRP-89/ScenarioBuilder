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
from adapters.ui_gradio.services._generate._submission import (  # noqa: F401
    handle_create_scenario,
    handle_update_scenario,
)
from adapters.ui_gradio.ui_types import ErrorDict
from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


def _prepare_payload(  # noqa: C901
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
        actor=fs.actor,
        name=fs.name,
        m=fs.mode,
        armies_val=fs.armies_val,
        preset=fs.preset,
        width=fs.width,
        height=fs.height,
        unit=fs.unit,
        depl=fs.depl,
        lay=fs.lay,
        obj=fs.obj,
        init_priority=fs.init_priority,
        rules_state=fs.rules_state,
        vp_state=fs.vp_state,
        deployment_zones_state_val=fs.deployment_zones_state_val,
        objective_points_state_val=fs.objective_points_state_val,
        scenography_state_val=fs.scenography_state_val,
        default_actor_id=default_actor_id,
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

    if fs.objectives_with_vp_enabled and fs.vp_state:
        normalized_vps, error_msg = payload_builder.validate_victory_points(fs.vp_state)
        if error_msg:
            return {"status": "error", "message": error_msg}
        assert normalized_vps is not None
        objectives_dict: dict[str, Any] = {
            "objective": fs.obj.strip() if fs.obj.strip() else ""
        }
        if len(normalized_vps) > 0:
            objectives_dict["victory_points"] = normalized_vps
        if objectives_dict.get("objective"):
            payload["objectives"] = objectives_dict

    if fs.init_priority.strip():
        payload["initial_priority"] = fs.init_priority.strip()

    error_sr = _apply_special_rules(payload, fs.rules_state)
    if error_sr:
        return cast(dict[str, Any], error_sr)

    payload_builder.apply_visibility(payload, fs.vis, fs.shared)

    # -- Ensure required positional fields for GenerateScenarioCardRequest --
    payload.setdefault("seed", None)
    payload.setdefault("shared_with", None)

    # -- Build shapes ---------------------------------------------------
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
        "status": "ok",
        "payload": payload,
        "actor_id": actor_id,
        "custom_table": custom_table,
        "preset": fs.preset,
        "shapes": {
            "deployment_shapes": deployment_shapes,
            "objective_shapes": objective_shapes,
            "scenography_specs": scenography_specs,
        },
    }


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
        custom_table = prepared["custom_table"]
        preset = prepared["preset"]

        # -- Compute table_mm locally -----------------------------------
        if custom_table:
            table_mm = _build_table_mm_from_cm(custom_table)
        else:
            cm = _table_cm_from_preset(preset)
            table_mm = _build_table_mm_from_cm(cm)

        # -- Calculate seed -----------------------------------------------
        # Build config for hash-based seed (reusable across branches)
        seed_objectives = payload.get("objectives")
        seed_config = {
            "mode": fs.mode,
            "table_preset": preset,
            "table_width_mm": table_mm.get("width_mm") if table_mm else None,
            "table_height_mm": table_mm.get("height_mm") if table_mm else None,
            "armies": fs.armies_val.strip() if fs.armies_val else None,
            "deployment": fs.depl.strip() if fs.depl else None,
            "layout": fs.lay.strip() if fs.lay else None,
            "objectives": seed_objectives,
            "initial_priority": (
                fs.init_priority.strip() if fs.init_priority else None
            ),
            "special_rules": fs.rules_state if fs.rules_state else None,
            "deployment_shapes": prepared["shapes"]["deployment_shapes"],
            "objective_shapes": prepared["shapes"]["objective_shapes"],
            "scenography_specs": prepared["shapes"]["scenography_specs"],
        }

        gfs = (
            int(fs.generate_from_seed)
            if fs.generate_from_seed and fs.generate_from_seed > 0
            else 0
        )
        if gfs > 0:
            # Check if user modified content after applying the seed.
            # If unmodified → keep generate_from_seed as card seed.
            # If modified → recalculate so seed reflects actual data.
            from infrastructure.bootstrap import get_services

            svc = get_services()
            original = svc.generate_scenario_card.resolve_seed_preview(gfs)
            content_unmodified = (
                (fs.armies_val.strip() if fs.armies_val else "") == original["armies"]
                and (fs.depl.strip() if fs.depl else "") == original["deployment"]
                and (fs.lay.strip() if fs.lay else "") == original["layout"]
                and (fs.obj.strip() if fs.obj else "") == original["objectives"]
                and (fs.init_priority.strip() if fs.init_priority else "")
                == original["initial_priority"]
            )
            seed = (
                gfs if content_unmodified else calculate_seed_from_config(seed_config)
            )
        elif fs.is_replicable:
            seed = calculate_seed_from_config(seed_config)
        else:
            seed = 0

        # Shapes come strictly from the UI form state — no auto-fill from seed.
        # The "Apply Seed" button is the only mechanism that injects seed shapes.
        preview_shapes = prepared["shapes"]
        preview_objectives = payload.get("objectives") or (
            fs.obj.strip() if fs.obj else ""
        )
        preview_name = fs.name.strip()
        preview_special_rules = payload.get("special_rules")

        # -- Build preview result (NOT persisted) -----------------------
        # Note: _payload and _actor_id are internal fields needed for submission.
        # They are stored in the preview dict but filtered out before display.
        preview: dict[str, Any] = {
            "status": "preview",
            "name": preview_name,
            FIELD_MODE: fs.mode,
            "seed": seed,
            "is_replicable": fs.is_replicable,
            "armies": fs.armies_val.strip() if fs.armies_val else "",
            "table_preset": preset,
            "table_mm": table_mm,
            "deployment": fs.depl.strip() if fs.depl else "",
            "layout": fs.lay.strip() if fs.lay else "",
            "objectives": preview_objectives,
            "initial_priority": (fs.init_priority.strip() if fs.init_priority else ""),
            "visibility": fs.vis,
            "shapes": preview_shapes,
            "_payload": payload,  # Internal: for submission only
            "_actor_id": actor_id,  # Internal: for submission only
        }
        if preview_special_rules:
            preview["special_rules"] = preview_special_rules
        if payload.get("shared_with"):
            preview["shared_with"] = payload["shared_with"]

        return preview

    except Exception as exc:
        return {"status": "error", "message": f"Preview failed: {exc}"}


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

    except Exception as exc:
        return {"status": "error", "message": f"Generate failed: {exc}"}


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
