"""GenerateScenarioCard use case — thin facade.

Orchestrates domain logic and ports for scenario card generation.
All helper functions and DTOs live in ``_generate.*`` sub-modules;
this file re-exports the public/test-visible symbols for backward
compatibility.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from application.ports.repositories import CardRepository
from application.ports.scenario_generation import (
    IdGenerator,
    ScenarioGenerator,
    SeedGenerator,
)
from application.use_cases._generate._card_mapping import (  # re-export
    _card_to_full_data as _card_to_full_data,
)
from application.use_cases._generate._card_mapping import (
    _card_to_preview as _card_to_preview,
)
from application.use_cases._generate._dtos import (  # re-export
    GenerateScenarioCardRequest as GenerateScenarioCardRequest,
)
from application.use_cases._generate._dtos import (
    GenerateScenarioCardResponse as GenerateScenarioCardResponse,
)
from application.use_cases._generate._seed_resolution import (
    _resolve_seeded_content,
)
from application.use_cases._generate._shape_generation import (  # re-export
    _generate_seeded_shapes as _generate_seeded_shapes,
)
from application.use_cases._generate._table_resolution import _resolve_table
from application.use_cases._generate._text_utils import (
    _objectives_match_seed as _objectives_match_seed,  # re-export
)
from application.use_cases._generate._themes import (
    _resolve_seed_from_themes,
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
# MODULE-LEVEL HELPERS (pure functions, no self)
# =============================================================================
def _resolve_mode(mode: Union[str, GameMode]) -> GameMode:
    """Resolve mode to GameMode enum."""
    if isinstance(mode, GameMode):
        return mode
    return parse_game_mode(mode)


def _resolve_visibility(
    visibility: Optional[Union[str, Visibility]],
) -> Visibility:
    """Resolve visibility to Visibility enum, defaulting to PRIVATE."""
    if visibility is None:
        return Visibility.PRIVATE
    if isinstance(visibility, Visibility):
        return visibility
    return parse_visibility(visibility)


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


def _resolve_final_shapes(card: Card) -> dict:
    """Resolve final shape lists from card's map_spec."""
    return {
        "deployment_shapes": card.map_spec.deployment_shapes or [],
        "objective_shapes": card.map_spec.objective_shapes or [],
        "scenography_specs": card.map_spec.shapes or [],
    }


