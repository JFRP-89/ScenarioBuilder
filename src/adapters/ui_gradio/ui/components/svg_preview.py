"""SVG preview component for scenario map visualization.

Provides a reusable Gradio HTML component that renders SVG maps
from generated card data. Can be used in the main form (after
generating a card) or in a home screen to preview existing scenarios.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from infrastructure.maps.svg_map_renderer import SvgMapRenderer

_renderer = SvgMapRenderer()

# Default placeholder shown before any card is generated
_PLACEHOLDER_HTML = (
    '<div style="display:flex;align-items:center;justify-content:center;'
    "height:200px;border:2px dashed #ccc;border-radius:8px;"
    'color:#999;font-size:14px;">'
    "SVG preview will appear here after generating a card."
    "</div>"
)


def build_svg_preview(
    elem_id_prefix: str = "svg-preview",
    label: str = "Map Preview",
) -> gr.HTML:
    """Build an SVG preview component.

    Args:
        elem_id_prefix: Prefix for the Gradio elem_id.
        label: Label displayed above the preview area.

    Returns:
        gr.HTML component to display SVG content.
    """
    return gr.HTML(
        value=_PLACEHOLDER_HTML,
        label=label,
        elem_id=f"{elem_id_prefix}",
    )


def render_svg_from_card(card_data: dict[str, Any]) -> str:
    """Render an SVG string from a generated card's JSON data.

    Extracts table_mm and shapes from the card data and produces
    the SVG markup using SvgMapRenderer.

    Args:
        card_data: The generated card dictionary (as returned by the API).
                   Expected keys: "table_mm" (with width_mm, height_mm)
                   and optionally "shapes" (list of shape dicts).

    Returns:
        SVG markup string wrapped in a centered container,
        or the placeholder HTML if data is insufficient.
    """
    if not card_data or not isinstance(card_data, dict):
        return _PLACEHOLDER_HTML

    if "status" in card_data and card_data.get("status") == "error":
        return _PLACEHOLDER_HTML

    table_mm = card_data.get("table_mm")
    if not table_mm or not isinstance(table_mm, dict):
        return _PLACEHOLDER_HTML

    width_mm = table_mm.get("width_mm")
    height_mm = table_mm.get("height_mm")
    if not width_mm or not height_mm:
        return _PLACEHOLDER_HTML

    # Extract and flatten shapes
    shapes_data = card_data.get("shapes", [])
    shapes: list[dict[str, Any]] = []

    if isinstance(shapes_data, dict):
        # New format: shapes is a dict with subcategories
        deployment = shapes_data.get("deployment_shapes", [])
        if isinstance(deployment, list):
            shapes.extend(deployment)

        objectives = shapes_data.get("objective_shapes", [])
        if isinstance(objectives, list):
            shapes.extend(objectives)

        scenography = shapes_data.get("scenography_specs", [])
        if isinstance(scenography, list):
            shapes.extend(scenography)
    elif isinstance(shapes_data, list):
        # Legacy format: shapes is already a flat list
        shapes = shapes_data

    svg_content = _renderer.render(
        table_mm={"width_mm": int(width_mm), "height_mm": int(height_mm)},
        shapes=shapes,
    )

    # Wrap SVG in a responsive, centered container
    return (
        '<div style="display:flex;justify-content:center;align-items:center;'
        "padding:16px;background:#fafafa;border:1px solid #e0e0e0;"
        'border-radius:8px;overflow:auto;">'
        f"{svg_content}"
        "</div>"
    )
