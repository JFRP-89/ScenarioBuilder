"""Shared API call helpers for E2E tests.

Eliminates duplicate ``requests.post`` / ``requests.get`` boilerplate
that otherwise triggers pylint R0801 (duplicate-code).
"""

from __future__ import annotations

import requests
from e2e._support import get_api_base_url

__all__ = ["get_api_base_url", "get_map_svg", "matched_payload", "post_card"]


def matched_payload(seed: int = 123) -> dict[str, object]:
    """Return a standard matched-mode payload for card creation."""
    return {
        "mode": "matched",
        "seed": seed,
        "table_preset": "standard",
        "visibility": "private",
    }


def post_card(
    api_url: str,
    headers: dict[str, str],
    payload: dict,
) -> requests.Response:
    """POST /cards and return the raw response."""
    return requests.post(
        f"{api_url}/cards",
        headers=headers,
        json=payload,
        timeout=30,
    )


def get_map_svg(
    api_url: str,
    card_id: str,
    headers: dict[str, str],
) -> requests.Response:
    """GET /cards/{card_id}/map.svg and return the raw response."""
    return requests.get(
        f"{api_url}/cards/{card_id}/map.svg",
        headers=headers,
        timeout=30,
    )