def _generate_card_name(layout: Optional[str], deployment: Optional[str]) -> str:
    """Generate a descriptive card name from layout and deployment."""
    if layout and deployment or layout:
        return f"Battle for {layout}"
    elif deployment:
        return f"Battle with {deployment}"
    else:
        return "Battle Scenario"


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
        card_repository: Optional[CardRepository] = None,
    ) -> None:
        self._id_generator = id_generator
        self._seed_generator = seed_generator
        self._scenario_generator = scenario_generator
        self._card_repository = card_repository

    # ── public seed resolution (repo-aware) ──────────────────────────────

    def find_card_by_seed(self, seed: int) -> Optional[Card]:
        """Look up a card by seed number.

        Returns the first matching ``Card`` or ``None`` when no card
        with that seed exists (or no repository is configured).
        """
        if seed <= 0 or self._card_repository is None:
            return None
        return self._card_repository.find_by_seed(seed)

    def resolve_seed_preview(self, seed: int) -> dict[str, str]:
        """Resolve text content fields from a seed.

        If a card with the given seed already exists in the repository,
        returns that card's text content fields (incl. name).
        Otherwise falls back to theme-based generation.
        """
        if seed <= 0:
            return {
                "armies": "",
                "deployment": "",
                "layout": "",
                "objectives": "",
                "initial_priority": "",
                "name": "",
            }
        if self._card_repository is not None:
            existing = self._card_repository.find_by_seed(seed)
            if existing is not None:
                return _card_to_preview(existing)
        result: dict[str, str] = _resolve_seed_from_themes(seed)
        result["name"] = ""
        return result

    def resolve_full_seed_scenario(
        self,
        seed: int,
        table_width: int,
        table_height: int,
    ) -> dict[str, Any]:
        """Resolve COMPLETE scenario data from a seed (repo-aware)."""
        if seed <= 0:
            return {
                "armies": "",
                "deployment": "",
                "layout": "",
                "objectives": "",
                "initial_priority": "",
                "name": "",
                "special_rules": None,
                "deployment_shapes": [],
                "objective_shapes": [],
                "scenography_specs": [],
            }
        if self._card_repository is not None:
            existing = self._card_repository.find_by_seed(seed)
            if existing is not None:
                return _card_to_full_data(existing)
        text = _resolve_seed_from_themes(seed)
        shapes = _generate_seeded_shapes(seed, table_width, table_height)
        return {**text, "name": "", "special_rules": None, **shapes}

    # ── helpers for execute() ────────────────────────────────────────────

    def _resolve_seed_value(
        self,
        request: GenerateScenarioCardRequest,
        table: TableSize,
        effective_is_replicable: bool,
    ) -> int:
        """Resolve the seed value from request parameters."""
        if request.generate_from_seed and request.generate_from_seed > 0:
            return self._resolve_gfs_seed(request, table)

        if effective_is_replicable:
            if request.seed and request.seed > 0:
                return request.seed
            return int(
                self._seed_generator.calculate_from_config(
                    self._build_seed_config(request, table)
                )
            )

        return 0

    def _resolve_gfs_seed(
        self,
        request: GenerateScenarioCardRequest,
        table: TableSize,
    ) -> int:
        """Return *gfs* when content is unmodified, else hash(config)."""
        gfs = request.generate_from_seed
        assert gfs is not None, "_resolve_gfs_seed called with gfs=None"
        original = self.resolve_seed_preview(gfs)
        if self._is_content_unmodified(request, original):
            return gfs
        return int(
            self._seed_generator.calculate_from_config(
                self._build_seed_config(request, table)
            )
        )

    @staticmethod
    def _is_content_unmodified(
        request: GenerateScenarioCardRequest,
        original: dict[str, str],
    ) -> bool:
        """Check whether the user left every text field matching the seed."""
        from application.use_cases._generate._text_utils import _is_blank_text

        for field in ("armies", "deployment", "layout", "initial_priority"):
            val = getattr(request, field, None)
            if not _is_blank_text(val) and (val or "").strip() != original[field]:
                return False
        return _objectives_match_seed(request.objectives, original["objectives"])

    def _resolve_gfs_data(
        self,
        request: GenerateScenarioCardRequest,
        seed: int,
        table: TableSize,
    ) -> tuple[bool, dict[str, Any], dict[str, Any]]:
        """Resolve generate-from-seed data and seeded text content."""
        using_gfs = bool(request.generate_from_seed and request.generate_from_seed > 0)
        full_seed_data: dict[str, Any] = {}
        existing_card: Optional[Card] = None
        if using_gfs:
            if self._card_repository is not None:
                existing_card = self._card_repository.find_by_seed(seed)
            if existing_card is not None:
                full_seed_data = _card_to_full_data(existing_card)
            else:
                text = _resolve_seed_from_themes(seed)
                shapes = _generate_seeded_shapes(seed, table.width_mm, table.height_mm)
                full_seed_data = {
                    **text,
                    "name": "",
                    "special_rules": None,
                    **shapes,
                }
        seeded_content = (
            _resolve_seeded_content(seed, request, existing_card) if seed > 0 else {}
        )
        return using_gfs, full_seed_data, seeded_content

    # ------------------------------------------------------------------
    # execute() helpers — extracted to reduce cognitive complexity
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_replicability(
        request: GenerateScenarioCardRequest,
    ) -> bool:
        """Return effective replicability, raising if seed is used without it."""
        effective = bool(request.is_replicable)
        if not effective and request.generate_from_seed:
            raise ValidationError(
                "Cannot use 'Generate Scenario From Seed' when "
                "'Replicable Scenario' is disabled. "
                "Enable 'Replicable Scenario' to use a seed."
            )
        return effective

    @staticmethod
    def _resolve_content_fields(
        seeded_content: dict,
        request: GenerateScenarioCardRequest,
    ) -> tuple:
        """Pick seeded content over request content for text fields."""
        return (
            seeded_content.get("armies", request.armies),
            seeded_content.get("deployment", request.deployment),
            seeded_content.get("layout", request.layout),
            seeded_content.get("objectives", request.objectives),
            seeded_content.get("initial_priority", request.initial_priority),
        )

    @staticmethod
    def _resolve_shape_data(
        using_gfs: bool,
        full_seed_data: dict,
        request: GenerateScenarioCardRequest,
    ) -> tuple[list, Optional[list], Optional[list]]:
        """Resolve scenography, deployment and objective shapes.

        User-provided shapes take priority over seed-derived ones.
        """
        has_user_scenography = bool(request.scenography_specs or request.map_specs)
        has_user_deployment = bool(request.deployment_shapes)
        has_user_objectives = bool(request.objective_shapes)

        scenography = (
            full_seed_data.get("scenography_specs", [])
            if using_gfs and not has_user_scenography
            else request.scenography_specs or request.map_specs or []
        )
        deployment_shapes = (
            full_seed_data.get("deployment_shapes")
            if using_gfs and not has_user_deployment
            else request.deployment_shapes
        )
        objective_shapes = (
            full_seed_data.get("objective_shapes")
            if using_gfs and not has_user_objectives
            else request.objective_shapes
        )
        return scenography, deployment_shapes, objective_shapes

    @staticmethod
    def _resolve_card_name(
        request: GenerateScenarioCardRequest,
        using_gfs: bool,
        full_seed_data: dict,
        final_layout: Optional[str],
        final_deployment: Optional[str],
    ) -> str:
        """Pick name from request → seed → auto-generated."""
        if request.name and request.name.strip():
            return request.name.strip()
        seed_name = str(full_seed_data.get("name", "")) if using_gfs else ""
        if seed_name:
            return seed_name
        return _generate_card_name(final_layout, final_deployment)

    @staticmethod
    def _resolve_card_special_rules(
        request: GenerateScenarioCardRequest,
        using_gfs: bool,
        full_seed_data: dict,
    ) -> Optional[list[dict[str, Any]]]:
        """Pick special rules from request → seed → None."""
        if request.special_rules:
            return _resolve_special_rules(request.special_rules)
        if using_gfs and full_seed_data.get("special_rules"):
            raw = full_seed_data["special_rules"]
            return list(raw) if isinstance(raw, list) else None
        return None

    def execute(
        self, request: GenerateScenarioCardRequest
    ) -> GenerateScenarioCardResponse:
        """Execute the use case."""
        # 1) Validate actor_id
        actor_id = validate_actor_id(request.actor_id)

        # 2) Resolve table
        table = _resolve_table(
            request.table_preset,
            width_mm=request.table_width_mm,
            height_mm=request.table_height_mm,
        )

        # 3) Resolve seed (before auto-fill so hash uses raw request fields)
        effective_is_replicable = self._resolve_replicability(request)
        seed = self._resolve_seed_value(request, table, effective_is_replicable)

        # 4) Resolve mode & visibility
        mode = _resolve_mode(request.mode)
        visibility = _resolve_visibility(request.visibility)

        # 5) Resolve seeded content fields + shapes + secondary data
        using_gfs, full_seed_data, seeded_content = self._resolve_gfs_data(
            request, seed, table
        )
        (
            final_armies,
            final_deployment,
            final_layout,
            final_objectives,
            final_initial_priority,
        ) = self._resolve_content_fields(seeded_content, request)

        # 6) Validate content fields
        validate_objectives(final_objectives)
        validate_special_rules(
            request.special_rules
            if not isinstance(request.special_rules, str)
            else None
        )
        validate_shared_with_visibility(visibility, request.shared_with)

        # 7) Resolve shapes (user-provided take priority over seed)
        final_scenography, final_deployment_shapes, final_objective_shapes = (
            self._resolve_shape_data(using_gfs, full_seed_data, request)
        )

        # 8) Build MapSpec
        map_spec = MapSpec(
            table=table,
            shapes=final_scenography,
            objective_shapes=final_objective_shapes,
            deployment_shapes=final_deployment_shapes,
        )

        # 9) Resolve id, name, special_rules
        card_id = request.card_id or self._id_generator.generate_card_id()
        name = self._resolve_card_name(
            request,
            using_gfs,
            full_seed_data,
            final_layout,
            final_deployment,
        )
        final_special_rules = self._resolve_card_special_rules(
            request,
            using_gfs,
            full_seed_data,
        )
        final_shared_with = list(request.shared_with) if request.shared_with else None

        # 10) Construct Card (validates invariants)
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
            armies=final_armies,
            deployment=final_deployment,
            layout=final_layout,
            objectives=final_objectives,
            initial_priority=final_initial_priority
            or "Check the rulebook rules for it",
            special_rules=final_special_rules,
        )

        # 11) Build response DTO
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
        """Build response DTO from components."""
        name = card.name or ""
        priority = card.initial_priority or "Check the rulebook rules for it"
        final_shapes = _resolve_final_shapes(card)
        final_special_rules = card.special_rules
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
            is_replicable=request.is_replicable or False,
            table_preset=request.table_preset,
            armies=card.armies,
            layout=card.layout,
            deployment=card.deployment,
            objectives=card.objectives,
            special_rules=final_special_rules,
            shared_with=final_shared_with,
        )

    @staticmethod
    def _build_seed_config(
        request: GenerateScenarioCardRequest, table: TableSize
    ) -> dict[str, Any]:
        """Build configuration dict for deterministic seed calculation."""
        scenography_specs = request.scenography_specs or request.map_specs or []
        deployment_shapes = request.deployment_shapes or []
        objective_shapes = request.objective_shapes or []

        return {
            "mode": (
                request.mode.value
                if isinstance(request.mode, GameMode)
                else request.mode
            ),
            "table_preset": request.table_preset,
            "table_width_mm": table.width_mm,
            "table_height_mm": table.height_mm,
            "armies": request.armies,
            "deployment": request.deployment,
            "layout": request.layout,
            "objectives": request.objectives,
            "initial_priority": request.initial_priority,
            "special_rules": request.special_rules,
            "deployment_shapes": deployment_shapes,
            "objective_shapes": objective_shapes,
            "scenography_specs": scenography_specs,
        }
