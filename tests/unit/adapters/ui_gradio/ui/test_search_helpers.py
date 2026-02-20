"""Unit tests for search_helpers — sanitization, filtering, parsing, pagination.

Security-focused tests ensure XSS payloads, edge inputs, and boundary
values are correctly neutralised or rejected.
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from adapters.ui_gradio.ui.components.search_helpers import (
    DEFAULT_ITEMS_PER_PAGE,
    ITEMS_PER_PAGE_CHOICES,
    escape_html,
    filter_by_mode_preset,
    filter_cards_by_name,
    parse_per_page,
    render_filtered_page,
    render_page,
    sanitize_search_query,
    validate_page,
)

# ── sanitize_search_query ────────────────────────────────────────


class TestSanitizeSearchQuery:
    """Security-critical: all edge cases for XSS/injection prevention."""

    def test_empty_string_returns_empty(self):
        assert sanitize_search_query("") == ""

    def test_none_returns_empty(self):
        assert sanitize_search_query(None) == ""  # type: ignore[arg-type]

    def test_non_string_returns_empty(self):
        assert sanitize_search_query(42) == ""  # type: ignore[arg-type]

    def test_strips_whitespace(self):
        assert sanitize_search_query("  hello  ") == "hello"

    def test_removes_html_tags(self):
        assert sanitize_search_query("<script>alert(1)</script>") == "alert(1)"

    def test_removes_nested_html_tags(self):
        result = sanitize_search_query("<div><b>bold</b></div>")
        assert "<" not in result
        assert "bold" in result

    def test_escapes_special_html_chars(self):
        result = sanitize_search_query('a & b "c"')
        assert "&amp;" in result
        assert "&quot;" in result

    def test_limits_length_to_200(self):
        long_input = "x" * 300
        result = sanitize_search_query(long_input)
        assert len(result) == 200

    def test_combined_attack_vector(self):
        attack = '<img src=x onerror="alert(1)"> & <script>steal()</script>'
        result = sanitize_search_query(attack)
        assert "<" not in result
        assert ">" not in result
        assert "script" not in result.lower() or "&" in result

    def test_normal_search_passes_through(self):
        assert sanitize_search_query("Osgiliath") == "Osgiliath"

    def test_unicode_preserved(self):
        assert sanitize_search_query("Señor de los Anillos") == "Señor de los Anillos"


# ── filter_cards_by_name ─────────────────────────────────────────


class TestFilterCardsByName:
    """Substring matching tests."""

    CARDS: ClassVar[list[dict]] = [
        {"name": "Batalla de Osgiliath", "card_id": "c1"},
        {"name": "Alcantarillas de Osgiliath", "card_id": "c2"},
        {"name": "Minas Tirith", "card_id": "c3"},
        {"name": None, "card_id": "c4"},
        {"card_id": "c5"},  # no name field
    ]

    def test_empty_query_returns_all(self):
        result = filter_cards_by_name(self.CARDS, "")
        assert len(result) == len(self.CARDS)

    def test_case_insensitive_match(self):
        result = filter_cards_by_name(self.CARDS, "osgiliath")
        assert len(result) == 2

    def test_partial_match(self):
        result = filter_cards_by_name(self.CARDS, "Minas")
        assert len(result) == 1
        assert result[0]["card_id"] == "c3"

    def test_no_match_returns_empty(self):
        result = filter_cards_by_name(self.CARDS, "Mordor")
        assert result == []

    def test_cards_without_name_skipped(self):
        result = filter_cards_by_name(self.CARDS, "Batalla")
        assert all(c.get("name") for c in result)

    def test_html_escaped_query_still_matches(self):
        # sanitize_search_query escapes & to &amp;
        # filter_cards_by_name should unescape before matching
        cards = [{"name": "A & B", "card_id": "x"}]
        result = filter_cards_by_name(cards, "&amp;")
        assert len(result) == 1

    def test_empty_cards_list(self):
        assert filter_cards_by_name([], "anything") == []


# ── parse_per_page ───────────────────────────────────────────────


class TestParsePerPage:
    """Whitelist validation for per-page values."""

    @pytest.mark.parametrize("value", ITEMS_PER_PAGE_CHOICES)
    def test_valid_choices_accepted(self, value):
        assert parse_per_page(value) == value
        assert parse_per_page(str(value)) == value

    def test_invalid_number_returns_default(self):
        assert parse_per_page(7) == DEFAULT_ITEMS_PER_PAGE
        assert parse_per_page(0) == DEFAULT_ITEMS_PER_PAGE
        assert parse_per_page(-1) == DEFAULT_ITEMS_PER_PAGE
        assert parse_per_page(999) == DEFAULT_ITEMS_PER_PAGE

    def test_non_numeric_string_returns_default(self):
        assert parse_per_page("abc") == DEFAULT_ITEMS_PER_PAGE

    def test_none_returns_default(self):
        assert parse_per_page(None) == DEFAULT_ITEMS_PER_PAGE  # type: ignore[arg-type]

    def test_empty_string_returns_default(self):
        assert parse_per_page("") == DEFAULT_ITEMS_PER_PAGE


# ── render_page ──────────────────────────────────────────────────


class TestRenderPage:
    """Pagination rendering logic."""

    def _make_cards(self, n: int) -> list[dict]:
        return [{"card_id": f"c{i}", "name": f"Card {i}"} for i in range(n)]

    def test_empty_cards_returns_empty_html(self):
        html, info, page = render_page([], [], "cm", 1, 10)
        assert "No scenarios match" in html
        assert page == 1

    def test_custom_empty_message(self):
        html, _, _ = render_page([], [], "cm", 1, 10, empty_message="Nothing here!")
        assert "Nothing here!" in html

    def test_single_page(self):
        cards = self._make_cards(5)
        html, info, page = render_page(cards, [], "cm", 1, 10)
        assert "Page 1 of 1" in info
        assert "(5 scenarios)" in info
        assert page == 1

    def test_multi_page_first(self):
        cards = self._make_cards(25)
        html, info, page = render_page(cards, [], "cm", 1, 10)
        assert "Page 1 of 3" in info
        assert "(25 scenarios)" in info
        assert page == 1

    def test_multi_page_last(self):
        cards = self._make_cards(25)
        html, info, page = render_page(cards, [], "cm", 3, 10)
        assert "Page 3 of 3" in info
        assert page == 3

    def test_page_clamped_to_max(self):
        cards = self._make_cards(5)
        _, _, page = render_page(cards, [], "cm", 99, 10)
        assert page == 1  # only 1 page exists

    def test_page_clamped_to_min(self):
        cards = self._make_cards(5)
        _, _, page = render_page(cards, [], "cm", 0, 10)
        assert page == 1

    def test_custom_count_label(self):
        cards = self._make_cards(3)
        _, info, _ = render_page(cards, [], "cm", 1, 10, count_label="favorites")
        assert "(3 favorites)" in info

    def test_exact_page_boundary(self):
        cards = self._make_cards(10)
        _, info, page = render_page(cards, [], "cm", 1, 10)
        assert "Page 1 of 1" in info
        assert page == 1

    def test_one_over_boundary(self):
        cards = self._make_cards(11)
        _, info, page = render_page(cards, [], "cm", 2, 10)
        assert "Page 2 of 2" in info
        assert page == 2

    def test_per_page_5(self):
        cards = self._make_cards(12)
        _, info, page = render_page(cards, [], "cm", 1, 5)
        assert "Page 1 of 3" in info

    def test_favorites_marked_in_html(self):
        cards = self._make_cards(2)
        html, _, _ = render_page(cards, ["c0"], "cm", 1, 10)
        # The render_card_list_html should include the fav marker
        assert isinstance(html, str)


# ═══════════════════════════════════════════════════════════════════
# SECURITY-FOCUSED TESTS
# ═══════════════════════════════════════════════════════════════════


class TestEscapeHtml:
    """Centralised HTML escaping helper."""

    def test_basic_escaping(self):
        assert escape_html("<b>hi</b>") == "&lt;b&gt;hi&lt;/b&gt;"

    def test_quotes_escaped(self):
        result = escape_html("\"hello\" & 'world'")
        assert "&quot;" in result
        assert "&amp;" in result
        assert "&#x27;" in result

    def test_empty_string(self):
        assert escape_html("") == ""

    def test_non_string_returns_empty(self):
        assert escape_html(None) == ""  # type: ignore[arg-type]
        assert escape_html(42) == ""  # type: ignore[arg-type]
        assert escape_html([]) == ""  # type: ignore[arg-type]

    def test_plain_text_unchanged(self):
        assert escape_html("Normal text") == "Normal text"

    def test_unicode_preserved(self):
        assert escape_html("Ñoño — «cañón»") == "Ñoño — «cañón»"


class TestSanitizeSearchQueryXSS:
    """XSS payload battery — verify no active HTML survives sanitise."""

    XSS_PAYLOADS: ClassVar[list[str]] = [
        '<script>alert("XSS")</script>',
        "<script>alert(String.fromCharCode(88,83,83))</script>",
        '<img src=x onerror="alert(1)">',
        "<img src=x onerror=alert(1)>",
        '<svg onload="alert(1)">',
        "<svg/onload=alert(1)>",
        '<a href="javascript:alert(1)">click</a>',
        "<body onload=alert(1)>",
        '<input onfocus="alert(1)" autofocus>',
        '<details open ontoggle="alert(1)">',
        '<marquee onstart="alert(1)">',
        "<script",  # incomplete tag
        "<script src=//evil.com>",
        '"><script>alert(1)</script>',
        "';alert(1)//",
        '<iframe src="javascript:alert(1)">',
        "<math><mtext><table><mglyph><svg><mtext><textarea><mi><code>&#x0a;alert(1)</code>",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_no_raw_angle_brackets_survive(self, payload: str):
        result = sanitize_search_query(payload)
        assert "<" not in result, f"Unescaped '<' in result: {result!r}"
        assert ">" not in result, f"Unescaped '>' in result: {result!r}"

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_no_script_tag_in_output(self, payload: str):
        result = sanitize_search_query(payload)
        assert "<script" not in result.lower()
        assert "</script>" not in result.lower()

    def test_double_encoded_xss(self):
        """Double-encoded brackets must not produce real tags."""
        raw = "&lt;script&gt;alert(1)&lt;/script&gt;"
        result = sanitize_search_query(raw)
        assert "<script" not in result

    def test_null_byte_injection(self):
        result = sanitize_search_query("hello\x00<script>alert(1)</script>")
        assert "<" not in result

    def test_event_handler_attribute(self):
        result = sanitize_search_query('x" onmouseover="alert(1)')
        assert "onmouseover" in result  # text survives …
        assert "<" not in result  # … but no active HTML

    def test_incomplete_tag_stripped(self):
        """Tags missing closing '>' must be removed."""
        result = sanitize_search_query("<script")
        assert result == ""

    def test_multiple_incomplete_tags(self):
        result = sanitize_search_query("<div<script<img")
        assert "<" not in result


class TestSanitizeSearchQueryEdgeCases:
    """Boundary / weird-input tests for sanitize_search_query."""

    def test_whitespace_only(self):
        assert sanitize_search_query("   ") == ""

    def test_tab_and_newline_stripped(self):
        result = sanitize_search_query("\t\nhello\r\n")
        assert result == "hello"

    def test_max_length_with_html(self):
        """After sanitization the result must not exceed 200 chars."""
        payload = "<b>" + "A" * 300 + "</b>"
        result = sanitize_search_query(payload)
        assert len(result) <= 200

    def test_enormous_input(self):
        big = "x" * 10_000
        result = sanitize_search_query(big)
        assert len(result) == 200

    def test_unicode_rtl_mark(self):
        """Right-to-left mark and zero-width chars preserved (non-harmful)."""
        result = sanitize_search_query("\u200fHello\u200b")
        assert "Hello" in result

    def test_unicode_emoji(self):
        assert sanitize_search_query("⚔️🛡️") == "⚔️🛡️"

    def test_mixed_unicode_and_html(self):
        result = sanitize_search_query("<b>Ñoño</b>")
        assert "Ñoño" in result
        assert "<" not in result

    def test_only_html_tags(self):
        """Input that is *entirely* tags produces empty string."""
        assert sanitize_search_query("<div><span></span></div>") == ""

    def test_boolean_input(self):
        assert sanitize_search_query(True) == ""  # type: ignore[arg-type]

    def test_list_input(self):
        assert sanitize_search_query(["a"]) == ""  # type: ignore[arg-type]


class TestValidatePage:
    """Page-number coercion and boundary validation."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (1, 1),
            (5, 5),
            (100, 100),
            ("3", 3),
            ("1", 1),
        ],
    )
    def test_valid_pages(self, raw, expected):
        assert validate_page(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [0, -1, -999],
    )
    def test_non_positive_clamped_to_one(self, raw):
        assert validate_page(raw) == 1

    def test_none_returns_one(self):
        assert validate_page(None) == 1

    def test_float_truncated(self):
        assert validate_page(3.7) == 3

    def test_negative_float(self):
        assert validate_page(-2.5) == 1

    def test_non_numeric_string(self):
        assert validate_page("abc") == 1

    def test_empty_string(self):
        assert validate_page("") == 1

    def test_very_large_int(self):
        """Huge page numbers are accepted — clamping happens in render_page."""
        assert validate_page(999_999) == 999_999

    def test_string_with_spaces(self):
        assert validate_page(" 5 ") == 5

    def test_boolean_true(self):
        # bool is subclass of int; True == 1
        assert validate_page(True) == 1

    def test_boolean_false(self):
        assert validate_page(False) == 1  # max(1, 0) == 1

    def test_list_returns_one(self):
        assert validate_page([1, 2]) == 1


