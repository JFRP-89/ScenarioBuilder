"""Unit tests for the tactical overlay module (_overlay.py).

Tests cover:
- ``format_dimension`` utility (cm, in, ft conversions)
- ``overlay_defs`` (SVG marker definitions)
- ``overlay_style_full`` (CSS class rules)
- ``layer_overlay`` (full overlay layer generation)
"""

from __future__ import annotations

import pytest

from infrastructure.maps._renderer._overlay import (
    format_dimension,
    layer_overlay,
    overlay_defs,
    overlay_style_full,
)


# =============================================================================
# format_dimension
# =============================================================================
class TestFormatDimension:
    """Test dimension formatting for different unit systems."""

    # -- cm (default) --
    def test_cm_standard_120(self) -> None:
        assert format_dimension(1200, "cm") == "120 cm"

    def test_cm_massive_180(self) -> None:
        assert format_dimension(1800, "cm") == "180 cm"

    def test_cm_minimum_60(self) -> None:
        assert format_dimension(600, "cm") == "60 cm"

    def test_cm_maximum_300(self) -> None:
        assert format_dimension(3000, "cm") == "300 cm"

    def test_cm_is_default(self) -> None:
        assert format_dimension(1200) == "120 cm"

    def test_cm_unknown_unit_falls_back(self) -> None:
        assert format_dimension(1200, "meters") == "120 cm"

    # -- inches (1 in = 2.5 cm = 25 mm) --
    def test_in_standard_48(self) -> None:
        # 1200 mm = 120 cm = 48 in
        assert format_dimension(1200, "in") == '48"'

    def test_in_massive_72(self) -> None:
        # 1800 mm = 180 cm = 72 in
        assert format_dimension(1800, "in") == '72"'

    def test_in_fractional(self) -> None:
        # 750 mm = 75 cm = 30 in (exact)
        assert format_dimension(750, "in") == '30"'

    def test_in_non_integer(self) -> None:
        # 700 mm = 70 cm = 28 in (exact)
        assert format_dimension(700, "in") == '28"'

    def test_in_with_decimal(self) -> None:
        # 630 mm = 63 cm = 25.2 in → shows one decimal
        assert format_dimension(630, "in") == '25.2"'

    # -- feet (1 ft = 30 cm = 300 mm) --
    def test_ft_standard_4(self) -> None:
        # 1200 mm = 120 cm = 4 ft
        assert format_dimension(1200, "ft") == "4 ft"

    def test_ft_massive_6(self) -> None:
        # 1800 mm = 180 cm = 6 ft
        assert format_dimension(1800, "ft") == "6 ft"

    def test_ft_fractional(self) -> None:
        # 900 mm = 90 cm = 3 ft
        assert format_dimension(900, "ft") == "3 ft"

    def test_ft_with_decimal(self) -> None:
        # 1050 mm = 105 cm = 3.5 ft
        assert format_dimension(1050, "ft") == "3.5 ft"


# =============================================================================
# overlay_defs
# =============================================================================
class TestOverlayDefs:
    """Test that overlay_defs produces valid SVG marker and filter defs."""

    def test_contains_arrow_end_marker(self) -> None:
        defs = overlay_defs()
        assert 'id="sb-dim-arrow-end"' in defs

    def test_contains_arrow_start_marker(self) -> None:
        defs = overlay_defs()
        assert 'id="sb-dim-arrow-start"' in defs

    def test_contains_compass_arrow_marker(self) -> None:
        defs = overlay_defs()
        assert 'id="sb-compass-arrow"' in defs

    def test_contains_dim_glow_filter(self) -> None:
        defs = overlay_defs()
        assert 'id="sb-dim-glow"' in defs

    def test_is_pure_svg(self) -> None:
        defs = overlay_defs()
        assert "<script" not in defs
        assert "javascript" not in defs


