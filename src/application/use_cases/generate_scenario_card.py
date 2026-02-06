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
    armies: Optional[str] = None
    deployment: Optional[str] = None
    layout: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    initial_priority: Optional[str] = None
    name: Optional[str] = None
    special_rules: Optional[str] = None
    map_specs: Optional[list[dict]] = None
    deployment_shapes: Optional[list[dict]] = None
    objective_shapes: Optional[list[dict]] = None


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
    table_mm: dict
    initial_priority: str
    visibility: str
    # Shape mapping: deployment_shapes, objective_shapes, scenography_specs
    shapes: dict
    card: Card  # Domain entity ready for persistence
    table_preset: Optional[str] = None
    armies: Optional[str] = None
    layout: Optional[str] = None
    deployment: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    special_rules: Optional[list[dict]] = None
    shared_with: Optional[list[str]] = None


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

    def execute(
        self, request: GenerateScenarioCardRequest
    ) -> GenerateScenarioCardResponse:
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
        seed = (
            request.seed
            if request.seed is not None
            else self._seed_generator.generate_seed()
        )

        # 4) Resolve mode
        mode = self._resolve_mode(request.mode)

        # 5) Resolve visibility
        visibility = self._resolve_visibility(request.visibility)

        # 6) Generate shapes via port
        shapes = self._scenario_generator.generate_shapes(
            seed=seed, table=table, mode=mode
        )

        # 6a) Enforce contract: shapes MUST be list[dict], not dict
        if not isinstance(shapes, list):
            raise ValidationError(
                f"ScenarioGenerator contract violation: generate_shapes() returned "
                f"{type(shapes).__name__}, expected list[dict]. "
                f"The generator must return a flat list of shapes, not a structured dict."
            )
        if shapes and not all(isinstance(s, dict) for s in shapes):
            raise ValidationError(
                "ScenarioGenerator contract violation: shapes list contains non-dict elements"
            )

        # 7) Validate shapes with domain MapSpec (includes objective_shapes from request)
        map_spec = MapSpec(
            table=table, shapes=shapes, objective_shapes=request.objective_shapes
        )

        # 8) Generate card_id
        card_id = self._id_generator.generate_card_id()

        # 9) Construct Card to validate invariants
        card = Card(
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
            card=card,
            table_preset=request.table_preset,
            armies=request.armies,
            deployment=request.deployment,
            layout=request.layout,
            objectives=request.objectives,
            initial_priority=request.initial_priority,
            provided_name=request.name,
            special_rules=request.special_rules,
            shared_with=request.shared_with,
            map_specs=request.map_specs,
            deployment_shapes=request.deployment_shapes,
            objective_shapes=request.objective_shapes,
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
        card: Card,
        table_preset: Optional[str] = None,
        armies: Optional[str] = None,
        deployment: Optional[str] = None,
        layout: Optional[str] = None,
        objectives: Optional[Union[str, dict]] = None,
        initial_priority: Optional[str] = None,
        provided_name: Optional[str] = None,
        special_rules: Optional[Union[str, list[dict]]] = None,
        shared_with: Optional[Collection[str]] = None,
        map_specs: Optional[list[dict]] = None,
        deployment_shapes: Optional[list[dict]] = None,
        objective_shapes: Optional[list[dict]] = None,
    ) -> GenerateScenarioCardResponse:
        """Build response DTO from components.

        Returns structure with shapes as nested dict containing:
        - deployment_shapes
        - objective_shapes
        - scenography_specs
        - card: validated Card domain entity ready for persistence
        """
        # Use provided name or generate from layout and deployment
        if provided_name and provided_name.strip():
            name = provided_name.strip()
        else:
            name = self._generate_card_name(layout, deployment)

        # Use provided initial_priority or default
        priority = initial_priority or "Check the rulebook rules for it"

        # Separate shapes into deployment_shapes and scenography_specs
        # Start with auto-generated shapes from seed
        auto_deployment_shapes = [
            s for s in shapes if s.get("type") == "rect" and "borders" in s
        ]

        # Merge with user-provided shapes (user-provided takes precedence)
        # For deployment_shapes: use user-provided if available, else auto-generated
        # For scenography_specs: only include if explicitly provided by user
        final_deployment_shapes = (
            deployment_shapes if deployment_shapes else auto_deployment_shapes
        )
        final_scenography_specs = map_specs if map_specs else []
        final_objective_shapes = objective_shapes if objective_shapes else []

        # Validate final merged shapes with domain (post-merge validation)
        # This ensures that user-provided shapes + auto-generated shapes together
        # don't violate domain constraints (bounds, limits, etc.)
        all_map_shapes = final_deployment_shapes + final_scenography_specs
        try:
            MapSpec(
                table=table,
                shapes=all_map_shapes,
                objective_shapes=final_objective_shapes,
            )
        except ValidationError as e:
            # Re-raise with context about merge validation
            raise ValidationError(
                "Final shapes validation failed after merging user input "
                f"with generated shapes: {e}"
            ) from e

        # Parse special_rules to list[dict] if it's a string
        final_special_rules = None
        if special_rules:
            if isinstance(special_rules, list):
                final_special_rules = special_rules
            elif isinstance(special_rules, str):
                # Parse string to list of dicts (simplified for now, can be enhanced)
                final_special_rules = [
                    {"name": "Custom Rule", "description": special_rules}
                ]

        # Convert shared_with to list if needed
        final_shared_with = list(shared_with) if shared_with else []

        return GenerateScenarioCardResponse(
            card_id=card_id,
            seed=seed,
            owner_id=owner_id,
            name=name,
            mode=mode.value,
            table_mm={"width_mm": table.width_mm, "height_mm": table.height_mm},
            initial_priority=priority,
            visibility=visibility.value,
            shapes={
                "deployment_shapes": final_deployment_shapes,
                "objective_shapes": final_objective_shapes,
                "scenography_specs": final_scenography_specs,
            },
            card=card,
            table_preset=table_preset,
            armies=armies,
            layout=layout,
            deployment=deployment,
            objectives=objectives,
            special_rules=final_special_rules,
            shared_with=final_shared_with,
        )

    def _generate_card_name(
        self, layout: Optional[str], deployment: Optional[str]
    ) -> str:
        """Generate a descriptive card name from layout and deployment."""
        if layout and deployment or layout:
            return f"Battle for {layout}"
        elif deployment:
            return f"Battle with {deployment}"
        else:
            return "Battle Scenario"

    def _resolve_mode(self, mode: Union[str, GameMode]) -> GameMode:
        """Resolve mode to GameMode enum."""
        if isinstance(mode, GameMode):
            return mode
        return parse_game_mode(mode)

    def _resolve_visibility(
        self, visibility: Optional[Union[str, Visibility]]
    ) -> Visibility:
        """Resolve visibility to Visibility enum, defaulting to PRIVATE."""
        if visibility is None:
            return Visibility.PRIVATE
        if isinstance(visibility, Visibility):
            return visibility
        return parse_visibility(visibility)
