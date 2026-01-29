from __future__ import annotations

from flask import Flask, jsonify, request

from adapters.http_flask.routes.cards import cards_bp
from adapters.http_flask.routes.favorites import favorites_bp
from adapters.http_flask.routes.health import health_bp
from adapters.http_flask.routes.maps import maps_bp
from adapters.http_flask.routes.presets import presets_bp
from domain.errors import ValidationError
from infrastructure.bootstrap import build_services


def _get_actor_id() -> str:
    """Extract and validate actor ID from X-Actor-Id header."""
    actor_id = request.headers.get("X-Actor-Id", "").strip()
    if not actor_id:
        raise ValidationError("Missing or empty X-Actor-Id header")
    return actor_id


def create_app() -> Flask:
    app = Flask(__name__)

    # Build services once and store in config
    services = build_services()
    app.config["services"] = services

    # Expose get_actor_id helper
    app.config["get_actor_id"] = _get_actor_id

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(cards_bp, url_prefix="/cards")
    app.register_blueprint(favorites_bp, url_prefix="/favorites")
    app.register_blueprint(maps_bp, url_prefix="/maps")
    app.register_blueprint(presets_bp, url_prefix="/presets")

    # --- Error handlers ---
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({"error": "ValidationError", "message": str(exc)}), 400

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception):
        message = str(exc).lower()
        if "not found" in message:
            return jsonify({"error": "NotFound", "message": str(exc)}), 404
        if "forbidden" in message:
            return jsonify({"error": "Forbidden", "message": str(exc)}), 403
        return jsonify({"error": "InternalError", "message": str(exc)}), 500

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000)
