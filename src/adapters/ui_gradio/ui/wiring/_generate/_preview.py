"""Preview-and-render helper for the generate button."""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.services.generate import handle_preview
from adapters.ui_gradio.ui.components.svg_preview import render_svg_from_card


def _filter_internal_fields(preview_data: dict[str, Any]) -> dict[str, Any]:
    """Filter internal fields from preview data for display.

    Internal fields are:
    - Fields prefixed with _ (_payload, _actor_id) - needed for submission only
    - is_replicable - configuration flag, not part of scenario data visible to user

    These fields are kept in full preview data for submission but hidden from JSON display.
    """
    return {
        k: v
        for k, v in preview_data.items()
        if not k.startswith("_") and k != "is_replicable"
    }


def preview_and_render(*args: Any) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Validate form, build preview card, and render SVG locally.

    Pure delegation — no Gradio wiring, easy to unit-test.

    Returns:
        Tuple of (filtered_preview_for_display, svg_html, full_preview_data).
        - filtered_preview_for_display: preview without internal fields (for JSON display)
        - svg_html: rendered SVG
        - full_preview_data: complete preview with _payload and _actor_id (for submission)
    """
    preview_data = handle_preview(*args)
    svg_html = render_svg_from_card(preview_data)
    # Filter internal fields before displaying to user
    display_data = _filter_internal_fields(preview_data)
    return display_data, svg_html, preview_data