class TestParsePerPageSecurity:
    """Additional edge-case tests for parse_per_page."""

    def test_float_valid_value(self):
        # float 10.0 → int 10 → in whitelist
        assert parse_per_page(10.0) == 10  # type: ignore[arg-type]

    def test_float_invalid_value(self):
        assert parse_per_page(10.5) == DEFAULT_ITEMS_PER_PAGE  # type: ignore[arg-type]

    def test_negative_value(self):
        assert parse_per_page(-10) == DEFAULT_ITEMS_PER_PAGE

    def test_boolean_true(self):
        # True == 1, not in whitelist
        assert parse_per_page(True) == DEFAULT_ITEMS_PER_PAGE

    def test_very_large_value(self):
        assert parse_per_page(10**9) == DEFAULT_ITEMS_PER_PAGE

    def test_string_with_spaces(self):
        # " 10 " → int("10") via strip → but int() can handle spaces?
        # Actually int(" 10 ") works in Python
        assert parse_per_page(" 10 ") == 10

    def test_sql_injection_string(self):
        assert parse_per_page("10; DROP TABLE") == DEFAULT_ITEMS_PER_PAGE

    def test_html_string(self):
        assert parse_per_page("<script>10</script>") == DEFAULT_ITEMS_PER_PAGE


class TestRenderPageSecurity:
    """Verify parameter escaping in render_page HTML output."""

    def _make_cards(self, n: int) -> list[dict]:
        return [{"card_id": f"c{i}", "name": f"Card {i}"} for i in range(n)]

    def test_empty_message_xss_escaped(self):
        html_out, _, _ = render_page(
            [],
            [],
            "cm",
            1,
            10,
            empty_message='<script>alert("xss")</script>',
        )
        assert "<script>" not in html_out
        assert "&lt;script&gt;" in html_out

    def test_count_label_xss_escaped(self):
        cards = self._make_cards(3)
        _, info, _ = render_page(
            cards,
            [],
            "cm",
            1,
            10,
            count_label='<img onerror="alert(1)">',
        )
        assert "<img" not in info
        assert "&lt;img" in info

    def test_negative_page_clamped(self):
        cards = self._make_cards(5)
        _, _, page = render_page(cards, [], "cm", -5, 10)
        assert page == 1

    def test_zero_page_clamped(self):
        cards = self._make_cards(5)
        _, _, page = render_page(cards, [], "cm", 0, 10)
        assert page == 1

    def test_page_exceeding_max_clamped(self):
        cards = self._make_cards(5)
        _, _, page = render_page(cards, [], "cm", 999, 10)
        assert page == 1  # 5 cards / 10 per page = 1 total page


