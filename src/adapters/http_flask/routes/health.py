from __future__ import annotations

from flask import Blueprint, jsonify

from adapters.http_flask.constants import KEY_STATUS, STATUS_OK

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({KEY_STATUS: STATUS_OK})
