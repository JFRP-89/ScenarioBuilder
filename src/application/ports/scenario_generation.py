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
    """Port for generating scenario shapes based on game rules."""

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
        """
        ...
