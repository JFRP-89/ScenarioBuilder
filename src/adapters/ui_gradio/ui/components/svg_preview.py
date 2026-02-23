"""SVG preview component for scenario map visualization.

Provides a reusable Gradio HTML component that renders SVG maps
from generated card data. Can be used in the main form (after
generating a card) or in a home screen to preview existing scenarios.
"""

from __future__ import annotations

from typing import Any, Callable

import gradio as gr


class _RendererHolder:
    """Mutable holder for the injected SVG render function (DIP)."""

    fn: Callable[..., str] | None = None


_renderer = _RendererHolder()


def configure_renderer(
    render_fn: Callable[..., str],
) -> None:
    """Inject the SVG render function (called once at app startup).

    Args:
        render_fn: callable with signature
            ``(table_mm=dict, shapes=list[dict]) -> str``.
    """
    _renderer.fn = render_fn


# Default placeholder shown before any card is generated
_PLACEHOLDER_HTML = (
    '<div style="display:flex;align-items:center;justify-content:center;'
    "height:200px;border:2px dashed #2a3545;border-radius:14px;"
    'color:#5a7090;font-size:14px;background:#111315;">'
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


def _flatten_shapes(shapes_data: Any) -> list[dict[str, Any]]:
    """Flatten shapes from card data into a single list.

    Supports both the new dict format (with subcategories) and
    the legacy flat-list format.
    """
    if isinstance(shapes_data, list):
        return shapes_data

    if not isinstance(shapes_data, dict):
        return []

    result: list[dict[str, Any]] = []
    for key in ("deployment_shapes", "objective_shapes", "scenography_specs"):
        sub = shapes_data.get(key, [])
        if isinstance(sub, list):
            result.extend(sub)
    return result


def render_svg_from_card(
    card_data: dict[str, Any],
    render_mode: str = "full",
    display_units: str = "cm",
) -> str:
    """Render an SVG string from a generated card's JSON data.

    Extracts table_mm and shapes from the card data and produces
    the SVG markup using the injected renderer.

    Args:
        card_data: The generated card dictionary (as returned by the API).
                   Expected keys: "table_mm" (with width_mm, height_mm)
                   and optionally "shapes" (list of shape dicts).
        render_mode: ``"full"`` for detail view, ``"thumb"`` for card list.
        display_units: Unit system for dimension overlays
            (``"cm"``, ``"in"``, or ``"ft"``).

    Returns:
        SVG markup string wrapped in a centered container,
        or the placeholder HTML if data is insufficient.
    """
    if not card_data or not isinstance(card_data, dict):
        return _PLACEHOLDER_HTML

    if card_data.get("status") == "error":
        return _PLACEHOLDER_HTML

    table_mm = card_data.get("table_mm")
    if not table_mm or not isinstance(table_mm, dict):
        return _PLACEHOLDER_HTML

    width_mm = table_mm.get("width_mm")
    height_mm = table_mm.get("height_mm")
    if not width_mm or not height_mm:
        return _PLACEHOLDER_HTML

    if _renderer.fn is None:
        return _PLACEHOLDER_HTML

    shapes = _flatten_shapes(card_data.get("shapes", []))

    svg_content: str = _renderer.fn(
        table_mm={"width_mm": int(width_mm), "height_mm": int(height_mm)},
        shapes=shapes,
        render_mode=render_mode,
        display_units=display_units,
    )

    # Wrap SVG in a responsive, centered container
    return (
        '<div style="display:flex;justify-content:center;align-items:center;'
        "padding:16px;background:#111315;border:1px solid #2a3545;"
        "border-radius:14px;overflow:auto;"
        'box-shadow:0 0 20px rgba(246,212,28,.06);">'
        f"{svg_content}"
        "</div>"
    )
