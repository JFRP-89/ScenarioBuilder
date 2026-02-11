"""Navigation-oriented API client extensions.

Wraps HTTP calls to Flask API for card listing, detail, favorites, and SVG.
Reuses ``api_client`` helpers for base URL, headers, and error handling.
"""

from __future__ import annotations

from typing import Any, cast

from adapters.ui_gradio.api_client import (
    build_headers,
    get_api_base_url,
    normalize_error,
)

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None

_TIMEOUT = 30


# ============================================================================
# List cards
# ============================================================================
def list_cards(
    actor_id: str,
    filter_value: str = "mine",
) -> dict[str, Any]:
    """GET /cards?filter=... — list cards visible to the actor.

    Returns:
        ``{"cards": [...]}`` on success, or ``{"status": "error", ...}`` on failure.
    """
    if not requests:
        return {"status": "error", "message": "requests library not available"}
    try:
        url = f"{get_api_base_url()}/cards"
        headers = build_headers(actor_id)
        resp = requests.get(
            url,
            params={"filter": filter_value},
            headers=headers,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 200:
            return cast(dict[str, Any], resp.json())
        return cast(dict[str, Any], normalize_error(resp))
    except Exception as exc:
        return cast(dict[str, Any], normalize_error(None, exc))


# ============================================================================
# Get card detail
# ============================================================================
def get_card(actor_id: str, card_id: str) -> dict[str, Any]:
    """GET /cards/<card_id> — retrieve a single card.

    Returns:
        Card dict on success, or ``{"status": "error", ...}`` on failure.
    """
    if not requests:
        return {"status": "error", "message": "requests library not available"}
    try:
        url = f"{get_api_base_url()}/cards/{card_id}"
        headers = build_headers(actor_id)
        resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
        if resp.status_code == 200:
            return cast(dict[str, Any], resp.json())
        return cast(dict[str, Any], normalize_error(resp))
    except Exception as exc:
        return cast(dict[str, Any], normalize_error(None, exc))


# ============================================================================
# Delete card
# ============================================================================
def delete_card(actor_id: str, card_id: str) -> dict[str, Any]:
    """DELETE /cards/<card_id> — delete a card.

    Returns:
        ``{"card_id": ..., "deleted": True}`` on success,
        or ``{"status": "error", ...}`` on failure.
    """
    if not requests:
        return {"status": "error", "message": "requests library not available"}
    try:
        url = f"{get_api_base_url()}/cards/{card_id}"
        headers = build_headers(actor_id)
        resp = requests.delete(url, headers=headers, timeout=_TIMEOUT)
        if resp.status_code == 200:
            return cast(dict[str, Any], resp.json())
        return cast(dict[str, Any], normalize_error(resp))
    except Exception as exc:
        return cast(dict[str, Any], normalize_error(None, exc))


# ============================================================================
# Toggle favorite
# ============================================================================
def toggle_favorite(actor_id: str, card_id: str) -> dict[str, Any]:
    """POST /favorites/<card_id>/toggle — toggle favorite status.

    Returns:
        ``{"card_id": ..., "is_favorite": bool}`` on success,
        or ``{"status": "error", ...}`` on failure.
    """
    if not requests:
        return {"status": "error", "message": "requests library not available"}
    try:
        url = f"{get_api_base_url()}/favorites/{card_id}/toggle"
        headers = build_headers(actor_id)
        resp = requests.post(url, headers=headers, timeout=_TIMEOUT)
        if resp.status_code == 200:
            return cast(dict[str, Any], resp.json())
        return cast(dict[str, Any], normalize_error(resp))
    except Exception as exc:
        return cast(dict[str, Any], normalize_error(None, exc))


# ============================================================================
# List favorites
# ============================================================================
def list_favorites(actor_id: str) -> dict[str, Any]:
    """GET /favorites — list favorite card IDs.

    Returns:
        ``{"card_ids": [...]}`` on success,
        or ``{"status": "error", ...}`` on failure.
    """
    if not requests:
        return {"status": "error", "message": "requests library not available"}
    try:
        url = f"{get_api_base_url()}/favorites"
        headers = build_headers(actor_id)
        resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
        if resp.status_code == 200:
            return cast(dict[str, Any], resp.json())
        return cast(dict[str, Any], normalize_error(resp))
    except Exception as exc:
        return cast(dict[str, Any], normalize_error(None, exc))


# ============================================================================
# Get card SVG map
# ============================================================================
def get_card_svg(actor_id: str, card_id: str) -> str:
    """GET /cards/<card_id>/map.svg — fetch rendered SVG markup.

    Returns:
        SVG string on success, or a placeholder HTML string on failure.
    """
    placeholder = (
        '<div style="color:#999;font-size:14px;text-align:center;">'
        "SVG preview unavailable.</div>"
    )
    if not requests:
        return placeholder
    try:
        url = f"{get_api_base_url()}/cards/{card_id}/map.svg"
        headers = build_headers(actor_id)
        resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
        if resp.status_code == 200:
            return cast(str, resp.text)
        return placeholder
    except Exception:
        return placeholder
