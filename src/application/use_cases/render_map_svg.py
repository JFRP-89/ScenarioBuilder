"""RenderMapSvg use case.

Renders a Card's map to SVG format:
- Delegates rendering to a renderer port (does NOT render directly)
- Security: actor must be able to read the card (anti-IDOR)
- Returns SVG string
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# Legacy import for backwards compatibility
from application.ports.map_renderer import MapRenderer
from application.use_cases._validation import validate_actor_id, validate_card_id


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
        repository: Any,
        renderer: Any,
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

        # 2) Load card
        card = self._repository.get_by_id(card_id)
        if card is None:
            raise Exception(f"Card not found: {card_id}")

        # 3) Authorization: actor must be able to read card (anti-IDOR)
        if not card.can_user_read(actor_id):
            raise Exception("Forbidden: access denied")

        # 4) Prepare data for renderer
        table_mm = {
            "width_mm": card.table.width_mm,
            "height_mm": card.table.height_mm,
        }
        shapes = card.map_spec.shapes

        # 5) Delegate rendering to renderer port
        svg = self._renderer.render(table_mm=table_mm, shapes=shapes)

        # 6) Return response
        return RenderMapSvgResponse(svg=svg)


# =============================================================================
# LEGACY API (for backwards compatibility)
# =============================================================================
def execute(renderer: MapRenderer, map_spec: dict) -> str:
    """Legacy functional API - delegates to renderer directly."""
    svg: str = renderer.render_svg(map_spec)
    return svg
