"""Cards API routes (Flask adapter).

HTTP adapter for card operations. Maps HTTP requests to use case DTOs,
delegates to use cases via app.config["services"], and returns JSON responses.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from io import BytesIO

from defusedxml.ElementTree import fromstring as defused_fromstring
from flask import Blueprint, current_app, jsonify, request, send_file

from application.use_cases.generate_scenario_card import GenerateScenarioCardRequest
from application.use_cases.get_card import GetCardRequest
from application.use_cases.list_cards import ListCardsRequest
from application.use_cases.render_map_svg import RenderMapSvgRequest
from application.use_cases.save_card import SaveCardRequest
from domain.cards.card import Card, parse_game_mode
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import parse_visibility


cards_bp = Blueprint("cards", __name__)


def _resolve_table(preset: str) -> TableSize:
    """Resolve table preset string to TableSize."""
    if preset == "massive":
        return TableSize.massive()
    # Default to standard
    return TableSize.standard()


@cards_bp.post("")
def create_card():
    """POST /cards - Generate and save a new scenario card."""
    # 1) Get actor_id from header (raises ValidationError if missing)
    actor_id = current_app.config["get_actor_id"]()

    # 2) Parse request body
    payload = request.get_json(force=True) or {}
    mode = payload.get("mode", "casual")
    seed = payload.get("seed")
    table_preset = payload.get("table_preset", "standard")
    visibility = payload.get("visibility", "private")
    shared_with = payload.get("shared_with")

    # 3) Get services from config
    services = current_app.config["services"]

    # 4) Call generate use case
    gen_request = GenerateScenarioCardRequest(
        actor_id=actor_id,
        mode=mode,
        seed=seed,
        table_preset=table_preset,
        visibility=visibility,
        shared_with=shared_with,
    )
    gen_response = services.generate_scenario_card.execute(gen_request)

    # 5) Build Card domain entity for saving
    table = _resolve_table(table_preset)
    card = Card(
        card_id=gen_response.card_id,
        owner_id=gen_response.owner_id,
        visibility=parse_visibility(gen_response.visibility),
        shared_with=shared_with,
        mode=parse_game_mode(gen_response.mode),
        seed=gen_response.seed,
        table=table,
        map_spec=MapSpec(table=table, shapes=gen_response.shapes),
    )

    # 6) Call save use case
    save_request = SaveCardRequest(actor_id=actor_id, card=card)
    services.save_card.execute(save_request)

    # 7) Return response
    return jsonify({
        "card_id": gen_response.card_id,
        "owner_id": gen_response.owner_id,
        "seed": gen_response.seed,
        "mode": gen_response.mode,
        "visibility": gen_response.visibility,
        "table_mm": gen_response.table_mm,
        "shapes": gen_response.shapes,
    }), 201


@cards_bp.get("/<card_id>")
def get_card(card_id: str):
    """GET /cards/<card_id> - Retrieve a card by ID."""
    # 1) Get actor_id from header
    actor_id = current_app.config["get_actor_id"]()

    # 2) Get services from config
    services = current_app.config["services"]

    # 3) Call get_card use case
    get_request = GetCardRequest(actor_id=actor_id, card_id=card_id)
    response = services.get_card.execute(get_request)

    # 4) Return response
    return jsonify({
        "card_id": response.card_id,
        "owner_id": response.owner_id,
        "seed": response.seed,
        "mode": response.mode,
        "visibility": response.visibility,
    }), 200


@cards_bp.get("")
def list_cards():
    """GET /cards?filter=... - List cards for the actor."""
    # 1) Get actor_id from header
    actor_id = current_app.config["get_actor_id"]()

    # 2) Get filter from query params
    filter_param = request.args.get("filter", "mine")

    # 3) Get services from config
    services = current_app.config["services"]

    # 4) Call list_cards use case
    list_request = ListCardsRequest(actor_id=actor_id, filter=filter_param)
    response = services.list_cards.execute(list_request)

    # 5) Map cards to JSON
    cards_json = [
        {
            "card_id": c.card_id,
            "owner_id": c.owner_id,
            "seed": c.seed,
            "mode": c.mode,
            "visibility": c.visibility,
        }
        for c in response.cards
    ]

    return jsonify({"cards": cards_json}), 200


@cards_bp.get("/<card_id>/map.svg")
def get_card_map_svg(card_id: str):
    """GET /cards/<card_id>/map.svg - Render a card's map as SVG."""
    # 1) Get actor_id from header (raises ValidationError if missing)
    actor_id = current_app.config["get_actor_id"]()

    # 2) Get services from config
    services = current_app.config["services"]

    # 3) Call render_map_svg use case
    uc_request = RenderMapSvgRequest(actor_id=actor_id, card_id=card_id)
    uc_response = services.render_map_svg.execute(uc_request)

    # 4) Extract SVG (support both .svg attr and direct string)
    svg_raw = uc_response.svg if hasattr(uc_response, "svg") else str(uc_response)

    # 5) Normalize SVG (validates + sanitizes: XXE/XSS prevention by construction)
    svg_safe = _normalize_svg_xml(svg_raw)

    # 6) Prepare safe SVG as bytes for send_file
    svg_bytes = BytesIO(svg_safe.encode("utf-8"))
    svg_bytes.seek(0)

    # 7) Return SVG with defense-in-depth headers
    response = send_file(
        svg_bytes,
        mimetype="image/svg+xml",
        as_attachment=False,  # Display inline, not download
        download_name="map.svg"
    )

    # Add security headers (defense in depth)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

    return response


