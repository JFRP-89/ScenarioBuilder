"""Seed resolution logic for scenario card generation."""

from __future__ import annotations

import random
from typing import Optional, Union

from application.use_cases._generate._dtos import GenerateScenarioCardRequest
from application.use_cases._generate._text_utils import _is_blank_text
from application.use_cases._generate._themes import _CONTENT_THEMES
from domain.cards.card import Card

_ContentDict = dict[str, Optional[Union[str, dict]]]

_FIELDS = ("armies", "deployment", "layout", "objectives", "initial_priority")


def _pick(request_val: Optional[str], fallback: Optional[str]) -> Optional[str]:
    """Return *fallback* when the user left the field blank, else the user value."""
    return fallback if _is_blank_text(request_val) else request_val


def _pick_objectives(
    request_val: Optional[Union[str, dict]],
    fallback: Optional[Union[str, dict]],
) -> Optional[Union[str, dict]]:
    """Objectives can be str or dict, so blank-check is slightly different."""
    if request_val is None:
        return fallback
    if isinstance(request_val, str) and not request_val.strip():
        return fallback
    return request_val


def _resolve_from_existing(
    request: GenerateScenarioCardRequest,
    card: Card,
) -> _ContentDict:
    """Resolve fields from an existing card, deferring to user values."""
    return {
        "armies": _pick(request.armies, card.armies),
        "deployment": _pick(request.deployment, card.deployment),
        "layout": _pick(request.layout, card.layout),
        "objectives": _pick_objectives(request.objectives, card.objectives),
        "initial_priority": _pick(request.initial_priority, card.initial_priority),
    }


def _resolve_from_theme(
    seed: int,
    request: GenerateScenarioCardRequest,
) -> _ContentDict:
    """Resolve fields from the theme catalog using deterministic RNG."""
    rng = random.Random(seed)  # nosec B311
    theme = rng.choice(list(_CONTENT_THEMES.keys()))
    tv = _CONTENT_THEMES[theme]

    return {
        "armies": _pick(request.armies, rng.choice(tv["armies"])),
        "deployment": _pick(request.deployment, rng.choice(tv["deployment"])),
        "layout": _pick(request.layout, rng.choice(tv["layout"])),
        "objectives": _pick_objectives(
            request.objectives, rng.choice(tv["objectives"])
        ),
        "initial_priority": _pick(
            request.initial_priority, rng.choice(tv["initial_priority"])
        ),
    }


def _resolve_seeded_content(
    seed: int,
    request: GenerateScenarioCardRequest,
    existing_card: Optional[Card] = None,
) -> _ContentDict:
    """Resolve text content fields from seed, existing card, or themes.

    Returns dict with keys: armies, deployment, layout, objectives,
    initial_priority.  User-provided (non-blank) values always take
    priority over seed/card/theme defaults.
    """
    if seed <= 0:
        return {f: getattr(request, f) for f in _FIELDS}

    if existing_card is not None:
        return _resolve_from_existing(request, existing_card)

    return _resolve_from_theme(seed, request)
