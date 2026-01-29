"""Favorites routes blueprint for Flask adapter."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from application.use_cases.list_favorites import ListFavoritesRequest
from application.use_cases.toggle_favorite import ToggleFavoriteRequest

favorites_bp = Blueprint("favorites", __name__)


@favorites_bp.route("/<card_id>/toggle", methods=["POST"])
def toggle_favorite(card_id: str):
    """Toggle favorite status for a card."""
    actor_id = current_app.config["get_actor_id"]()
    services = current_app.config["services"]

    dto = ToggleFavoriteRequest(actor_id=actor_id, card_id=card_id)
    resp = services.toggle_favorite.execute(dto)

    return jsonify({"card_id": resp.card_id, "is_favorite": resp.is_favorite}), 200


@favorites_bp.route("", methods=["GET"])
def list_favorites():
    """List all favorite cards for the current actor."""
    actor_id = current_app.config["get_actor_id"]()
    services = current_app.config["services"]

    dto = ListFavoritesRequest(actor_id=actor_id)
    resp = services.list_favorites.execute(dto)

    return jsonify({"card_ids": resp.card_ids}), 200
