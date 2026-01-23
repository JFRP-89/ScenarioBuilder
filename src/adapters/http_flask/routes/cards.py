from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.application.use_cases.generate_card import execute as generate
from src.infrastructure.content.file_content_provider import FileContentProvider


cards_bp = Blueprint("cards", __name__)

VALID_MODES = {"casual", "narrative", "matched"}


@cards_bp.post("")
def create_card():
    payload = request.get_json(force=True)
    mode = payload.get("mode", "casual")
    if mode not in VALID_MODES:
        return jsonify({"error": "Invalid mode"}), 400
    seed = int(payload.get("seed", 1))
    if seed < 0:
        return jsonify({"error": "Invalid seed"}), 400
    card = generate(mode, seed, FileContentProvider())
    return jsonify({"id": card.id, "mode": card.mode, "seed": card.seed})
