"""Preview-and-render helper for the generate button."""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.services.generate import handle_preview
from adapters.ui_gradio.ui.components.svg_preview import render_svg_from_card


def preview_and_render(*args: Any) -> tuple[dict[str, Any], str]:
    """Validate form, build preview card, and render SVG locally.

    Pure delegation — no Gradio wiring, easy to unit-test.
    """
    preview_data = handle_preview(*args)
    svg_html = render_svg_from_card(preview_data)
    return preview_data, svg_html
