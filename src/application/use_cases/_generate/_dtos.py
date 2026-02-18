"""Request and Response DTOs for GenerateScenarioCard use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection, Optional, Union

from domain.cards.card import Card, GameMode
from domain.security.authz import Visibility


@dataclass
class GenerateScenarioCardRequest:
    """Request DTO for GenerateScenarioCard use case."""

    actor_id: Optional[str]
    mode: Union[str, GameMode]
    seed: Optional[int]
    table_preset: str
    visibility: Optional[Union[str, Visibility]]
    shared_with: Optional[Collection[str]]
    armies: Optional[str] = None
    deployment: Optional[str] = None
    layout: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    initial_priority: Optional[str] = None
    name: Optional[str] = None
    special_rules: Optional[Union[str, list[dict]]] = None
    map_specs: Optional[list[dict]] = None
    scenography_specs: Optional[list[dict]] = None
    deployment_shapes: Optional[list[dict]] = None
    objective_shapes: Optional[list[dict]] = None
    # Custom table dimensions (when table_preset is "custom")
    table_width_mm: Optional[int] = None
    table_height_mm: Optional[int] = None
    # If provided, reuses this card_id (for update/edit flows)
    card_id: Optional[str] = None
    # If True, user designs scenario manually from scratch (no seed auto-fill).
    # If False or None, the optional generate_from_seed field can be used.
    is_replicable: Optional[bool] = None
    # Optional seed for "Generate Scenario From Seed" — auto-fills all content
    # fields when provided.  Mutually exclusive with is_replicable=True.
    generate_from_seed: Optional[int] = None


@dataclass
class GenerateScenarioCardResponse:
    """Response DTO for GenerateScenarioCard use case.

    Fields match the production schema:
    - shapes dict contains deployment_shapes, objective_shapes, scenography_specs
    - objectives can be a string or dict with 'objective' and 'victory_points'
    - special_rules is a list of dicts (not a string)
    - card: The validated Card domain entity ready for persistence
    """

    card_id: str
    seed: int
    owner_id: str
    name: str
    mode: str
    table_mm: dict[str, Any]
    initial_priority: str
    visibility: str
    # Shape mapping: deployment_shapes, objective_shapes, scenography_specs
    shapes: dict[str, Any]
    card: Card  # Domain entity ready for persistence
    is_replicable: bool  # Whether scenario was generated as replicable
    table_preset: Optional[str] = None
    armies: Optional[str] = None
    layout: Optional[str] = None
    deployment: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    special_rules: Optional[list[dict]] = None
    shared_with: Optional[list[str]] = None
