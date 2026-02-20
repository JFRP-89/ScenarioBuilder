"""Card result helpers — augmentation, table conversion, ordering."""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.constants import (
    FIELD_MODE,
    FIELD_SEED,
    TABLE_MASSIVE_CM,
    TABLE_STANDARD_CM,
)

# ── Constants ──────────────────────────────────────────────────────────

_PAYLOAD_FILL_KEYS = (
    FIELD_MODE,
    FIELD_SEED,
    "armies",
    "deployment",
    "layout",
    "objectives",
    "special_rules",
    "visibility",
    "shared_with",
)

_CARD_KEYS_ORDER = [
    "card_id",
    "seed",
    "owner_id",
    "name",
    "mode",
    "armies",
    "table_preset",
    "table_mm",
    "layout",
    "deployment",
    "initial_priority",
    "objectives",
    "special_rules",
    "visibility",
    "shared_with",
    "shapes",
]

_EXCLUDED_KEYS = frozenset(("map_specs", "deployment_shapes"))


def table_cm_from_preset(preset: str) -> dict[str, float]:
    """Return table dimensions in cm for a known preset."""
    if preset == "massive":
        w, h = TABLE_MASSIVE_CM
    else:
        w, h = TABLE_STANDARD_CM
    return {"width_cm": float(w), "height_cm": float(h)}


def build_table_mm_from_cm(table_cm: dict[str, float]) -> dict[str, int]:
    """Convert table sizes from cm to mm."""
    return {
        "width_mm": int(round(table_cm["width_cm"] * 10)),
        "height_mm": int(round(table_cm["height_cm"] * 10)),
    }


def reorder_table_dimensions(table: Any, width_key: str, height_key: str) -> Any:
    """Return table dict with *width_key* before *height_key*."""
    if not isinstance(table, dict):
        return table

    ordered: dict[str, Any] = {}
    if width_key in table:
        ordered[width_key] = table[width_key]
    if height_key in table:
        ordered[height_key] = table[height_key]
    return ordered or table


def _fill_from_payload(result: dict[str, Any], payload: dict[str, Any]) -> None:
    """Copy keys from *payload* to *result* if missing."""
    for key in _PAYLOAD_FILL_KEYS:
        if key in payload and key not in result:
            result[key] = payload[key]


def _order_card_keys(result: dict[str, Any]) -> dict[str, Any]:
    """Order card dictionary keys according to standard display order."""
    ordered: dict[str, Any] = {}
    for key in _CARD_KEYS_ORDER:
        if key in result:
            ordered[key] = result[key]
    for key in result:
        if key not in ordered and key not in _EXCLUDED_KEYS:
            ordered[key] = result[key]
    return ordered


def augment_generated_card(
    response_json: dict[str, Any],
    payload: dict[str, Any],
    preset: str,
    custom_table: dict[str, float] | None,
) -> dict[str, Any]:
    """Ensure displayed card includes UI fields and returns in exact order."""
    result = dict(response_json)

    if preset:
        result.setdefault("table_preset", preset)

    if custom_table:
        result["table_mm"] = build_table_mm_from_cm(custom_table)
        result.pop("table_cm", None)

    _fill_from_payload(result, payload)

    if "table_mm" in result:
        result["table_mm"] = reorder_table_dimensions(
            result["table_mm"], "width_mm", "height_mm"
        )
    if "table_cm" in result:
        result["table_cm"] = reorder_table_dimensions(
            result["table_cm"], "width_cm", "height_cm"
        )

    result.pop("map_specs", None)
    result.pop("deployment_shapes", None)

    return _order_card_keys(result)
