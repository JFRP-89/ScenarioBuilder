from __future__ import annotations

from adapters.http_flask.error_contract import (
    ERROR_FORBIDDEN,
    ERROR_INTERNAL,
    ERROR_NOT_FOUND,
    ERROR_VALIDATION,
    MSG_FORBIDDEN,
    MSG_INTERNAL_ERROR,
    MSG_NOT_FOUND,
    STATUS_BAD_REQUEST,
    STATUS_FORBIDDEN,
    STATUS_INTERNAL_ERROR,
    STATUS_NOT_FOUND,
    error_response,
)
from adapters.http_flask.routes.cards import cards_bp
from adapters.http_flask.routes.favorites import favorites_bp
from adapters.http_flask.routes.health import health_bp
from adapters.http_flask.routes.maps import maps_bp
from adapters.http_flask.routes.presets import presets_bp
from domain.errors import ValidationError
from flask import Flask, jsonify, request
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
        """Map domain ValidationError to 400 Bad Request."""
        body, status = error_response(
            ERROR_VALIDATION,
            str(exc),
            STATUS_BAD_REQUEST,
        )
        return jsonify(body), status

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception):
        """Catch-all for unhandled exceptions.

        IMPORTANT: For 500 errors, always return a generic message.
        Never expose internal error details to the client.
        """
        exc_type = type(exc).__name__
        exc_message = str(exc).lower()

        # Map specific exception types to appropriate HTTP status codes
        if exc_type == "NotFound" or "not found" in exc_message:
            body, status = error_response(
                ERROR_NOT_FOUND,
                MSG_NOT_FOUND,
                STATUS_NOT_FOUND,
            )
            return jsonify(body), status

        if exc_type == "Forbidden" or "forbidden" in exc_message:
            body, status = error_response(
                ERROR_FORBIDDEN,
                MSG_FORBIDDEN,
                STATUS_FORBIDDEN,
            )
            return jsonify(body), status

        # Default: 500 Internal Server Error with GENERIC message (never leak internals)
        body, status = error_response(
            ERROR_INTERNAL,
            MSG_INTERNAL_ERROR,
            STATUS_INTERNAL_ERROR,
        )
        return jsonify(body), status

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000)  # nosec B104 - container/local dev
