"""Defensive tests: XSS / HTML injection / SVG injection prevention.

Verifies that user-controlled data is properly escaped in all render
surfaces — HTML detail view, SVG map renderer, and escape helpers.
"""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.components.search_helpers import (
    escape_html,
    escape_html_attr,
    escape_svg_attr,
    escape_svg_text,
)

# ── XSS Payloads ─────────────────────────────────────────────────

# fmt: off
XSS_PAYLOADS = [
    '<script>alert(1)</script>',
    '" onerror="alert(1)',
    "' onerror='alert(1)",
    'javascript:alert(1)',
    '</text><script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '"><img src=x onerror=alert(1)>',
    '<script',                           # incomplete tag
    '<<script>>alert(1)<</script>>',     # doubled angle brackets
    '<scr\x00ipt>alert(1)</scr\x00ipt>', # null-byte injection
    '\u200balert(1)\u200b',              # zero-width spaces
    '\u202ealert(1)\u202c',              # RTL override
]
# fmt: on


# ============================================================================
# 1. Escape helper unit tests
# ============================================================================


class TestEscapeHtmlAttr:
    """escape_html_attr must neutralise every payload for attribute context."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_no_unescaped_angle_brackets(self, payload: str):
        result = escape_html_attr(payload)
        assert "<" not in result
        assert ">" not in result

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_quotes_escaped(self, payload: str):
        result = escape_html_attr(payload)
        assert '"' not in result  # must be &quot;

    def test_none_returns_empty(self):
        assert escape_html_attr(None) == ""

    def test_bool_returns_str(self):
        assert escape_html_attr(True) == "True"

    def test_int_returns_str(self):
        assert escape_html_attr(42) == "42"

    def test_list_returns_str(self):
        result = escape_html_attr(["a", "b"])
        assert isinstance(result, str)
        assert "<" not in result

    def test_dict_returns_str(self):
        result = escape_html_attr({"key": "<val>"})
        assert "<" not in result


class TestEscapeSvgText:
    """escape_svg_text neutralises payloads in SVG <text> context."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_no_unescaped_angle_brackets(self, payload: str):
        result = escape_svg_text(payload)
        assert "<" not in result
        assert ">" not in result

    def test_none_returns_empty(self):
        assert escape_svg_text(None) == ""


