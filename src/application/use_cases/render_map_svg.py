from __future__ import annotations

from src.application.ports.map_renderer import MapRenderer


def execute(renderer: MapRenderer, map_spec: dict) -> str:
    return renderer.render_svg(map_spec)
