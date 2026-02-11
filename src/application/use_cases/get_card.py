"""GetCard use case.

Retrieves a Card by ID, enforcing visibility/authz rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from application.use_cases._validation import validate_actor_id, validate_card_id


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

    def __init__(self, repository: Any) -> None:
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
        # 1) Validate actor_id
        actor_id = validate_actor_id(request.actor_id)

        # 2) Validate card_id
        card_id = validate_card_id(request.card_id)

        # 3) Fetch card from repository
        card = self._repository.get_by_id(card_id)
        if card is None:
            raise Exception(f"Card not found: {card_id}")

        # 4) Enforce read access
        if not card.can_user_read(actor_id):
            raise Exception("Forbidden: user does not have read access")

        # 5) Build response
        table_preset = self._detect_table_preset(card.table)
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

    def _detect_table_preset(self, table: Any) -> str:
        """Detect table preset based on dimensions.

        Args:
            table: TableSize instance

        Returns:
            "standard", "massive", or "custom"
        """
        # Standard is 1200x1200 mm
        if table.width_mm == 1200 and table.height_mm == 1200:
            return "standard"
        # Massive is 1800x1200 mm
        if table.width_mm == 1800 and table.height_mm == 1200:
            return "massive"
        # Everything else is custom
        return "custom"