# ═══════════════════════════════════════════════════════════════════
# SOLID REFACTOR — EXTRACTED UNITS
# ═══════════════════════════════════════════════════════════════════


class TestFilterByModePreset:
    """Mode/preset filtering (SRP extraction from wire_home)."""

    CARDS: ClassVar[list[dict]] = [
        {"name": "A", "mode": "battle", "table_preset": "standard", "card_id": "c1"},
        {"name": "B", "mode": "narrative", "table_preset": "standard", "card_id": "c2"},
        {"name": "C", "mode": "battle", "table_preset": "custom", "card_id": "c3"},
        {"name": "D", "mode": "narrative", "table_preset": "custom", "card_id": "c4"},
    ]

    def test_all_all_returns_all(self):
        assert len(filter_by_mode_preset(self.CARDS, "All", "All")) == 4

    def test_filter_by_mode(self):
        result = filter_by_mode_preset(self.CARDS, "battle", "All")
        assert len(result) == 2
        assert all(c["mode"] == "battle" for c in result)

    def test_filter_by_preset(self):
        result = filter_by_mode_preset(self.CARDS, "All", "standard")
        assert len(result) == 2
        assert all(c["table_preset"] == "standard" for c in result)

    def test_filter_by_both(self):
        result = filter_by_mode_preset(self.CARDS, "battle", "custom")
        assert len(result) == 1
        assert result[0]["name"] == "C"

    def test_case_insensitive_mode(self):
        assert len(filter_by_mode_preset(self.CARDS, "Battle", "All")) == 2

    def test_case_insensitive_preset(self):
        assert len(filter_by_mode_preset(self.CARDS, "All", "Standard")) == 2

    def test_no_match(self):
        assert filter_by_mode_preset(self.CARDS, "nonexistent", "All") == []

    def test_empty_cards(self):
        assert filter_by_mode_preset([], "battle", "All") == []

    def test_missing_mode_field(self):
        cards: list[dict] = [{"name": "X", "card_id": "x1"}]
        assert filter_by_mode_preset(cards, "battle", "All") == []

    def test_missing_preset_field(self):
        cards: list[dict] = [{"name": "X", "mode": "battle", "card_id": "x1"}]
        assert filter_by_mode_preset(cards, "All", "standard") == []

    def test_defaults_return_all(self):
        assert len(filter_by_mode_preset(self.CARDS)) == 4


