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
from adapters.ui_gradio.services._generate._submission import (  # noqa: F401
    handle_create_scenario,
    handle_update_scenario,
)
from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)


def _prepare_payload(  # noqa: C901
    actor: str,
    name: str,
    m: str,
    is_replicable: bool,
    generate_from_seed: float | None,
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

    payload = payload_builder.build_generate_payload(m, is_replicable)

    # Attach generate_from_seed when provided
    if generate_from_seed is not None and generate_from_seed > 0:
        payload["generate_from_seed"] = int(generate_from_seed)

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

    # -- Ensure required positional fields for GenerateScenarioCardRequest --
    payload.setdefault("seed", None)
    payload.setdefault("shared_with", None)

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
    is_replicable: bool,
    generate_from_seed: float | None,
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
            is_replicable,
            generate_from_seed,
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

        # -- Calculate seed -----------------------------------------------
        # Build config for hash-based seed (reusable across branches)
        seed_objectives = payload.get("objectives")
        seed_config = {
            "mode": m,
            "table_preset": preset,
            "table_width_mm": table_mm.get("width_mm") if table_mm else None,
            "table_height_mm": table_mm.get("height_mm") if table_mm else None,
            "armies": armies_val.strip() if armies_val else None,
            "deployment": depl.strip() if depl else None,
            "layout": lay.strip() if lay else None,
            "objectives": seed_objectives,
            "initial_priority": init_priority.strip() if init_priority else None,
            "special_rules": rules_state if rules_state else None,
            "deployment_shapes": prepared["shapes"]["deployment_shapes"],
            "objective_shapes": prepared["shapes"]["objective_shapes"],
            "scenography_specs": prepared["shapes"]["scenography_specs"],
        }

        gfs = (
            int(generate_from_seed)
            if generate_from_seed and generate_from_seed > 0
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
                (armies_val.strip() if armies_val else "") == original["armies"]
                and (depl.strip() if depl else "") == original["deployment"]
                and (lay.strip() if lay else "") == original["layout"]
                and (obj.strip() if obj else "") == original["objectives"]
                and (init_priority.strip() if init_priority else "")
                == original["initial_priority"]
            )
            seed = (
                gfs if content_unmodified else calculate_seed_from_config(seed_config)
            )
        elif is_replicable:
            seed = calculate_seed_from_config(seed_config)
        else:
            seed = 0

        # Shapes come strictly from the UI form state — no auto-fill from seed.
        # The "Apply Seed" button is the only mechanism that injects seed shapes.
        preview_shapes = prepared["shapes"]
        preview_objectives = payload.get("objectives") or (obj.strip() if obj else "")
        preview_name = name.strip()
        preview_special_rules = payload.get("special_rules")

        # -- Build preview result (NOT persisted) -----------------------
        # Note: _payload and _actor_id are internal fields needed for submission.
        # They are stored in the preview dict but filtered out before display.
        preview: dict[str, Any] = {
            "status": "preview",
            "name": preview_name,
            FIELD_MODE: m,
            "seed": seed,
            "is_replicable": is_replicable,
            "armies": armies_val.strip() if armies_val else "",
            "table_preset": preset,
            "table_mm": table_mm,
            "deployment": depl.strip() if depl else "",
            "layout": lay.strip() if lay else "",
            "objectives": preview_objectives,
            "initial_priority": init_priority.strip() if init_priority else "",
            "visibility": vis,
            "shapes": preview_shapes,
            "_payload": payload,  # Internal: for submission only, filtered from display
            "_actor_id": actor_id,  # Internal: for submission only, filtered from display
        }
        if preview_special_rules:
            preview["special_rules"] = preview_special_rules
        if payload.get("shared_with"):
            preview["shared_with"] = payload["shared_with"]

        return preview

    except Exception as exc:
        return {"status": "error", "message": f"Preview failed: {exc}"}


def handle_generate(
    actor: str,
    name: str,
    m: str,
    is_replicable: bool,
    generate_from_seed: float | None,
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
    """Generate a scenario card via direct use-case call."""
    try:
        prepared = _prepare_payload(
            actor,
            name,
            m,
            is_replicable,
            generate_from_seed,
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
        return _augment_generated_card(response_json, payload, preset, custom_table)  # type: ignore[no-any-return]

    except Exception as exc:
        return {"status": "error", "message": f"Generate failed: {exc}"}


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
