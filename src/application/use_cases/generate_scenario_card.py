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
from domain.cards.card_content_validation import (
    validate_objectives,
    validate_shared_with_visibility,
    validate_special_rules,
)
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility, parse_visibility

# =============================================================================
# TABLE PRESETS
# =============================================================================
_TABLE_PRESETS = frozenset(["standard", "massive", "custom"])


def _resolve_table(
    preset: str,
    width_mm: Optional[int] = None,
    height_mm: Optional[int] = None,
) -> TableSize:
    """Resolve table preset to TableSize.

    Args:
        preset: Table preset ("standard", "massive", or "custom")
        width_mm: Width in mm (required if preset is "custom")
        height_mm: Height in mm (required if preset is "custom")

    Returns:
        TableSize instance

    Raises:
        ValidationError: If preset is unknown or custom dimensions are invalid
    """
    if preset == "standard":
        return TableSize.standard()
    elif preset == "massive":
        return TableSize.massive()
    elif preset == "custom":
        if width_mm is None or height_mm is None:
            raise ValidationError(
                "Custom table preset requires table_width_mm and table_height_mm"
            )
        # TableSize constructor validates dimensions
        return TableSize(width_mm=width_mm, height_mm=height_mm)
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
    special_rules: Optional[Union[str, list[dict]]] = None
    map_specs: Optional[list[dict]] = None
    scenography_specs: Optional[list[dict]] = None
    deployment_shapes: Optional[list[dict]] = None
    objective_shapes: Optional[list[dict]] = None
    # Custom table dimensions (when table_preset is "custom")
    table_width_mm: Optional[int] = None
    table_height_mm: Optional[int] = None


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

        # 2) Resolve table from preset (and custom dimensions if applicable)
        table = _resolve_table(
            request.table_preset,
            width_mm=request.table_width_mm,
            height_mm=request.table_height_mm,
        )

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

        # 5a) Validate content fields
        validate_objectives(request.objectives)
        validate_special_rules(
            request.special_rules
            if not isinstance(request.special_rules, str)
            else None
        )
        validate_shared_with_visibility(visibility, request.shared_with)

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

        # 8a) Resolve name for the scenario
        name = self._resolve_name(request.name, request.layout, request.deployment)

        # 8b) Resolve content fields
        final_special_rules = self._resolve_special_rules(request.special_rules)
        final_shared_with = list(request.shared_with) if request.shared_with else None

        # 9) Construct Card to validate invariants (now includes content fields)
        card = Card(
            card_id=card_id,
            owner_id=actor_id,
            visibility=visibility,
            shared_with=final_shared_with,
            mode=mode,
            seed=seed,
            table=table,
            map_spec=map_spec,
            name=name,
            armies=request.armies,
            deployment=request.deployment,
            layout=request.layout,
            objectives=request.objectives,
            initial_priority=request.initial_priority
            or "Check the rulebook rules for it",
            special_rules=final_special_rules,
        )

        # 10) Build response DTO
        return self._build_response(
            card_id=card_id,
            owner_id=actor_id,
            seed=seed,
            mode=mode,
            visibility=visibility,
            table=table,
            card=card,
            request=request,
        )

    def _build_response(
        self,
        card_id: str,
        owner_id: str,
        seed: int,
        mode: GameMode,
        visibility: Visibility,
        table: TableSize,
        card: Card,
        request: GenerateScenarioCardRequest,
    ) -> GenerateScenarioCardResponse:
        """Build response DTO from components.

        Returns structure with shapes as nested dict containing:
        - deployment_shapes
        - objective_shapes
        - scenography_specs
        - card: validated Card domain entity ready for persistence
        """
        # Name is already in the Card object
        name = card.name or ""
        priority = request.initial_priority or "Check the rulebook rules for it"
        final_shapes = self._resolve_final_shapes(request, table)
        final_special_rules = self._resolve_special_rules(request.special_rules)
        final_shared_with = list(request.shared_with) if request.shared_with else []

        return GenerateScenarioCardResponse(
            card_id=card_id,
            seed=seed,
            owner_id=owner_id,
            name=name,
            mode=mode.value,
            table_mm={"width_mm": table.width_mm, "height_mm": table.height_mm},
            initial_priority=priority,
            visibility=visibility.value,
            shapes=final_shapes,
            card=card,
            table_preset=request.table_preset,
            armies=request.armies,
            layout=request.layout,
            deployment=request.deployment,
            objectives=request.objectives,
            special_rules=final_special_rules,
            shared_with=final_shared_with,
        )

    def _resolve_final_shapes(
        self, request: GenerateScenarioCardRequest, table: TableSize
    ) -> dict:
        """Resolve and validate final shape lists from request."""
        final_deployment = request.deployment_shapes or []
        final_scenography = request.scenography_specs or request.map_specs or []
        final_objectives = request.objective_shapes or []

        try:
            MapSpec(
                table=table,
                shapes=final_scenography,
                objective_shapes=final_objectives,
                deployment_shapes=final_deployment or None,
            )
        except ValidationError as e:
            raise ValidationError(
                "Final shapes validation failed after merging user input "
                f"with generated shapes: {e}"
            ) from e

        return {
            "deployment_shapes": final_deployment,
            "objective_shapes": final_objectives,
            "scenography_specs": final_scenography,
        }

    @staticmethod
    def _resolve_special_rules(
        special_rules: Optional[Union[str, list[dict]]],
    ) -> Optional[list[dict]]:
        """Parse special_rules to list[dict] format."""
        if not special_rules:
            return None
        if isinstance(special_rules, list):
            return special_rules
        if isinstance(special_rules, str):
            return [{"name": "Custom Rule", "description": special_rules}]
        return None

    def _resolve_name(
        self,
        provided_name: Optional[str],
        layout: Optional[str],
        deployment: Optional[str],
    ) -> str:
        """Resolve card name from provided name or layout/deployment."""
        if provided_name and provided_name.strip():
            return provided_name.strip()
        return self._generate_card_name(layout, deployment)

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
