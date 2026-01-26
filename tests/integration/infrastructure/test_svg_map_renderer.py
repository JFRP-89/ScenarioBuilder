"""RED tests for SvgMapRenderer.

Tests the SVG implementation of map rendering for the modern API.
This renderer produces SVG strings from table dimensions and shape data.
"""

from __future__ import annotations

import pytest


# =============================================================================
# BASIC CONTRACT TESTS
# =============================================================================
class TestSvgMapRendererBasicContract:
    """Tests for basic contract: returns valid SVG string."""

    def test_render_empty_shapes_returns_valid_svg(self) -> None:
        """render with empty shapes returns valid SVG container."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes: list[dict] = []

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_render_returns_non_empty_string(self) -> None:
        """render returns a non-empty string."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1100, "height_mm": 700}
        shapes = [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert
        assert isinstance(svg, str)
        assert len(svg) > 0


# =============================================================================
# SHAPE RENDERING TESTS
# =============================================================================
class TestSvgMapRendererShapeTypes:
    """Tests for rendering different shape types."""

    def test_render_draws_rect(self) -> None:
        """render with rect shape includes <rect element."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1100, "height_mm": 700}
        shapes = [{"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200}]

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert
        assert "<rect" in svg

    def test_render_draws_circle(self) -> None:
        """render with circle shape includes <circle element."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1100, "height_mm": 700}
        shapes = [{"type": "circle", "cx": 300, "cy": 300, "r": 50}]

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert
        assert "<circle" in svg

    def test_render_draws_polygon(self) -> None:
        """render with polygon shape includes <polygon element with points."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1100, "height_mm": 700}
        shapes = [
            {
                "type": "polygon",
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 100, "y": 0},
                    {"x": 50, "y": 50},
                ],
            }
        ]

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert
        assert "<polygon" in svg
        assert "points=" in svg


# =============================================================================
# MIXED SHAPES TESTS
# =============================================================================
class TestSvgMapRendererMixedShapes:
    """Tests for rendering multiple shape types together."""

    def test_render_supports_mixed_shapes(self) -> None:
        """render with mixed shapes includes all shape types."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1100, "height_mm": 700}
        shapes = [
            {"type": "rect", "x": 100, "y": 100, "width": 200, "height": 200},
            {"type": "circle", "cx": 500, "cy": 500, "r": 75},
            {
                "type": "polygon",
                "points": [
                    {"x": 800, "y": 100},
                    {"x": 900, "y": 100},
                    {"x": 850, "y": 200},
                ],
            },
        ]

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert - all shape types present
        assert "<rect" in svg
        assert "<circle" in svg
        assert "<polygon" in svg
        assert "points=" in svg

    def test_render_multiple_shapes_of_same_type(self) -> None:
        """render with multiple shapes of the same type."""
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        # Arrange
        renderer = SvgMapRenderer()
        table_mm = {"width_mm": 1100, "height_mm": 700}
        shapes = [
            {"type": "rect", "x": 100, "y": 100, "width": 50, "height": 50},
            {"type": "rect", "x": 200, "y": 200, "width": 100, "height": 100},
            {"type": "rect", "x": 400, "y": 400, "width": 75, "height": 75},
        ]

        # Act
        svg = renderer.render(table_mm=table_mm, shapes=shapes)

        # Assert - contains rect elements (count check would be fragile)
        assert svg.count("<rect") >= 3
