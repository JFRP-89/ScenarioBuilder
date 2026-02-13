"""Unit tests for _detail/_render.py — pure HTML rendering helpers.

Tests cover:
- XSS safety (all outputs escape user data)
- Edge cases (empty inputs, missing keys)
- Correct HTML structure
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# _field_row
# ---------------------------------------------------------------------------
class TestFieldRow:
    def test_basic_rendering(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _field_row

        html = _field_row("Name", "Test Value")
        assert "Name:" in html
        assert "Test Value" in html

    def test_xss_label_and_value(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _field_row

        html = _field_row("<script>", "a]&b")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "&amp;" in html


# ---------------------------------------------------------------------------
# _section_title
# ---------------------------------------------------------------------------
class TestSectionTitle:
    def test_renders_title(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _section_title

        html = _section_title("Details")
        assert "Details" in html

    def test_escapes_html(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _section_title

        html = _section_title("<b>evil</b>")
        assert "<b>" not in html
        assert "&lt;b&gt;" in html


# ---------------------------------------------------------------------------
# _render_shared_with
# ---------------------------------------------------------------------------
class TestRenderSharedWith:
    def test_empty_list(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_shared_with

        assert _render_shared_with([]) == ""

    def test_multiple_users(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_shared_with

        html = _render_shared_with(["alice", "bob"])
        assert "alice" in html
        assert "bob" in html
        assert "Shared With" in html

    def test_xss_in_username(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_shared_with

        html = _render_shared_with(['<img onerror="x">'])
        assert "<img" not in html


# ---------------------------------------------------------------------------
# _render_victory_points
# ---------------------------------------------------------------------------
class TestRenderVictoryPoints:
    def test_empty_list(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_victory_points

        assert _render_victory_points([]) == ""

    def test_renders_items(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_victory_points

        html = _render_victory_points(["Hold bridge", "Defeat leader"])
        assert "Hold bridge" in html
        assert "Defeat leader" in html


# ---------------------------------------------------------------------------
# _render_special_rules
# ---------------------------------------------------------------------------
class TestRenderSpecialRules:
    def test_empty_rules(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_special_rules

        assert _render_special_rules([]) == ""

    def test_source_only_rule(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_special_rules

        rules = [{"name": "Ambush", "source": "Core p.42"}]
        html = _render_special_rules(rules)
        assert "Ambush" in html
        assert "Core p.42" in html

    def test_description_rule(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_special_rules

        rules = [{"name": "Rally", "description": "Units regroup"}]
        html = _render_special_rules(rules)
        assert "Rally" in html
        assert "Units regroup" in html

    def test_xss_in_rule_name(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_special_rules

        rules = [{"name": "<script>alert(1)</script>", "description": "safe"}]
        html = _render_special_rules(rules)
        assert "<script>" not in html


# ---------------------------------------------------------------------------
# _format_table_display
# ---------------------------------------------------------------------------
class TestFormatTableDisplay:
    def test_basic(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _format_table_display

        card = {
            "table_preset": "standard",
            "table_mm": {"width_mm": 1200, "height_mm": 720},
        }
        result = _format_table_display(card)
        assert "Standard" in result
        assert "120x72 cm" in result
        assert "1200x720 mm" in result

    def test_no_dimensions(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _format_table_display

        card = {"table_preset": "small"}
        result = _format_table_display(card)
        assert result == "Small"


# ---------------------------------------------------------------------------
# _extract_objectives_text
# ---------------------------------------------------------------------------
class TestExtractObjectivesText:
    def test_dict_input(self):
        from adapters.ui_gradio.ui.wiring._detail._render import (
            _extract_objectives_text,
        )

        assert _extract_objectives_text({"objective": "Hold center"}) == "Hold center"

    def test_string_input(self):
        from adapters.ui_gradio.ui.wiring._detail._render import (
            _extract_objectives_text,
        )

        assert _extract_objectives_text("Simple objective") == "Simple objective"

    def test_none_input(self):
        from adapters.ui_gradio.ui.wiring._detail._render import (
            _extract_objectives_text,
        )

        assert _extract_objectives_text(None) == "—"


# ---------------------------------------------------------------------------
# _build_card_title
# ---------------------------------------------------------------------------
class TestBuildCardTitle:
    def test_with_name(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _build_card_title

        assert _build_card_title({"name": "Battle"}) == "## Battle"

    def test_xss_in_name(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _build_card_title

        md = _build_card_title({"name": "<script>"})
        assert "<script>" not in md
        assert "&lt;script&gt;" in md

    def test_fallback_no_name(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _build_card_title

        md = _build_card_title({"mode": "matched", "seed": 42})
        assert "Matched" in md
        assert "#42" in md


# ---------------------------------------------------------------------------
# _wrap_svg
# ---------------------------------------------------------------------------
class TestWrapSvg:
    def test_wraps_svg(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _wrap_svg

        html = _wrap_svg('<svg width="100"></svg>')
        assert "display:flex" in html
        assert '<svg width="100"></svg>' in html

    def test_passthrough_non_svg(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _wrap_svg

        assert _wrap_svg("plain text") == "plain text"


# ---------------------------------------------------------------------------
# _render_detail_content (integration of all renderers)
# ---------------------------------------------------------------------------
class TestRenderDetailContent:
    def test_basic_card(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_detail_content

        card = {
            "name": "Epic Battle",
            "owner_id": "user1",
            "mode": "matched",
            "seed": 7,
            "visibility": "public",
            "table_preset": "standard",
        }
        html = _render_detail_content(card)
        assert "Epic Battle" in html
        assert "Matched" in html
        assert "user1" in html

    def test_shared_visibility(self):
        from adapters.ui_gradio.ui.wiring._detail._render import _render_detail_content

        card = {
            "name": "Shared Battle",
            "owner_id": "u",
            "mode": "casual",
            "seed": 1,
            "visibility": "shared",
            "shared_with": ["alice"],
            "table_preset": "standard",
        }
        html = _render_detail_content(card)
        assert "alice" in html
        assert "Shared With" in html


# ---------------------------------------------------------------------------
# Backward-compat: importing from wire_detail still works
# ---------------------------------------------------------------------------
class TestBackwardCompatReExports:
    def test_render_functions_importable_from_wire_detail(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _build_card_title,
            _field_row,
            _render_detail_content,
            _section_title,
            _wrap_svg,
        )

        # Just verify they're callable
        assert callable(_field_row)
        assert callable(_section_title)
        assert callable(_build_card_title)
        assert callable(_render_detail_content)
        assert callable(_wrap_svg)
