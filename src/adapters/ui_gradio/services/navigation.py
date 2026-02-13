"""Navigation-oriented API client extensions.

Wraps HTTP calls to Flask API for card listing, detail, favorites, and SVG.
Reuses ``api_client`` helpers for base URL, headers, and error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, cast

from adapters.ui_gradio.api_client import (
    build_headers,
    get_api_base_url,
    normalize_error,
)

if TYPE_CHECKING:
    import requests
else:
    try:
        import requests  # type: ignore[import-untyped]
    except ImportError:
        requests = None  # type: ignore[assignment]

_TIMEOUT = 30


# ── Generic helper (DRY) ───────────────────────────────────────────


def _api_call(
    method: str,
    path: str,
    actor_id: str,
    *,
    params: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Execute an API call and return parsed JSON or an error dict.

    Args:
        method: HTTP method (``"GET"``, ``"POST"``, ``"DELETE"``).
        path: URL path relative to API base (e.g. ``"/cards"``).
        actor_id: Actor ID for the ``X-Actor-Id`` header.
        params: Optional query parameters.

    Returns:
        Parsed JSON dict on HTTP 200, or ``{"status": "error", ...}``.
    """
    if not requests:
        return {"status": "error", "message": "requests library not available"}
    try:
        url = f"{get_api_base_url()}{path}"
        headers = build_headers(actor_id)
        resp = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 200:
            return cast(dict[str, Any], resp.json())
        return cast(dict[str, Any], normalize_error(resp))
    except Exception as exc:
        return cast(dict[str, Any], normalize_error(None, exc))


# ============================================================================
# List cards
# ============================================================================
def list_cards(
    actor_id: str,
    filter_value: str = "mine",
) -> dict[str, Any]:
    """GET /cards?filter=... — list cards visible to the actor."""
    return _api_call("GET", "/cards", actor_id, params={"filter": filter_value})


# ============================================================================
# Get card detail
# ============================================================================
def get_card(actor_id: str, card_id: str) -> dict[str, Any]:
    """GET /cards/<card_id> — retrieve a single card."""
    return _api_call("GET", f"/cards/{card_id}", actor_id)


# ============================================================================
# Delete card
# ============================================================================
def delete_card(actor_id: str, card_id: str) -> dict[str, Any]:
    """DELETE /cards/<card_id> — delete a card."""
    return _api_call("DELETE", f"/cards/{card_id}", actor_id)


# ============================================================================
# Toggle favorite
# ============================================================================
def toggle_favorite(actor_id: str, card_id: str) -> dict[str, Any]:
    """POST /favorites/<card_id>/toggle — toggle favorite status."""
    return _api_call("POST", f"/favorites/{card_id}/toggle", actor_id)


# ============================================================================
# List favorites
# ============================================================================
def list_favorites(actor_id: str) -> dict[str, Any]:
    """GET /favorites — list favorite card IDs."""
    return _api_call("GET", "/favorites", actor_id)


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
            return resp.text
        return placeholder
    except Exception:
        return placeholder
