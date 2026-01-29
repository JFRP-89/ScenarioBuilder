from __future__ import annotations

from flask import Blueprint, jsonify

from application.use_cases.manage_presets import list_presets


presets_bp = Blueprint("presets", __name__)


@presets_bp.get("")
def presets():
    return jsonify(list_presets())
