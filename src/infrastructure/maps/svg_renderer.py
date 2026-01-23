from __future__ import annotations


class SvgRenderer:
    def render_svg(self, map_spec: dict) -> str:
        width = map_spec.get("width", 120)
        height = map_spec.get("height", 120)
        return f"<svg width='{width}' height='{height}'></svg>"