# =============================================================================
# overlay_style_full
# =============================================================================
class TestOverlayStyleFull:
    """Test CSS class definitions for overlay elements."""

    def test_contains_dim_line_class(self) -> None:
        style = overlay_style_full()
        assert ".sb-dim-line" in style

    def test_contains_dim_label_bg_class(self) -> None:
        style = overlay_style_full()
        assert ".sb-dim-label-bg" in style

    def test_contains_dim_label_text_class(self) -> None:
        style = overlay_style_full()
        assert ".sb-dim-label-text" in style

    def test_contains_compass_line_class(self) -> None:
        style = overlay_style_full()
        assert ".sb-compass-line" in style

    def test_contains_compass_text_class(self) -> None:
        style = overlay_style_full()
        assert ".sb-compass-text" in style

    def test_thumb_hides_overlay(self) -> None:
        style = overlay_style_full()
        assert ".sbmap-thumb .sb-overlay" in style
        assert "display: none" in style


# =============================================================================
# layer_overlay
# =============================================================================
class TestLayerOverlay:
    """Test SVG overlay layer generation."""

    @pytest.fixture()
    def standard_overlay(self) -> str:
        return layer_overlay(1200, 1200, 96.0, "cm")

    @pytest.fixture()
    def massive_overlay(self) -> str:
        return layer_overlay(1800, 1200, 144.0, "cm")

    # -- structure --
    def test_has_layer_id(self, standard_overlay: str) -> None:
        assert 'id="layer-overlay"' in standard_overlay

    def test_has_overlay_class(self, standard_overlay: str) -> None:
        assert 'class="sb-overlay"' in standard_overlay

    def test_opens_and_closes_g(self, standard_overlay: str) -> None:
        assert standard_overlay.startswith("<g ")
        assert standard_overlay.endswith("</g>")

    # -- south dimension (width) --
    def test_south_dimension_line_present(self, standard_overlay: str) -> None:
        assert 'marker-end="url(#sb-dim-arrow-end)"' in standard_overlay

    def test_south_dimension_label_cm(self, standard_overlay: str) -> None:
        assert "120 cm" in standard_overlay

    def test_south_dimension_tick_marks(self, standard_overlay: str) -> None:
        assert 'class="sb-dim-tick"' in standard_overlay

    # -- east dimension (height) --
    def test_east_dimension_line_present(self, standard_overlay: str) -> None:
        # Vertical dimension line
        assert 'marker-start="url(#sb-dim-arrow-start)"' in standard_overlay

    def test_east_dimension_label_cm(self, standard_overlay: str) -> None:
        # Both width and height are 1200 for standard → "120 cm" appears twice
        assert standard_overlay.count("120 cm") == 2

    def test_east_label_rotated(self, standard_overlay: str) -> None:
        assert "rotate(-90" in standard_overlay

    # -- compass --
    def test_compass_n_label(self, standard_overlay: str) -> None:
        assert ">N<" in standard_overlay

    def test_compass_s_label(self, standard_overlay: str) -> None:
        assert ">S<" in standard_overlay

    def test_compass_line_class(self, standard_overlay: str) -> None:
        assert 'class="sb-compass-line"' in standard_overlay

    def test_compass_max_length_300mm(self) -> None:
        """Compass arrow should be at most 300 mm (30 cm) long."""
        import re

        overlay = layer_overlay(1200, 1200, 96.0, "cm")
        # Extract compass line from the SVG
        re.search(
            r'class="sb-compass-line".*?'
            r'y1="([^"]+)".*?y2="([^"]+)"'
            r'|y1="([^"]+)".*?y2="([^"]+)".*?class="sb-compass-line"',
            overlay,
        )
        # Try parsing from the line element directly
        lines = re.findall(r'<line[^>]+class="sb-compass-line"[^>]*/>', overlay)
        assert len(lines) == 1, f"Expected 1 compass line, got {len(lines)}"
        m_y1 = re.search(r'y1="([^"]+)"', lines[0])
        m_y2 = re.search(r'y2="([^"]+)"', lines[0])
        assert m_y1 is not None and m_y2 is not None
        y1 = float(m_y1.group(1))
        y2 = float(m_y2.group(1))
        length = abs(y1 - y2)
        assert length <= 300 + 1, f"Compass length {length} exceeds 300mm"

    def test_compass_inside_map_bounds(self) -> None:
        """Compass must be inside the map area (SW of NE corner)."""
        import re

        overlay = layer_overlay(1200, 1200, 96.0, "cm")
        compass_lines = re.findall(r'<line[^>]+class="sb-compass-line"[^>]*/>', overlay)
        assert len(compass_lines) == 1
        m_x = re.search(r'x1="([^"]+)"', compass_lines[0])
        m_y1 = re.search(r'y1="([^"]+)"', compass_lines[0])
        m_y2 = re.search(r'y2="([^"]+)"', compass_lines[0])
        assert m_x is not None and m_y1 is not None and m_y2 is not None
        compass_x = float(m_x.group(1))
        y1 = float(m_y1.group(1))
        y2 = float(m_y2.group(1))
        # x must be inside map width
        assert 0 < compass_x < 1200, f"Compass x={compass_x} outside map"
        # Both y endpoints must be inside map height
        assert min(y1, y2) >= 0, f"Compass top y={min(y1, y2)} above map"
        assert max(y1, y2) <= 1200, f"Compass bottom y={max(y1, y2)} below map"

    # -- unit variants --
    def test_inches_format(self) -> None:
        overlay = layer_overlay(1200, 1200, 96.0, "in")
        assert '48"' in overlay

    def test_feet_format(self) -> None:
        overlay = layer_overlay(1200, 1200, 96.0, "ft")
        assert "4 ft" in overlay

    # -- massive table (different width/height) --
    def test_massive_width_label(self, massive_overlay: str) -> None:
        assert "180 cm" in massive_overlay

    def test_massive_height_label(self, massive_overlay: str) -> None:
        assert "120 cm" in massive_overlay

    # -- is pure SVG --
    def test_no_script_elements(self, standard_overlay: str) -> None:
        assert "<script" not in standard_overlay
        assert "javascript" not in standard_overlay


