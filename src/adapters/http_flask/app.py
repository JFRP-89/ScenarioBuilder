from __future__ import annotations

from flask import Flask

from src.adapters.http_flask.routes.cards import cards_bp
from src.adapters.http_flask.routes.health import health_bp
from src.adapters.http_flask.routes.maps import maps_bp
from src.adapters.http_flask.routes.presets import presets_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.register_blueprint(cards_bp, url_prefix="/cards")
    app.register_blueprint(maps_bp, url_prefix="/maps")
    app.register_blueprint(presets_bp, url_prefix="/presets")
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000)
