"""
HTTP API client for Gradio UI adapter.

This module handles all HTTP communication with the Flask API backend,
including URL normalization, header construction, and error handling.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None


# Constants imported from constants module
ENDPOINT_GENERATE_CARD = "/cards"
REQUEST_TIMEOUT_SECONDS = 30
ERROR_REQUEST_FAILED = "Request failed"
ERROR_REQUESTS_NOT_AVAILABLE = "Requests library not available"
ERROR_API_FAILURE = "API call failed"
ERROR_UNEXPECTED = "Unexpected error"
SUCCESS_STATUS_CODES = [200, 201]


def get_api_base_url() -> str:
    """Get API base URL from environment and normalize (remove trailing slash).

    Returns:
        str: API base URL without trailing slash (e.g., "http://localhost:8000")
    """
    default = "http://localhost:8000"
    api_url = os.environ.get("API_BASE_URL", default)
    # Remove trailing slash if present
    return api_url.rstrip("/")


def build_headers(actor_id: str) -> dict[str, str]:
    """Build HTTP headers for API requests.

    Args:
        actor_id: Actor ID to include in header

    Returns:
        dict: Headers dict with X-Actor-Id
    """
    return {"X-Actor-Id": actor_id}


def post_generate_card(
    base_url: str, headers: dict[str, str], payload: dict[str, Any]
) -> requests.Response | None:
    """Call the API to generate a card.

    Args:
        base_url: API base URL
        headers: HTTP headers
        payload: Request payload

    Returns:
        Response object or None if request failed
    """
    if not requests:
        return None

    try:
        response = requests.post(
            f"{base_url}{ENDPOINT_GENERATE_CARD}",
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return response
    except requests.RequestException:
        return None


def call_generate_card(
    base_url: str, headers: dict[str, str], payload: dict[str, Any]
) -> requests.Response | None:
    """Backwards-compatible wrapper for post_generate_card."""
    return post_generate_card(base_url, headers, payload)


def put_update_card(
    base_url: str,
    headers: dict[str, str],
    card_id: str,
    payload: dict[str, Any],
) -> requests.Response | None:
    """Call the API to update an existing card (PUT /cards/<card_id>)."""
    if not requests:
        return None
    try:
        response = requests.put(
            f"{base_url}{ENDPOINT_GENERATE_CARD}/{card_id}",
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return response
    except requests.RequestException:
        return None


def normalize_error(
    response: requests.Response | None = None, exc: Exception | None = None
) -> dict[str, Any]:
    """Normalize error response into consistent JSON format.

    Args:
        response: HTTP response (if available)
        exc: Exception (if available)

    Returns:
        dict: Error response with status and message
    """
    if exc is not None:
        if requests and isinstance(exc, requests.RequestException):
            return {
                "status": "error",
                "message": f"{ERROR_REQUEST_FAILED}: {exc!s}",
            }
        return {"status": "error", "message": f"{ERROR_UNEXPECTED}: {exc!s}"}

    if response is None:
        return {"status": "error", "message": ERROR_REQUESTS_NOT_AVAILABLE}

    # Try to extract error message from response JSON
    try:
        response_json = response.json()
        if isinstance(response_json, dict) and "message" in response_json:
            return {
                "status": "error",
                "message": f"API error {response.status_code}: {response_json['message']}",
            }
    except Exception:
        pass

    return {
        "status": "error",
        "message": f"{ERROR_API_FAILURE}: {response.status_code}",
    }
