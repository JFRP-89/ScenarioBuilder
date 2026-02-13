"""RenderMapSvg use case.

Renders a Card's map to SVG format:
- Delegates rendering to a renderer port (does NOT render directly)
- Security: actor must be able to read the card (anti-IDOR)
- Returns SVG string
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Legacy import for backwards compatibility
from application.ports.map_renderer import MapRenderer
from application.ports.repositories import CardRepository
from application.use_cases._validation import (
    load_card_for_read,
    validate_actor_id,
    validate_card_id,
)


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass(frozen=True)
class RenderMapSvgRequest:
    """Request DTO for RenderMapSvg use case."""

    actor_id: Optional[str]
    card_id: Optional[str]


@dataclass(frozen=True)
class RenderMapSvgResponse:
    """Response DTO for RenderMapSvg use case."""

    svg: str


# =============================================================================
# USE CASE
# =============================================================================
class RenderMapSvg:
    """Use case for rendering a card's map to SVG."""

    def __init__(
        self,
        repository: CardRepository,
        renderer: MapRenderer,
    ) -> None:
        self._repository = repository
        self._renderer = renderer

    def execute(self, request: RenderMapSvgRequest) -> RenderMapSvgResponse:
        """Execute the use case.

        Args:
            request: Request DTO with actor_id and card_id.

        Returns:
            Response DTO with SVG string.

        Raises:
            ValidationError: If inputs are invalid.
            Exception: If card not found or access forbidden.
        """
        # 1) Validate inputs
        actor_id = validate_actor_id(request.actor_id)
        card_id = validate_card_id(request.card_id)

        # 2) Load card + enforce read access (anti-IDOR)
        card = load_card_for_read(self._repository, card_id, actor_id)

        # 3) Prepare data for renderer
        table_mm = {
            "width_mm": card.table.width_mm,
            "height_mm": card.table.height_mm,
        }

        # Combine all shape categories into a single list for rendering
        all_shapes: list[dict] = []
        if card.map_spec.shapes:
            all_shapes.extend(card.map_spec.shapes)
        if card.map_spec.deployment_shapes:
            all_shapes.extend(card.map_spec.deployment_shapes)
        if card.map_spec.objective_shapes:
            all_shapes.extend(card.map_spec.objective_shapes)

        # 5) Delegate rendering to renderer port
        svg = self._renderer.render(table_mm=table_mm, shapes=all_shapes)

        # 6) Return response
        return RenderMapSvgResponse(svg=svg)


# =============================================================================
# LEGACY API (for backwards compatibility)
# =============================================================================
def execute(renderer: MapRenderer, map_spec: dict) -> str:
    """Legacy functional API - delegates to renderer directly."""
    svg: str = renderer.render_svg(map_spec)
    return svg
