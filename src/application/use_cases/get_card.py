"""GetCard use case.

Retrieves a Card by ID, enforcing visibility/authz rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from application.ports.repositories import CardRepository
from application.use_cases._validation import (
    load_card_for_read,
    validate_actor_id,
    validate_card_id,
)


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class GetCardRequest:
    """Request DTO for GetCard use case."""

    actor_id: Optional[str]
    card_id: Optional[str]


@dataclass
class GetCardResponse:
    """Response DTO for GetCard use case."""

    card_id: str
    owner_id: str
    seed: int
    mode: str
    visibility: str
    table_mm: dict[str, int]
    name: str
    table_preset: str
    shared_with: list[str] = field(default_factory=list)
    armies: Optional[str] = None
    deployment: Optional[str] = None
    layout: Optional[str] = None
    objectives: Optional[Union[str, dict[str, Any]]] = None
    initial_priority: Optional[str] = None
    special_rules: Optional[list[dict[str, Any]]] = None
    shapes: Optional[dict[str, Any]] = None


# =============================================================================
# USE CASE
# =============================================================================
class GetCard:
    """Use case for retrieving a card by ID."""

    def __init__(self, repository: CardRepository) -> None:
        self._repository = repository

    def execute(self, request: GetCardRequest) -> GetCardResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor and card IDs.

        Returns:
            Response DTO with card data.

        Raises:
            ValidationError: If actor_id or card_id is invalid.
            Exception: If card not found or access forbidden.
        """
        # 1) Validate inputs
        actor_id = validate_actor_id(request.actor_id)
        card_id = validate_card_id(request.card_id)

        # 2) Fetch card + enforce read access (anti-IDOR)
        card = load_card_for_read(self._repository, card_id, actor_id)

        # 3) Build response
        table_preset = card.table.preset_name
        shared_list = list(card.shared_with) if card.shared_with else []
        return GetCardResponse(
            card_id=card.card_id,
            owner_id=card.owner_id,
            seed=card.seed,
            mode=card.mode.value,
            visibility=card.visibility.value,
            table_mm={
                "width_mm": card.table.width_mm,
                "height_mm": card.table.height_mm,
            },
            name=card.name or "",
            table_preset=table_preset,
            shared_with=shared_list,
            armies=card.armies,
            deployment=card.deployment,
            layout=card.layout,
            objectives=card.objectives,
            initial_priority=card.initial_priority,
            special_rules=card.special_rules,
            shapes=self._extract_shapes(card),
        )

    @staticmethod
    def _extract_shapes(card: Any) -> dict[str, Any]:
        """Extract shapes dict from card's map_spec."""
        ms = getattr(card, "map_spec", None)
        if ms is None:
            return {}
        return {
            "scenography_specs": list(ms.shapes) if ms.shapes else [],
            "deployment_shapes": (
                list(ms.deployment_shapes) if ms.deployment_shapes else []
            ),
            "objective_shapes": (
                list(ms.objective_shapes) if ms.objective_shapes else []
            ),
        }
