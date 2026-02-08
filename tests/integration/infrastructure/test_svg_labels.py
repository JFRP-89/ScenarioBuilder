"""Integration tests for SVG labels in SvgMapRenderer."""

from __future__ import annotations

import pytest


class TestSvgLabelsForShapes:
    """Test that labels appear correctly for shapes with descriptions."""

    @pytest.fixture()
    def renderer(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        return SvgMapRenderer()

    def test_rect_with_description_has_label(self, renderer):
        """Deployment zone (rect) with description should have centered label."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 300,
                "description": "Attacking Army",
            }
        ]
        result = renderer.render(table_mm, shapes)
        assert "<text" in result
        assert "Attacking Army" in result
        # Center should be at x=600, y=150
        assert 'x="600"' in result
        assert 'y="150"' in result

    def test_rect_without_description_has_no_label(self, renderer):
        """Rect without description should not have a label."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [{"type": "rect", "x": 0, "y": 0, "width": 1200, "height": 300}]
        result = renderer.render(table_mm, shapes)
        # Should have rect but no text element
        assert "<rect" in result
        assert "<text" not in result

    def test_circle_with_description_has_label(self, renderer):
        """Circle (scenography) with description should have centered label."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "circle",
                "cx": 600,
                "cy": 600,
                "r": 150,
                "description": "Large Rock",
            }
        ]
        result = renderer.render(table_mm, shapes)
        assert "<text" in result
        assert "Large Rock" in result
        # Center should be at cx=600, cy=600
        assert 'x="600"' in result
        assert 'y="600"' in result

    def test_polygon_with_description_has_label(self, renderer):
        """Polygon (scenography) with description should have centered label."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "polygon",
                "points": [
                    {"x": 500, "y": 300},
                    {"x": 700, "y": 300},
                    {"x": 600, "y": 500},
                ],
                "description": "Hill",
            }
        ]
        result = renderer.render(table_mm, shapes)
        assert "<text" in result
        assert "Hill" in result
        # Approximate center: x=(500+700+600)/3=600, y=(300+300+500)/3=366
        assert 'x="600"' in result
        assert 'y="366"' in result

    def test_objective_point_with_description_has_label_above(self, renderer):
        """Objective point with description should have label 50mm above."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "objective_point",
                "cx": 600,
                "cy": 600,
                "description": "Central Marker",
            }
        ]
        result = renderer.render(table_mm, shapes)
        assert "<text" in result
        assert "Central Marker" in result
        # Label should be 50mm above: y = 600 - 50 = 550
        assert 'x="600"' in result
        assert 'y="550"' in result

    def test_objective_point_without_description_has_no_label(self, renderer):
        """Objective point without description should not have a label."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [{"type": "objective_point", "cx": 600, "cy": 600}]
        result = renderer.render(table_mm, shapes)
        assert "<circle" in result
        assert "<text" not in result

    def test_multiple_shapes_with_descriptions(self, renderer):
        """Multiple shapes with descriptions should all have labels."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 300,
                "description": "North Zone",
            },
            {
                "type": "circle",
                "cx": 600,
                "cy": 600,
                "r": 100,
                "description": "Center Hill",
            },
            {
                "type": "objective_point",
                "cx": 900,
                "cy": 900,
                "description": "South Marker",
            },
        ]
        result = renderer.render(table_mm, shapes)
        # Should have 3 text elements
        assert result.count("<text") == 3
        assert "North Zone" in result
        assert "Center Hill" in result
        assert "South Marker" in result

    def test_description_with_special_characters_is_escaped(self, renderer):
        """Descriptions with HTML special characters should be escaped."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 300,
                "description": 'Army <Strong> & "Brave"',
            }
        ]
        result = renderer.render(table_mm, shapes)
        # Should escape HTML entities
        assert "&lt;Strong&gt;" in result
        assert "&amp;" in result
        assert "&quot;Brave&quot;" in result
        # Should not contain raw HTML
        assert "<Strong>" not in result

    def test_empty_description_treated_as_no_description(self, renderer):
        """Empty or whitespace-only descriptions should not produce labels."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 300,
                "description": "",
            },
            {"type": "circle", "cx": 600, "cy": 600, "r": 100, "description": "   "},
        ]
        result = renderer.render(table_mm, shapes)
        assert "<rect" in result
        assert "<circle" in result
        assert "<text" not in result