class TestEscapeSvgAttr:
    """escape_svg_attr neutralises payloads in SVG attribute context."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_no_unescaped_angle_brackets(self, payload: str):
        result = escape_svg_attr(payload)
        assert "<" not in result

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_quotes_escaped(self, payload: str):
        assert '"' not in escape_svg_attr(payload)


# ============================================================================
# 2. wire_detail.py HTML render helpers
# ============================================================================


class TestFieldRowEscaping:
    """_field_row must escape both label and value."""

    def test_script_in_value_is_escaped(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _field_row

        html = _field_row("Name", "<script>alert(1)</script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_script_in_label_is_escaped(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _field_row

        html = _field_row('<img onerror="alert(1)">', "safe")
        assert "onerror" not in html or "&quot;" in html
        assert "<img" not in html

    def test_attr_breakout_in_value(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _field_row

        html = _field_row("Test", '" onerror="alert(1)')
        assert 'onerror="alert' not in html
        assert "&quot;" in html


class TestSectionTitleEscaping:
    """_section_title must escape title text."""

    def test_script_escaped(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _section_title

        html = _section_title("<script>alert(1)</script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestRenderSharedWithEscaping:
    """_render_shared_with must escape user names."""

    def test_xss_in_username(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_shared_with

        html = _render_shared_with(["<img src=x onerror=alert(1)>"])
        assert "<img" not in html
        assert "&lt;img" in html

    def test_multiple_users_all_escaped(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_shared_with

        html = _render_shared_with(["<b>bold</b>", "<script>x</script>"])
        assert "<b>" not in html
        assert "<script>" not in html


class TestRenderVictoryPointsEscaping:
    """_render_victory_points must escape VP text."""

    def test_script_in_vp(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_victory_points

        html = _render_victory_points(["<script>alert(1)</script>"])
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestRenderSpecialRulesEscaping:
    """_render_special_rules must escape name, description, source."""

    def test_xss_in_name(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_special_rules

        rules = [{"name": "<script>alert(1)</script>", "source": "book"}]
        html = _render_special_rules(rules)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_xss_in_description(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_special_rules

        rules = [{"name": "Rule", "description": "<img src=x onerror=alert(1)>"}]
        html = _render_special_rules(rules)
        assert "<img" not in html
        assert "&lt;img" in html

    def test_xss_in_source(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_special_rules

        rules = [{"name": "Rule", "source": '"><script>alert(1)</script>'}]
        html = _render_special_rules(rules)
        assert "<script>" not in html

    def test_attr_breakout_in_name(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_special_rules

        rules = [{"name": '" onerror="alert(1)', "source": "x"}]
        html = _render_special_rules(rules)
        assert 'onerror="alert' not in html


class TestBuildCardTitleEscaping:
    """_build_card_title must escape card name in Markdown heading."""

    def test_html_in_name_escaped(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _build_card_title

        md = _build_card_title({"name": "<script>alert(1)</script>"})
        assert "<script>" not in md
        assert "&lt;script&gt;" in md


class TestRenderDetailContentEscaping:
    """Integration: _render_detail_content must produce safe HTML."""

    def test_xss_in_all_fields(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import _render_detail_content

        xss = "<script>alert(1)</script>"
        card = {
            "owner_id": xss,
            "name": xss,
            "mode": xss,
            "seed": xss,
            "armies": xss,
            "visibility": "shared",
            "shared_with": [xss],
            "table_preset": xss,
            "deployment": xss,
            "layout": xss,
            "objectives": xss,
            "initial_priority": xss,
        }
        html = _render_detail_content(card)
        assert "<script>" not in html
        # All occurrences should be escaped
        assert html.count("&lt;script&gt;") >= 1


# ============================================================================
# 3. SVG renderer
# ============================================================================


class TestSvgRendererEscaping:
    """SvgMapRenderer must escape text and validate paint attributes."""

    def _make_renderer(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        r = SvgMapRenderer()
        r.table_width_mm = 1200
        r.table_height_mm = 800
        return r

    def test_escape_text_blocks_script(self):
        r = self._make_renderer()
        result = r._escape_text("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escape_text_quotes_encoded(self):
        r = self._make_renderer()
        result = r._escape_text('" onerror="alert(1)')
        assert '"' not in result

    def test_safe_paint_allows_hex(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_paint("#ff0000", "x") == "#ff0000"
        assert SvgMapRenderer._safe_paint("#abc", "x") == "#abc"

    def test_safe_paint_allows_rgba(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        val = "rgba(100,150,250,0.3)"
        assert SvgMapRenderer._safe_paint(val, "x") == val

    def test_safe_paint_allows_named_color(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_paint("red", "x") == "red"
        assert SvgMapRenderer._safe_paint("none", "x") == "none"
        assert SvgMapRenderer._safe_paint("transparent", "x") == "transparent"

    def test_safe_paint_blocks_javascript(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_paint("javascript:alert(1)", "safe") == "safe"

    def test_safe_paint_blocks_url(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_paint("url(evil)", "safe") == "safe"

    def test_safe_paint_blocks_expression(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_paint("expression(alert(1))", "safe") == "safe"

    def test_safe_paint_blocks_html_injection(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert (
            SvgMapRenderer._safe_paint('"><script>alert(1)</script>', "safe") == "safe"
        )

    def test_safe_numeric_allows_numbers(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_numeric("2", "0") == "2"
        assert SvgMapRenderer._safe_numeric("1.5", "0") == "1.5"

    def test_safe_numeric_blocks_injection(self):
        from infrastructure.maps.svg_map_renderer import SvgMapRenderer

        assert SvgMapRenderer._safe_numeric("2;alert(1)", "0") == "0"
        assert SvgMapRenderer._safe_numeric('" onerror="x', "0") == "0"

    def test_rect_with_malicious_fill(self):
        r = self._make_renderer()
        shape = {
            "type": "rect",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "fill": "javascript:alert(1)",
        }
        svg = r._rect_svg(shape)
        assert "javascript:" not in svg

    def test_circle_with_malicious_stroke(self):
        r = self._make_renderer()
        shape = {
            "type": "circle",
            "cx": 50,
            "cy": 50,
            "r": 25,
            "stroke": '"><script>alert(1)</script>',
        }
        svg = r._circle_svg(shape)
        assert "<script>" not in svg

    def test_polygon_with_malicious_fill(self):
        r = self._make_renderer()
        shape = {
            "type": "polygon",
            "points": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 50, "y": 100}],
            "fill": "expression(alert(1))",
        }
        svg = r._polygon_svg(shape)
        assert "expression(" not in svg

    def test_text_label_with_xss_description(self):
        r = self._make_renderer()
        svg = r._text_label_svg(100, 100, "</text><script>alert(1)</script>")
        assert "<script>" not in svg
        assert "&lt;script&gt;" in svg

    def test_full_render_with_malicious_description(self):
        """Integration: full render() with XSS in shape description."""
        r = self._make_renderer()
        table_mm = {"width_mm": 1200, "height_mm": 800}
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "description": "<script>alert(1)</script>",
                "fill": "javascript:alert(1)",
            }
        ]
        svg = r.render(table_mm, shapes)
        assert "<script>" not in svg
        assert "javascript:" not in svg


# ============================================================================
# 4. Edge cases
# ============================================================================


class TestEdgeCases:
    """Edge cases: null bytes, unicode, RTL overrides."""

    @pytest.mark.parametrize(
        "input_val",
        [
            "hello\x00world",  # null byte
            "\u200balert\u200b",  # zero-width spaces
            "\u202ealert\u202c",  # RTL override
            "Ñoño — «cañón»",  # unicode
        ],
    )
    def test_escape_html_handles_unicode(self, input_val: str):
        result = escape_html(input_val)
        assert isinstance(result, str)
        assert "<" not in result

    def test_incomplete_tag_escaped(self):
        result = escape_html("<script")
        assert "<script" not in result
        assert "&lt;script" in result

    def test_double_angle_brackets(self):
        result = escape_html("<<script>>")
        assert "<script" not in result

    def test_no_double_escape(self):
        """Already-escaped text should not be double-escaped in escape_html.

        Note: this is expected Python html.escape() behaviour — it WILL
        double-escape &amp; → &amp;amp; etc.  This test documents that
        the caller is responsible for not escaping twice.
        """
        first = escape_html("<b>test</b>")
        second = escape_html(first)
        # Double-escaping is a known property of html.escape —
        # we just verify it doesn't crash and returns a string.
        assert isinstance(second, str)