def _validate_no_dangerous_xml_entities(svg: str) -> None:
    """Validate SVG does not contain dangerous XML entities (XXE prevention).

    Args:
        svg: SVG string to validate.

    Raises:
        ValidationError: If DOCTYPE or ENTITY declarations are found.
    """
    from domain.errors import ValidationError

    # Block DOCTYPE declarations (XXE attack vector)
    if re.search(r"<!DOCTYPE", svg, re.IGNORECASE):
        raise ValidationError("SVG must not contain DOCTYPE declarations")

    # Block ENTITY declarations (XXE attack vector)
    if re.search(r"<!ENTITY", svg, re.IGNORECASE):
        raise ValidationError("SVG must not contain ENTITY declarations")


def _normalize_svg_xml(svg: str) -> str:
    """Normalize SVG via XML parsing and re-serialization.

    This ensures the SVG is well-formed XML and removes potential XSS vectors.
    Static analysis tools (Sonar/Snyk) recognize this as sanitization.

    Uses defusedxml to prevent XXE attacks (safer than stdlib ET.fromstring).
    Validates SVG content against allowlist to block XSS vectors.
    Strips namespaces to ensure deterministic output without ns0: prefixes.

    Args:
        svg: SVG string from renderer.

    Returns:
        Normalized SVG string (always contains literal <svg>, not <ns0:svg>).

    Raises:
        ValidationError: If SVG is not well-formed XML or contains dangerous content.
    """
    from domain.errors import ValidationError

    try:
        # 1) Validate no dangerous entities BEFORE parsing (defense in depth)
        _validate_no_dangerous_xml_entities(svg)

        # 2) Parse SVG as XML (validates well-formedness)
        # Using defusedxml to prevent XXE/DoS attacks
        root = defused_fromstring(svg)

        # 3) Validate SVG content against allowlist (XSS prevention)
        _validate_svg_allowlist(root)

        # 4) Strip namespaces from entire tree (ensures deterministic output)
        _strip_svg_namespaces_inplace(root)

        # 5) Re-serialize to normalized XML
        return ET.tostring(root, encoding="unicode", method="xml")

    except ET.ParseError as e:
        raise ValidationError(f"Invalid SVG XML: {e}") from e
    except Exception as e:
        # Catch defusedxml exceptions (EntitiesForbidden, etc.) and other parsing errors
        if "defusedxml" in type(e).__module__ or "Forbidden" in type(e).__name__:
            raise ValidationError(f"SVG contains forbidden XML features: {e}") from e
        raise ValidationError(f"SVG parsing failed: {e}") from e