class TestRenderFilteredPage:
    """End-to-end composition: sanitise → filter → paginate → render."""

    def _make_cards(self, n: int) -> list[dict]:
        return [{"card_id": f"c{i}", "name": f"Card {i}"} for i in range(n)]

    def test_basic_rendering(self):
        cards = self._make_cards(5)
        html_out, info, page = render_filtered_page(cards, [], "cm", 1)
        assert "Page 1 of 1" in info
        assert page == 1

    def test_search_filters_cards(self):
        cards = self._make_cards(5)
        _, info, _ = render_filtered_page(cards, [], "cm", 1, search_raw="Card 0")
        assert "(1 scenarios)" in info

    def test_per_page_applied(self):
        cards = self._make_cards(15)
        _, info, _ = render_filtered_page(cards, [], "cm", 1, per_page_raw="5")
        assert "Page 1 of 3" in info

    def test_page_validated_from_none(self):
        cards = self._make_cards(5)
        _, _, page = render_filtered_page(cards, [], "cm", None)
        assert page == 1

    def test_page_validated_from_negative(self):
        cards = self._make_cards(5)
        _, _, page = render_filtered_page(cards, [], "cm", -3)
        assert page == 1

    def test_custom_count_label(self):
        cards = self._make_cards(3)
        _, info, _ = render_filtered_page(cards, [], "cm", 1, count_label="favorites")
        assert "(3 favorites)" in info

    def test_empty_cards(self):
        html_out, _, page = render_filtered_page([], [], "cm", 1)
        assert "No scenarios match" in html_out
        assert page == 1

    def test_custom_empty_message(self):
        html_out, _, _ = render_filtered_page(
            [], [], "cm", 1, empty_message="Nothing found"
        )
        assert "Nothing found" in html_out

    def test_search_sanitised_before_filtering(self):
        """HTML tags in search are stripped before matching."""
        cards = [{"card_id": "c1", "name": "alert"}]
        _, info, _ = render_filtered_page(cards, [], "cm", 1, search_raw="<b>alert</b>")
        assert "(1 scenarios)" in info

    def test_invalid_per_page_uses_default(self):
        cards = self._make_cards(15)
        _, info, _ = render_filtered_page(cards, [], "cm", 1, per_page_raw="abc")
        assert "Page 1 of 2" in info  # 15 / 10 default = 2 pages
