"""Cards API routes (Flask adapter).

HTTP adapter for card operations. Maps HTTP requests to use case DTOs,
delegates to use cases via app.config["services"], and returns JSON responses.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.use_cases.generate_scenario_card import (
        GenerateScenarioCardResponse,
    )

from adapters.http_flask.constants import (
    DEFAULT_FILTER,
    DEFAULT_MODE,
    DEFAULT_TABLE_PRESET,
    DEFAULT_VISIBILITY,
    KEY_ARMIES,
    KEY_CARD_ID,
    KEY_CARDS,
    KEY_DEPLOYMENT,
    KEY_DEPLOYMENT_SHAPES,
    KEY_FILTER,
    KEY_INITIAL_PRIORITY,
    KEY_LAYOUT,
    KEY_MODE,
    KEY_NAME,
    KEY_OBJECTIVE_SHAPES,
    KEY_OBJECTIVES,
    KEY_OWNER_ID,
    KEY_SCENOGRAPHY_SPECS,
    KEY_SEED,
    KEY_SHAPES,
    KEY_SHARED_WITH,
    KEY_SPECIAL_RULES,
    KEY_TABLE_MM,
    KEY_TABLE_PRESET,
    KEY_VISIBILITY,
)
from adapters.http_flask.context import get_actor_id, get_services
from adapters.http_flask.svg_sanitizer import normalize_svg_xml
from application.use_cases.delete_card import DeleteCardRequest
from application.use_cases.generate_scenario_card import GenerateScenarioCardRequest
from application.use_cases.get_card import GetCardRequest
from application.use_cases.list_cards import ListCardsRequest
from application.use_cases.render_map_svg import RenderMapSvgRequest
from application.use_cases.save_card import SaveCardRequest
from flask import Blueprint, jsonify, request, send_file

cards_bp = Blueprint("cards", __name__)


# ── Shared helpers for create / update ────────────────────────────


def _parse_card_payload(payload: dict) -> dict:
    """Extract and normalise card fields from a JSON request body.

    Returns a dict suitable for unpacking into
    :class:`GenerateScenarioCardRequest`.
    """
    mode = payload.get(KEY_MODE, DEFAULT_MODE)
    is_replicable = payload.get("is_replicable", True)  # Default to True for replicable scenarios
    table_preset = payload.get(KEY_TABLE_PRESET, DEFAULT_TABLE_PRESET)
    visibility = payload.get(KEY_VISIBILITY, DEFAULT_VISIBILITY)
    shared_with = payload.get(KEY_SHARED_WITH)
    armies = payload.get(KEY_ARMIES)
    deployment = payload.get(KEY_DEPLOYMENT)
    layout = payload.get(KEY_LAYOUT)
    objectives = payload.get(KEY_OBJECTIVES)
    initial_priority = payload.get(KEY_INITIAL_PRIORITY)
    name = payload.get(KEY_NAME)
    special_rules = payload.get(KEY_SPECIAL_RULES)

    # Parse custom table dimensions if preset is "custom"
    table_width_mm = None
    table_height_mm = None
    if table_preset == "custom":
        table_cm = payload.get("table_cm")
        if table_cm:
            table_width_mm = int(table_cm.get("width_cm", 0) * 10)
            table_height_mm = int(table_cm.get("height_cm", 0) * 10)
        table_mm = payload.get(KEY_TABLE_MM)
        if table_mm:
            table_width_mm = table_mm.get("width_mm")
            table_height_mm = table_mm.get("height_mm")

    # Parse shapes from nested 'shapes' dict or top-level fields
    shapes_dict = payload.get(KEY_SHAPES) or {}
    deployment_shapes = payload.get(KEY_DEPLOYMENT_SHAPES) or shapes_dict.get(
        KEY_DEPLOYMENT_SHAPES
    )
    objective_shapes = payload.get(KEY_OBJECTIVE_SHAPES) or shapes_dict.get(
        KEY_OBJECTIVE_SHAPES
    )
    scenography_specs = payload.get(KEY_SCENOGRAPHY_SPECS) or shapes_dict.get(
        KEY_SCENOGRAPHY_SPECS
    )
    map_specs = payload.get("map_specs")

    return {
        "mode": mode,
        "seed": None,  # seed is now calculated internally based on is_replicable
        "is_replicable": is_replicable,
        "table_preset": table_preset,
        "table_width_mm": table_width_mm,
        "table_height_mm": table_height_mm,
        "visibility": visibility,
        "shared_with": shared_with,
        "armies": armies,
        "deployment": deployment,
        "layout": layout,
        "objectives": objectives,
        "initial_priority": initial_priority,
        "name": name,
        "special_rules": special_rules,
        "map_specs": map_specs,
        "scenography_specs": scenography_specs,
        "deployment_shapes": deployment_shapes,
        "objective_shapes": objective_shapes,
    }


def _build_gen_response_dict(gen_response: GenerateScenarioCardResponse) -> dict:
    """Build the public JSON dict from a ``GenerateScenarioCardResponse``."""
    return {
        KEY_CARD_ID: gen_response.card_id,
        KEY_SEED: gen_response.seed,
        KEY_OWNER_ID: gen_response.owner_id,
        KEY_NAME: gen_response.name,
        KEY_MODE: gen_response.mode,
        KEY_ARMIES: gen_response.armies,
        KEY_TABLE_PRESET: gen_response.table_preset,
        KEY_TABLE_MM: gen_response.table_mm,
        KEY_LAYOUT: gen_response.layout,
        KEY_DEPLOYMENT: gen_response.deployment,
        KEY_INITIAL_PRIORITY: gen_response.initial_priority,
        KEY_OBJECTIVES: gen_response.objectives,
        KEY_SPECIAL_RULES: gen_response.special_rules,
        KEY_VISIBILITY: gen_response.visibility,
        KEY_SHARED_WITH: gen_response.shared_with or [],
        KEY_SHAPES: gen_response.shapes,
    }


@cards_bp.post("")
def create_card():
    """POST /cards - Generate and save a new scenario card."""
    actor_id = get_actor_id()
    payload = request.get_json(force=True) or {}
    parsed = _parse_card_payload(payload)

    services = get_services()
    gen_request = GenerateScenarioCardRequest(actor_id=actor_id, **parsed)
    gen_response = services.generate_scenario_card.execute(gen_request)

    save_request = SaveCardRequest(actor_id=actor_id, card=gen_response.card)
    services.save_card.execute(save_request)

    return jsonify(_build_gen_response_dict(gen_response)), 201


@cards_bp.get("/<card_id>")
def get_card(card_id: str):
    """GET /cards/<card_id> - Retrieve a card by ID."""
    # 1) Get actor_id from header
    actor_id = get_actor_id()

    # 2) Get services
    services = get_services()

    # 3) Call get_card use case
    get_request = GetCardRequest(actor_id=actor_id, card_id=card_id)
    response = services.get_card.execute(get_request)

    # 4) Return response
    response_data = {
        KEY_CARD_ID: response.card_id,
        KEY_OWNER_ID: response.owner_id,
        KEY_SEED: response.seed,
        KEY_MODE: response.mode,
        KEY_VISIBILITY: response.visibility,
        KEY_TABLE_MM: response.table_mm,
        KEY_TABLE_PRESET: response.table_preset,
        KEY_NAME: response.name,
        KEY_SHARED_WITH: response.shared_with or [],
        KEY_ARMIES: response.armies,
        KEY_DEPLOYMENT: response.deployment,
        KEY_LAYOUT: response.layout,
        KEY_OBJECTIVES: response.objectives,
        KEY_INITIAL_PRIORITY: response.initial_priority,
        KEY_SPECIAL_RULES: response.special_rules,
        KEY_SHAPES: response.shapes or {},
    }
    return jsonify(response_data), 200


@cards_bp.put("/<card_id>")
def update_card(card_id: str):
    """PUT /cards/<card_id> - Update an existing scenario card.

    Only the card owner may update. Re-generates the card with the
    same card_id and saves (overwrites) the existing entry.

    Authorization is enforced by the use cases (get_card + save_card).
    """
    actor_id = get_actor_id()
    services = get_services()

    # 1) Verify card exists and actor can read it
    existing_card = services.get_card.execute(
        GetCardRequest(actor_id=actor_id, card_id=card_id)
    )

    # 2) Parse request body (same structure as create_card)
    payload = request.get_json(force=True) or {}
    parsed = _parse_card_payload(payload)

    # 3) Preserve the existing seed (edit mode should maintain seed stability)
    parsed["seed"] = existing_card.seed

    # 4) Re-generate with same card_id and existing seed
    gen_request = GenerateScenarioCardRequest(
        actor_id=actor_id, card_id=card_id, **parsed
    )
    gen_response = services.generate_scenario_card.execute(gen_request)

    # 5) Save (overwrite) — enforces ownership via save_card use case
    save_request = SaveCardRequest(actor_id=actor_id, card=gen_response.card)
    services.save_card.execute(save_request)

    return jsonify(_build_gen_response_dict(gen_response)), 200


@cards_bp.delete("/<card_id>")
def delete_card(card_id: str):
    """DELETE /cards/<card_id> - Delete a scenario card.

    Only the card owner may delete. Returns 200 on success.
    Errors (not found / forbidden) are handled by the global error handler.
    """
    actor_id = get_actor_id()
    services = get_services()

    result = services.delete_card.execute(
        DeleteCardRequest(actor_id=actor_id, card_id=card_id)
    )

    return (
        jsonify(
            {
                "card_id": result.card_id,
                "deleted": result.deleted,
            }
        ),
        200,
    )


@cards_bp.get("")
def list_cards():
    """GET /cards?filter=... - List cards for the actor."""
    # 1) Get actor_id from header
    actor_id = get_actor_id()

    # 2) Get filter from query params
    filter_param = request.args.get(KEY_FILTER, DEFAULT_FILTER)

    # 3) Get services
    services = get_services()

    # 4) Call list_cards use case
    list_request = ListCardsRequest(actor_id=actor_id, filter=filter_param)
    response = services.list_cards.execute(list_request)

    # 5) Map cards to JSON
    cards_json = [
        {
            KEY_CARD_ID: c.card_id,
            KEY_OWNER_ID: c.owner_id,
            KEY_SEED: c.seed,
            KEY_MODE: c.mode,
            KEY_VISIBILITY: c.visibility,
            KEY_NAME: c.name,
            KEY_TABLE_PRESET: c.table_preset,
            KEY_TABLE_MM: c.table_mm,
        }
        for c in response.cards
    ]

    return jsonify({KEY_CARDS: cards_json}), 200


@cards_bp.get("/<card_id>/map.svg")
def get_card_map_svg(card_id: str):
    """GET /cards/<card_id>/map.svg - Render a card's map as SVG."""
    # 1) Get actor_id from header (raises ValidationError if missing)
    actor_id = get_actor_id()

    # 2) Get services
    services = get_services()

    # 3) Call render_map_svg use case
    uc_request = RenderMapSvgRequest(actor_id=actor_id, card_id=card_id)
    uc_response = services.render_map_svg.execute(uc_request)

    # 4) Extract SVG (support both .svg attr and direct string)
    svg_raw = uc_response.svg if hasattr(uc_response, "svg") else str(uc_response)

    # 5) Normalize SVG (validates + sanitizes: XXE/XSS prevention by construction)
    svg_safe = normalize_svg_xml(svg_raw)

    # 6) Prepare safe SVG as bytes for send_file
    svg_bytes = BytesIO(svg_safe.encode("utf-8"))
    svg_bytes.seek(0)

    # 7) Return SVG with defense-in-depth headers
    response = send_file(
        svg_bytes,
        mimetype="image/svg+xml",
        as_attachment=False,  # Display inline, not download
        download_name="map.svg",
    )

    # Add security headers (defense in depth)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

    return response