def _strip_svg_namespaces_inplace(element: ET.Element) -> None:
    """Strip namespaces from SVG element tree (in-place modification).

    Converts tags like "{http://www.w3.org/2000/svg}rect" to "rect".
    This ensures deterministic serialization without ns0: prefixes.

    Args:
        element: Root element to process (modified in-place).
    """
    # Strip namespace from tag if present
    if "}" in element.tag:
        element.tag = element.tag.split("}", 1)[1]

    # Strip namespaces from attributes
    for attr_name in list(element.attrib.keys()):
        if "}" in attr_name:
            # Move attribute to name without namespace
            clean_name = attr_name.split("}", 1)[1]
            element.attrib[clean_name] = element.attrib.pop(attr_name)

    # Recursively process all children
    for child in element:
        _strip_svg_namespaces_inplace(child)


def _validate_svg_allowlist(element: ET.Element) -> None:
    """Strict SVG allowlist validation (XSS prevention).

    Allows only the minimal SVG subset we generate (svg/rect/circle/polygon)
    and only safe attributes. Everything else is rejected.
    """
    from domain.errors import ValidationError

    # 1) Allowed tags (minimal subset)
    ALLOWED_TAGS = {"svg", "rect", "circle", "polygon"}

    # 2) Allowed attributes per tag (minimal subset)
    ALLOWED_ATTRS: dict[str, set[str]] = {
        "svg": {"xmlns", "width", "height", "viewBox"},
        "rect": {"x", "y", "width", "height"},
        "circle": {"cx", "cy", "r"},
        "polygon": {"points"},
    }

    # Helper: strip namespace
    def _local_name(name: str) -> str:
        return name.split("}")[-1] if "}" in name else name

    tag = _local_name(element.tag)

    # Root must be <svg>
    if element is not None and element.getroottree is None:
        # (ElementTree stdlib doesn't give easy root check; ignore)
        pass

    if tag not in ALLOWED_TAGS:
        raise ValidationError(f"SVG contains forbidden tag: <{tag}>")

    # Reject any attribute not in the allowed set for that tag
    allowed_for_tag = ALLOWED_ATTRS.get(tag, set())
    for attr_name, attr_value in element.attrib.items():
        clean_attr = _local_name(attr_name)

        # Block event handlers always
        if clean_attr.lower().startswith("on"):
            raise ValidationError(f"SVG contains forbidden event handler attribute: {clean_attr}")

        # Disallow any linking/external content attributes entirely
        if clean_attr.lower() in {"href", "xlink:href", "src"}:
            raise ValidationError(f"SVG must not contain external reference attribute: {clean_attr}")

        # Disallow style-like / CSS injection surfaces (keep minimal)
        if clean_attr.lower() in {"style", "class"}:
            raise ValidationError(f"SVG must not contain styling attribute: {clean_attr}")

        if clean_attr not in allowed_for_tag:
            raise ValidationError(f"SVG contains forbidden attribute '{clean_attr}' on <{tag}>")

        # Optional: basic type checks (keeps things tight and scanner-friendly)
        if tag in {"svg", "rect", "circle"} and clean_attr != "xmlns":
            # allow viewBox like "0 0 1200 700"
            if clean_attr == "viewBox":
                parts = attr_value.strip().split()
                if len(parts) != 4 or any(not p.lstrip("-").isdigit() for p in parts):
                    raise ValidationError("SVG viewBox must be 4 integers")
            else:
                if not attr_value.strip().lstrip("-").isdigit():
                    raise ValidationError(f"SVG attribute '{clean_attr}' must be an integer")

        if tag == "polygon" and clean_attr == "points":
            # points like "10,10 20,20 30,10"
            # Keep it simple: only digits, spaces, commas, minus
            for ch in attr_value:
                if not (ch.isdigit() or ch in {" ", ",", "-"}):
                    raise ValidationError("SVG polygon points contain invalid characters")

    # 3) Recurse into children
    for child in list(element):
        _validate_svg_allowlist(child)
