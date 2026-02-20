"""CreateVariant use case.

Creates a new card derived from an existing base card:
- Only owner of base card can create variant (security)
- Variant inherits mode, table, visibility, shared_with from base
- New owner_id = actor_id
- Seed can be explicit or generated via SeedGenerator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from application.ports.repositories import CardRepository
from application.ports.scenario_generation import (
    IdGenerator,
    ScenarioGenerator,
    SeedGenerator,
)
from application.use_cases._validation import (
    load_card_for_write,
    validate_actor_id,
    validate_card_id,
)
from domain.cards.card import Card
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass(frozen=True)
class CreateVariantRequest:
    """Request DTO for CreateVariant use case."""

    actor_id: Optional[str]
    base_card_id: Optional[str]
    seed: Optional[int]


@dataclass(frozen=True)
class CreateVariantResponse:
    """Response DTO for CreateVariant use case."""

    card_id: str
    owner_id: str
    seed: int
    mode: str
    visibility: str


# =============================================================================
# USE CASE
# =============================================================================
class CreateVariant:
    """Use case for creating a variant of an existing card."""

    def __init__(
        self,
        repository: CardRepository,
        id_generator: IdGenerator,
        seed_generator: SeedGenerator,
        scenario_generator: ScenarioGenerator,
    ) -> None:
        self._repository = repository
        self._id_generator = id_generator
        self._seed_generator = seed_generator
        self._scenario_generator = scenario_generator

    def execute(self, request: CreateVariantRequest) -> CreateVariantResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor_id, base_card_id, and optional seed.

        Returns:
            Response DTO with new card snapshot.

        Raises:
            ValidationError: If inputs are invalid or shapes fail validation.
            Exception: If base card not found or access forbidden.
        """
        # 1) Validate inputs
        actor_id = validate_actor_id(request.actor_id)
        base_card_id = validate_card_id(request.base_card_id)

        # 2-3) Load base card + authorization (centralized anti-IDOR)
        base = load_card_for_write(self._repository, base_card_id, actor_id)

        # 4) Determine seed
        seed = (
            self._seed_generator.generate_seed()
            if request.seed is None
            else request.seed
        )

        # 5) Generate new shapes
        shapes = self._scenario_generator.generate_shapes(
            seed=seed,
            table=base.table,
            mode=base.mode,
        )

        # 5a) Capture generation metadata (if available)
        seed_attempt: int | None = getattr(
            self._scenario_generator, "last_attempt_index", None
        )
        gen_version: str | None = getattr(
            self._scenario_generator, "generator_version", None
        )

        # 5b) Enforce contract: shapes MUST be list[dict], not dict
        if not isinstance(shapes, list):
            raise ValidationError(
                f"ScenarioGenerator contract violation: generate_shapes() returned "
                f"{type(shapes).__name__}, expected list[dict]"
            )
        if shapes and not all(isinstance(s, dict) for s in shapes):
            raise ValidationError(
                "ScenarioGenerator contract violation: shapes list contains non-dict elements"
            )

        # 6) Validate shapes with domain (MapSpec)
        try:
            map_spec = MapSpec(table=base.table, shapes=shapes)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid shapes for map: {e}") from e

        # 7) Generate new card_id
        new_id = self._id_generator.generate_card_id()

        # 8) Create variant Card (inherits from base)
        new_card = Card(
            card_id=new_id,
            owner_id=actor_id,
            visibility=base.visibility,
            shared_with=base.shared_with,
            mode=base.mode,
            seed=seed,
            table=base.table,
            map_spec=map_spec,
            seed_attempt=seed_attempt,
            generator_version=gen_version,
        )

        # 9) Persist
        self._repository.save(new_card)

        # 10) Return snapshot
        return CreateVariantResponse(
            card_id=new_card.card_id,
            owner_id=new_card.owner_id,
            seed=new_card.seed,
            mode=new_card.mode.value,
            visibility=new_card.visibility.value,
        )
