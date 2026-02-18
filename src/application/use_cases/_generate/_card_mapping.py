"""Card data mapping functions."""

from __future__ import annotations

from typing import Any

from domain.cards.card import Card


def _card_to_preview(card: Card) -> dict[str, str]:
    """Extract preview-compatible dict (text fields) from an existing Card."""
    obj = card.objectives
    if isinstance(obj, dict):
        obj = obj.get("objective", str(obj))
    return {
        "armies": card.armies or "",
        "deployment": card.deployment or "",
        "layout": card.layout or "",
        "objectives": str(obj) if obj else "",
        "initial_priority": card.initial_priority or "",
        "name": card.name or "",
    }


def _card_to_full_data(card: Card) -> dict[str, Any]:
    """Extract ALL scenario data from an existing Card entity.

    Returns text fields, structured objectives (with VP), shapes,
    special_rules, and name — everything needed to fully replicate
    a scenario.
    """
    return {
        "armies": card.armies or "",
        "deployment": card.deployment or "",
        "layout": card.layout or "",
        "objectives": card.objectives,  # preserves dict w/ VP
        "initial_priority": card.initial_priority or "",
        "name": card.name or "",
        "special_rules": card.special_rules,
        "deployment_shapes": card.map_spec.deployment_shapes or [],
        "objective_shapes": card.map_spec.objective_shapes or [],
        "scenography_specs": card.map_spec.shapes or [],
    }
