"""Ports for scenario generation capabilities.

These ports define the interfaces for external concerns like ID generation,
seed generation, and scenario content generation that the application layer
depends on but doesn't implement.
"""

from __future__ import annotations

from typing import Protocol

from domain.cards.card import GameMode
from domain.maps.table_size import TableSize


class IdGenerator(Protocol):
    """Port for generating unique card IDs."""

    def generate_card_id(self) -> str:
        """Generate a unique card identifier.

        Returns:
            Unique card ID string.
        """
        ...


class SeedGenerator(Protocol):
    """Port for generating deterministic seeds."""

    def generate_seed(self) -> int:
        """Generate a seed for scenario generation.

        Returns:
            Integer seed >= 0.
        """
        ...


class ScenarioGenerator(Protocol):
    """Port for generating scenario shapes based on game rules.

    CONTRACT SPECIFICATION
    ======================

    generate_shapes() MUST return: list[dict]
    generate_shapes() MUST NOT return: dict

    The return value is a flat list of shape dictionaries that are compatible
    with domain.maps.map_spec.MapSpec. Each shape dict must contain at minimum:
    - type: str (e.g., "rect", "circle", "polygon")
    - Position/dimension fields appropriate for the type

    RATIONALE
    =========

    1. Domain Compatibility: MapSpec expects list[dict] for shapes parameter
    2. Separation of Concerns: Generator shouldn't know about API response structure
       (deployment_shapes vs scenography_specs is API concern, not generation concern)
    3. Composition: Use cases are responsible for transforming flat shapes list
       into structured API responses when needed
    4. Testability: Simple list[dict] is easier to validate and test

    ANTI-PATTERN
    ============

    ❌ DO NOT return structured dict like:
       {"deployment_shapes": [...], "scenography_specs": [...]}

    ✅ DO return flat list like:
       [{"type": "rect", "x": 0, "y": 0, ...}, {"type": "circle", ...}]
    """

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        """Generate scenario shapes for given parameters.

        Args:
            seed: Deterministic seed for reproducibility.
            table: Table dimensions for bounds validation.
            mode: Game mode affecting generation rules.

        Returns:
            List of shape dictionaries compatible with MapSpec.
            Each shape must be a dict with 'type' and appropriate fields.

        Raises:
            ValueError: If parameters are invalid (e.g., negative seed).

        Contract:
            Return type MUST be list[dict], never dict.
            See class docstring for full contract specification.
        """
        ...
