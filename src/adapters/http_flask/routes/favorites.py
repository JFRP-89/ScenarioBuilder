"""Favorites routes blueprint for Flask adapter."""

from __future__ import annotations

from adapters.http_flask.constants import KEY_CARD_ID, KEY_CARD_IDS, KEY_IS_FAVORITE
from adapters.http_flask.context import get_actor_id, get_services
from application.use_cases.list_favorites import ListFavoritesRequest
from application.use_cases.toggle_favorite import ToggleFavoriteRequest
from flask import Blueprint, jsonify

favorites_bp = Blueprint("favorites", __name__)


@favorites_bp.route("/<card_id>/toggle", methods=["POST"])
def toggle_favorite(card_id: str):
    """Toggle favorite status for a card."""
    actor_id = get_actor_id()
    services = get_services()

    dto = ToggleFavoriteRequest(actor_id=actor_id, card_id=card_id)
    resp = services.toggle_favorite.execute(dto)

    return (
        jsonify({KEY_CARD_ID: resp.card_id, KEY_IS_FAVORITE: resp.is_favorite}),
        200,
    )


@favorites_bp.route("", methods=["GET"])
def list_favorites():
    """List all favorite cards for the current actor."""
    actor_id = get_actor_id()
    services = get_services()

    dto = ListFavoritesRequest(actor_id=actor_id)
    resp = services.list_favorites.execute(dto)

    return jsonify({KEY_CARD_IDS: resp.card_ids}), 200
