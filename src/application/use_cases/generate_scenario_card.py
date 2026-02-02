"""GenerateScenarioCard use case.

Generates a new scenario card by orchestrating domain logic and ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Optional, Union

from application.ports.scenario_generation import (
    IdGenerator,
    ScenarioGenerator,
    SeedGenerator,
)
from application.use_cases._validation import validate_actor_id
from domain.cards.card import Card, GameMode, parse_game_mode
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility, parse_visibility

# =============================================================================
# TABLE PRESETS
# =============================================================================
_TABLE_PRESETS = frozenset(["standard", "massive"])


def _resolve_table(preset: str) -> TableSize:
    """Resolve table preset to TableSize."""
    if preset == "standard":
        return TableSize.standard()
    elif preset == "massive":
        return TableSize.massive()
    else:
        raise ValidationError(
            f"unknown table preset '{preset}', "
            f"must be one of: {', '.join(sorted(_TABLE_PRESETS))}"
        )


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class GenerateScenarioCardRequest:
    """Request DTO for GenerateScenarioCard use case."""

    actor_id: Optional[str]
    mode: Union[str, GameMode]
    seed: Optional[int]
    table_preset: str
    visibility: Optional[Union[str, Visibility]]
    shared_with: Optional[Collection[str]]


@dataclass
class GenerateScenarioCardResponse:
    """Response DTO for GenerateScenarioCard use case."""

    card_id: str
    owner_id: str
    seed: int
    mode: str
    visibility: str
    table_mm: dict
    shapes: list[dict]


# =============================================================================
# USE CASE
# =============================================================================
class GenerateScenarioCard:
    """Use case for generating a new scenario card."""

    def __init__(
        self,
        id_generator: IdGenerator,
        seed_generator: SeedGenerator,
        scenario_generator: ScenarioGenerator,
    ) -> None:
        self._id_generator = id_generator
        self._seed_generator = seed_generator
        self._scenario_generator = scenario_generator

    def execute(self, request: GenerateScenarioCardRequest) -> GenerateScenarioCardResponse:
        """Execute the use case.

        Args:
            request: Request DTO with generation parameters.

        Returns:
            Response DTO with generated card data.

        Raises:
            ValidationError: If any input validation fails.
        """
        # 1) Validate actor_id
        actor_id = validate_actor_id(request.actor_id)

        # 2) Resolve table from preset
        table = _resolve_table(request.table_preset)

        # 3) Resolve seed
        seed = request.seed if request.seed is not None else self._seed_generator.generate_seed()

        # 4) Resolve mode
        mode = self._resolve_mode(request.mode)

        # 5) Resolve visibility
        visibility = self._resolve_visibility(request.visibility)

        # 6) Generate shapes via port
        shapes = self._scenario_generator.generate_shapes(seed=seed, table=table, mode=mode)

        # 7) Validate shapes with domain MapSpec
        map_spec = MapSpec(table=table, shapes=shapes)

        # 8) Generate card_id
        card_id = self._id_generator.generate_card_id()

        # 9) Construct Card to validate invariants
        Card(
            card_id=card_id,
            owner_id=actor_id,
            visibility=visibility,
            shared_with=request.shared_with,
            mode=mode,
            seed=seed,
            table=table,
            map_spec=map_spec,
        )

        # 10) Build response DTO
        return self._build_response(
            card_id=card_id,
            owner_id=actor_id,
            seed=seed,
            mode=mode,
            visibility=visibility,
            table=table,
            shapes=shapes,
        )

    def _build_response(
        self,
        card_id: str,
        owner_id: str,
        seed: int,
        mode: GameMode,
        visibility: Visibility,
        table: TableSize,
        shapes: list[dict],
    ) -> GenerateScenarioCardResponse:
        """Build response DTO from components."""
        return GenerateScenarioCardResponse(
            card_id=card_id,
            owner_id=owner_id,
            seed=seed,
            mode=mode.value,
            visibility=visibility.value,
            table_mm={"width_mm": table.width_mm, "height_mm": table.height_mm},
            shapes=shapes,
        )

    def _resolve_mode(self, mode: Union[str, GameMode]) -> GameMode:
        """Resolve mode to GameMode enum."""
        if isinstance(mode, GameMode):
            return mode
        return parse_game_mode(mode)

    def _resolve_visibility(self, visibility: Optional[Union[str, Visibility]]) -> Visibility:
        """Resolve visibility to Visibility enum, defaulting to PRIVATE."""
        if visibility is None:
            return Visibility.PRIVATE
        if isinstance(visibility, Visibility):
            return visibility
        return parse_visibility(visibility)
