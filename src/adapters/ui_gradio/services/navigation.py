"""Navigation-oriented service for Gradio UI.

Calls use cases **directly** (same-process) instead of HTTP round-trips.
Returns plain dicts in the same shape that the wiring layer expects.
"""

from __future__ import annotations

from typing import Any

from application.use_cases.delete_card import DeleteCardRequest
from application.use_cases.get_card import GetCardRequest
from application.use_cases.list_cards import ListCardsRequest
from application.use_cases.list_favorites import ListFavoritesRequest
from application.use_cases.render_map_svg import RenderMapSvgRequest
from application.use_cases.toggle_favorite import ToggleFavoriteRequest
from domain.errors import DomainError
from infrastructure.bootstrap import get_services


# ============================================================================
# List cards
# ============================================================================
def list_cards(
    actor_id: str,
    filter_value: str = "mine",
) -> dict[str, Any]:
    """List cards visible to the actor (direct use-case call)."""
    try:
        svc = get_services()
        resp = svc.list_cards.execute(
            ListCardsRequest(actor_id=actor_id, filter=filter_value)
        )
        return {
            "cards": [
                {
                    "card_id": c.card_id,
                    "owner_id": c.owner_id,
                    "seed": c.seed,
                    "mode": c.mode,
                    "visibility": c.visibility,
                    "name": c.name,
                    "table_preset": c.table_preset,
                    "table_mm": c.table_mm,
                }
                for c in resp.cards
            ]
        }
    except (DomainError, OSError, ValueError, KeyError, RuntimeError) as exc:
        return {"status": "error", "message": str(exc)}


# ============================================================================
# Get card detail
# ============================================================================
def get_card(actor_id: str, card_id: str) -> dict[str, Any]:
    """Retrieve a single card (direct use-case call)."""
    try:
        svc = get_services()
        r = svc.get_card.execute(GetCardRequest(actor_id=actor_id, card_id=card_id))
        return {
            "card_id": r.card_id,
            "owner_id": r.owner_id,
            "seed": r.seed,
            "mode": r.mode,
            "visibility": r.visibility,
            "table_mm": r.table_mm,
            "table_preset": r.table_preset,
            "name": r.name,
            "shared_with": r.shared_with or [],
            "armies": r.armies,
            "deployment": r.deployment,
            "layout": r.layout,
            "objectives": r.objectives,
            "initial_priority": r.initial_priority,
            "special_rules": r.special_rules,
            "shapes": r.shapes or {},
        }
    except (DomainError, OSError, ValueError, KeyError, RuntimeError) as exc:
        return {"status": "error", "message": str(exc)}


# ============================================================================
# Delete card
# ============================================================================
def delete_card(actor_id: str, card_id: str) -> dict[str, Any]:
    """Delete a card (direct use-case call)."""
    try:
        svc = get_services()
        r = svc.delete_card.execute(
            DeleteCardRequest(actor_id=actor_id, card_id=card_id)
        )
        return {"card_id": r.card_id, "deleted": r.deleted}
    except (DomainError, OSError, ValueError, KeyError, RuntimeError) as exc:
        return {"status": "error", "message": str(exc)}


# ============================================================================
# Toggle favorite
# ============================================================================
def toggle_favorite(actor_id: str, card_id: str) -> dict[str, Any]:
    """Toggle favorite status (direct use-case call)."""
    try:
        svc = get_services()
        r = svc.toggle_favorite.execute(
            ToggleFavoriteRequest(actor_id=actor_id, card_id=card_id)
        )
        return {"card_id": r.card_id, "is_favorite": r.is_favorite}
    except (DomainError, OSError, ValueError, KeyError, RuntimeError) as exc:
        return {"status": "error", "message": str(exc)}


# ============================================================================
# List favorites
# ============================================================================
def list_favorites(actor_id: str) -> dict[str, Any]:
    """List favourite card IDs (direct use-case call)."""
    try:
        svc = get_services()
        r = svc.list_favorites.execute(ListFavoritesRequest(actor_id=actor_id))
        return {"card_ids": r.card_ids}
    except (DomainError, OSError, ValueError, KeyError, RuntimeError) as exc:
        return {"status": "error", "message": str(exc)}


# ============================================================================
# Get card SVG map
# ============================================================================
def get_card_svg(actor_id: str, card_id: str) -> str:
    """Render a card's map as SVG (direct use-case call)."""
    placeholder = (
        '<div style="color:#999;font-size:14px;text-align:center;">'
        "SVG preview unavailable.</div>"
    )
    try:
        svc = get_services()
        r = svc.render_map_svg.execute(
            RenderMapSvgRequest(actor_id=actor_id, card_id=card_id)
        )
        return str(r.svg)
    except (DomainError, OSError, RuntimeError):
        return placeholder
