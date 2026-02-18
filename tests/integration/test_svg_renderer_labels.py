"""Integration tests for SvgMapRenderer label rendering & shape descriptions.

Covers uncovered branches in svg_map_renderer.py:
- _render_shape_label for rect, circle, polygon, objective_point descriptions
- render_svg legacy API wrapper
- Shape-type delegate methods (geometry, primitives)
"""

from __future__ import annotations

from infrastructure.maps.svg_map_renderer import SvgMapRenderer


# ═════════════════════════════════════════════════════════════════════════════
# Label rendering per shape type
# ═════════════════════════════════════════════════════════════════════════════
class TestRenderWithLabels:
    """Tests that render() includes text labels when shapes have descriptions."""

    def _renderer(self) -> SvgMapRenderer:
        return SvgMapRenderer()

    def _table(self) -> dict:
        return {"width_mm": 1200, "height_mm": 800}

    def test_rect_with_description_renders_label(self) -> None:
        r = self._renderer()
        shapes = [
            {
                "type": "rect",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 150,
                "description": "Forest",
            }
        ]
        svg = r.render(self._table(), shapes)
        assert "Forest" in svg
        assert "<text" in svg

    def test_circle_with_description_renders_label(self) -> None:
        r = self._renderer()
        shapes = [
            {
                "type": "circle",
                "cx": 400,
                "cy": 300,
                "r": 50,
                "description": "Lake",
            }
        ]
        svg = r.render(self._table(), shapes)
        assert "Lake" in svg

    def test_polygon_with_description_renders_label(self) -> None:
        r = self._renderer()
        shapes = [
            {
                "type": "polygon",
                "points": [
                    {"x": 500, "y": 100},
                    {"x": 600, "y": 100},
                    {"x": 550, "y": 200},
                ],
                "description": "Hill",
            }
        ]
        svg = r.render(self._table(), shapes)
        assert "Hill" in svg

    def test_objective_point_with_description_renders_label(self) -> None:
        r = self._renderer()
        shapes = [
            {
                "type": "objective_point",
                "cx": 600,
                "cy": 400,
                "r": 25,
                "description": "Primary Objective",
            }
        ]
        svg = r.render(self._table(), shapes)
        assert "Primary Objective" in svg

    def test_unknown_type_with_description_no_label(self) -> None:
        r = self._renderer()
        shapes = [{"type": "hexagon", "description": "Mystery"}]
        svg = r.render(self._table(), shapes)
        # Unknown type doesn't render shape or label
        assert "Mystery" not in svg

    def test_shape_without_description_no_label(self) -> None:
        r = self._renderer()
        shapes = [{"type": "rect", "x": 10, "y": 10, "width": 50, "height": 50}]
        svg = r.render(self._table(), shapes)
        assert "<text" not in svg


# ═════════════════════════════════════════════════════════════════════════════
# Legacy render_svg API
# ═════════════════════════════════════════════════════════════════════════════
class TestRenderSvgLegacy:
    def test_render_svg_with_width_height_keys(self) -> None:
        r = SvgMapRenderer()
        svg = r.render_svg({"width_mm": 1100, "height_mm": 700, "shapes": []})
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_render_svg_with_short_keys(self) -> None:
        r = SvgMapRenderer()
        svg = r.render_svg({"width": 900, "height": 600, "shapes": []})
        assert "<svg" in svg

    def test_render_svg_defaults(self) -> None:
        r = SvgMapRenderer()
        svg = r.render_svg({})
        assert "<svg" in svg


# ═════════════════════════════════════════════════════════════════════════════
# Delegate methods (geometry + primitive via instance)
# ═════════════════════════════════════════════════════════════════════════════
class TestRendererDelegates:
    def test_calculate_rect_center(self) -> None:
        r = SvgMapRenderer()
        cx, cy = r._calculate_rect_center(
            {"x": 100, "y": 100, "width": 200, "height": 100}
        )
        assert cx == 200
        assert cy == 150

    def test_calculate_circle_center(self) -> None:
        r = SvgMapRenderer()
        cx, cy = r._calculate_circle_center({"cx": 300, "cy": 400})
        assert (cx, cy) == (300, 400)

    def test_calculate_polygon_center(self) -> None:
        r = SvgMapRenderer()
        pts = [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 50, "y": 100}]
        cx, cy = r._calculate_polygon_center({"points": pts})
        assert cx == 50

    def test_estimate_text_width(self) -> None:
        r = SvgMapRenderer()
        w = r._estimate_text_width("Hello")
        assert w > 0

    def test_text_fits_in_bounds(self) -> None:
        r = SvgMapRenderer()
        r.table_width_mm = 1000
        r.table_height_mm = 1000
        assert r._text_fits_in_bounds("Hi", 500, 500) is True

    def test_get_position_preference_order(self) -> None:
        r = SvgMapRenderer()
        r.table_width_mm = 1200
        r.table_height_mm = 800
        positions = r._get_position_preference_order(600, 400)
        assert len(positions) == 4

    def test_find_best_objective_position(self) -> None:
        r = SvgMapRenderer()
        r.table_width_mm = 1200
        r.table_height_mm = 800
        x, y, d = r._find_best_objective_position(600, 400, "Test")
        assert d in ("up", "down", "left", "right")

    def test_svg_header(self) -> None:
        r = SvgMapRenderer()
        h = r._svg_header(100, 200)
        assert "<svg" in h

    def test_rect_svg(self) -> None:
        r = SvgMapRenderer()
        s = r._rect_svg({"x": 0, "y": 0, "width": 50, "height": 50})
        assert "<rect" in s

    def test_circle_svg(self) -> None:
        r = SvgMapRenderer()
        s = r._circle_svg({"cx": 50, "cy": 50, "r": 25})
        assert "<circle" in s

    def test_polygon_svg(self) -> None:
        r = SvgMapRenderer()
        s = r._polygon_svg(
            {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 5, "y": 10}]}
        )
        assert "<polygon" in s

    def test_objective_point_svg(self) -> None:
        r = SvgMapRenderer()
        s = r._objective_point_svg({"cx": 50, "cy": 50, "r": 25})
        assert "circle" in s.lower() or "<" in s

    def test_shape_svg_rect(self) -> None:
        r = SvgMapRenderer()
        s = r._shape_svg({"type": "rect", "x": 0, "y": 0, "width": 10, "height": 10})
        assert s is not None

    def test_shape_svg_unknown(self) -> None:
        r = SvgMapRenderer()
        s = r._shape_svg({"type": "unknown"})
        assert s is None

    def test_text_label_svg(self) -> None:
        r = SvgMapRenderer()
        s = r._text_label_svg(100, 200, "Hello")
        assert "Hello" in s
