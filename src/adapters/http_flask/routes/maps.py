from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.application.use_cases.render_map_svg import execute as render
from src.infrastructure.maps.svg_renderer import SvgRenderer


maps_bp = Blueprint("maps", __name__)


@maps_bp.post("/render")
def render_map():
    payload = request.get_json(force=True)
    svg = render(SvgRenderer(), payload)
    return jsonify({"svg": svg})
