from __future__ import annotations

from typing import Protocol


class MapRenderer(Protocol):
    def render_svg(self, map_spec: dict) -> str: ...
