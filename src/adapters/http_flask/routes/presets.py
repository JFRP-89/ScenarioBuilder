from __future__ import annotations

from application.use_cases.manage_presets import list_presets
from flask import Blueprint, jsonify

presets_bp = Blueprint("presets", __name__)


@presets_bp.get("")
def presets():
    return jsonify(list_presets())
