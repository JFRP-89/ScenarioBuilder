"""Seed resolution logic for scenario card generation."""

from __future__ import annotations

import random
from typing import Optional, Union

from application.use_cases._generate._dtos import GenerateScenarioCardRequest
from application.use_cases._generate._text_utils import _is_blank_text
from application.use_cases._generate._themes import _CONTENT_THEMES
from domain.cards.card import Card


def _resolve_seeded_content(
    seed: int,
    request: GenerateScenarioCardRequest,
    existing_card: Optional[Card] = None,
) -> dict[str, Optional[Union[str, dict]]]:
    """Resolve text content fields from seed, existing card, or themes.

    Returns dict with keys: armies, deployment, layout, objectives,
    initial_priority.  User-provided (non-blank) values always take
    priority over seed/card/theme defaults.
    """
    if seed <= 0:
        return {
            "armies": request.armies,
            "deployment": request.deployment,
            "layout": request.layout,
            "objectives": request.objectives,
            "initial_priority": request.initial_priority,
        }

    # If an existing card with this seed exists, use its data as defaults.
    if existing_card is not None:
        armies = (
            existing_card.armies if _is_blank_text(request.armies) else request.armies
        )
        deployment = (
            existing_card.deployment
            if _is_blank_text(request.deployment)
            else request.deployment
        )
        layout = (
            existing_card.layout if _is_blank_text(request.layout) else request.layout
        )
        objectives: Optional[Union[str, dict]] = request.objectives
        if objectives is None or (
            isinstance(objectives, str) and not objectives.strip()
        ):
            objectives = existing_card.objectives
        initial_priority = (
            existing_card.initial_priority
            if _is_blank_text(request.initial_priority)
            else request.initial_priority
        )
        return {
            "armies": armies,
            "deployment": deployment,
            "layout": layout,
            "objectives": objectives,
            "initial_priority": initial_priority,
        }

    # Fall back to theme-based generation.
    rng = random.Random(seed)  # nosec B311
    theme = rng.choice(list(_CONTENT_THEMES.keys()))
    theme_values = _CONTENT_THEMES[theme]

    armies = (
        rng.choice(theme_values["armies"])
        if _is_blank_text(request.armies)
        else request.armies
    )
    deployment = (
        rng.choice(theme_values["deployment"])
        if _is_blank_text(request.deployment)
        else request.deployment
    )
    layout = (
        rng.choice(theme_values["layout"])
        if _is_blank_text(request.layout)
        else request.layout
    )

    objectives = request.objectives
    if objectives is None or (isinstance(objectives, str) and not objectives.strip()):
        objectives = rng.choice(theme_values["objectives"])

    initial_priority = (
        rng.choice(theme_values["initial_priority"])
        if _is_blank_text(request.initial_priority)
        else request.initial_priority
    )

    return {
        "armies": armies,
        "deployment": deployment,
        "layout": layout,
        "objectives": objectives,
        "initial_priority": initial_priority,
    }
