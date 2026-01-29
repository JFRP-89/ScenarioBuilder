from __future__ import annotations


class SvgRenderer:
    def render_svg(self, map_spec: dict) -> str:
        width = int(map_spec.get("width", 120))
        height = int(map_spec.get("height", 120))
        return f"<svg width='{width}' height='{height}'></svg>"