# =============================================================================
# Integration: SvgMapRenderer with overlay
# =============================================================================
class TestRendererOverlayIntegration:
    """Test that SvgMapRenderer correctly includes the overlay layer."""

    @pytest.fixture()
    def renderer(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        return SvgMapRenderer()

    def test_full_mode_includes_overlay(self, renderer) -> None:
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="full")
        assert 'id="layer-overlay"' in svg
        assert "120 cm" in svg
        assert ">N<" in svg

    def test_thumb_mode_excludes_overlay(self, renderer) -> None:
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="thumb")
        assert 'id="layer-overlay"' not in svg

    def test_full_mode_expanded_viewbox(self, renderer) -> None:
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="full")
        # viewBox should have negative offset (expanded margin)
        assert 'viewBox="-' in svg

    def test_thumb_mode_zero_margin_viewbox(self, renderer) -> None:
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="thumb")
        # viewBox should not have significant negative offset (no margin)
        # With margin=0.0 the viewBox is "-0.0 -0.0 1200.0 1200.0"
        assert "1200.0" in svg
        # Overlay layer NOT present in thumb mode
        assert 'id="layer-overlay"' not in svg

    def test_display_units_in_forwarded(self, renderer) -> None:
        table_mm = {"width_mm": 1800, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="full", display_units="in")
        assert '72"' in svg  # width in inches
        assert '48"' in svg  # height in inches

    def test_display_units_ft(self, renderer) -> None:
        table_mm = {"width_mm": 1800, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="full", display_units="ft")
        assert "6 ft" in svg
        assert "4 ft" in svg

    def test_overlay_defs_in_full_svg(self, renderer) -> None:
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        svg = renderer.render(table_mm, [], render_mode="full")
        assert 'id="sb-dim-arrow-end"' in svg
        assert 'id="sb-compass-arrow"' in svg

    def test_overlay_does_not_change_map_shapes(self, renderer) -> None:
        """Map shapes should still render at their original coordinates."""
        table_mm = {"width_mm": 1200, "height_mm": 1200}
        shapes = [
            {
                "type": "rect",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 200,
                "description": "Test Zone",
            }
        ]
        svg = renderer.render(table_mm, shapes, render_mode="full")
        # Shape coordinates unchanged
        assert 'x="100"' in svg
        assert 'y="100"' in svg
        assert 'width="200"' in svg
        assert 'height="200"' in svg
        # Overlay present too
        assert "120 cm" in svg
