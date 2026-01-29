"""CreateVariant use case.

Creates a new card derived from an existing base card:
- Only owner of base card can create variant (security)
- Variant inherits mode, table, visibility, shared_with from base
- New owner_id = actor_id
- Seed can be explicit or generated via SeedGenerator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from domain.errors import ValidationError
from domain.cards.card import Card
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
# VALIDATION HELPERS
# =============================================================================
def _validate_actor_id(actor_id: object) -> str:
    """Validate actor_id is non-empty string."""
    if actor_id is None:
        raise ValidationError("actor_id cannot be None")
    if not isinstance(actor_id, str):
        raise ValidationError("actor_id must be a string")
    stripped = actor_id.strip()
    if not stripped:
        raise ValidationError("actor_id cannot be empty or whitespace-only")
    return stripped


def _validate_base_card_id(base_card_id: object) -> str:
    """Validate base_card_id is non-empty string."""
    if base_card_id is None:
        raise ValidationError("base_card_id cannot be None")
    if not isinstance(base_card_id, str):
        raise ValidationError("base_card_id must be a string")
    stripped = base_card_id.strip()
    if not stripped:
        raise ValidationError("base_card_id cannot be empty or whitespace-only")
    return stripped


# =============================================================================
# USE CASE
# =============================================================================
class CreateVariant:
    """Use case for creating a variant of an existing card."""

    def __init__(
        self,
        repository: Any,
        id_generator: Any,
        seed_generator: Any,
        scenario_generator: Any,
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
        actor_id = _validate_actor_id(request.actor_id)
        base_card_id = _validate_base_card_id(request.base_card_id)

        # 2) Load base card
        base = self._repository.get_by_id(base_card_id)
        if base is None:
            raise Exception(f"Card not found: {base_card_id}")

        # 3) Authorization: only owner can create variant (MVP)
        if base.owner_id != actor_id:
            raise Exception("Forbidden: only owner can create variant")

        # 4) Determine seed
        if request.seed is None:
            seed = self._seed_generator.generate_seed()
        else:
            seed = request.seed

        # 5) Generate new shapes
        shapes = self._scenario_generator.generate_shapes(
            seed=seed,
            table=base.table,
            mode=base.mode,
        )

        # 6) Validate shapes with domain (MapSpec)
        try:
            map_spec = MapSpec(table=base.table, shapes=shapes)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid shapes for map: {e}")

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


# =============================================================================
# LEGACY API (for backwards compatibility)
# =============================================================================
def execute(card, new_seed: int):
    """Legacy functional API - stub that returns card unchanged.

    For full variant creation use the CreateVariant class.
    """
    return card
