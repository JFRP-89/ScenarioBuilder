"""Unit tests for the SVG preview component."""

from __future__ import annotations

import pytest
from adapters.ui_gradio.ui.components.svg_preview import (
    _PLACEHOLDER_HTML,
    build_svg_preview,
    render_svg_from_card,
)

# --- build_svg_preview ---


class TestBuildSvgPreview:
    """Tests for build_svg_preview()."""

    def test_returns_html_component(self):
        import gradio as gr

        component = build_svg_preview()
        assert isinstance(component, gr.HTML)

    def test_default_elem_id(self):
        component = build_svg_preview()
        assert component.elem_id == "svg-preview"

    def test_custom_elem_id_prefix(self):
        component = build_svg_preview(elem_id_prefix="home-preview")
        assert component.elem_id == "home-preview"

    def test_initial_value_is_placeholder(self):
        component = build_svg_preview()
        assert component.value == _PLACEHOLDER_HTML


# --- render_svg_from_card ---


class TestRenderSvgFromCard:
    """Tests for render_svg_from_card()."""

    @pytest.fixture()
    def valid_card(self) -> dict:
        return {
            "card_id": "abc-123",
            "seed": 42,
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": [
                {
                    "type": "rect",
                    "x": 0,
                    "y": 0,
                    "width": 600,
                    "height": 300,
                },
            ],
        }

    # --- happy path ---

    def test_valid_card_produces_svg(self, valid_card):
        result = render_svg_from_card(valid_card)
        assert "<svg" in result
        assert "</svg>" in result

    def test_valid_card_wrapped_in_container(self, valid_card):
        result = render_svg_from_card(valid_card)
        assert result.startswith("<div")
        assert result.endswith("</div>")

    def test_valid_card_contains_rect(self, valid_card):
        result = render_svg_from_card(valid_card)
        assert "<rect" in result

    def test_valid_card_no_shapes(self):
        card = {
            "table_mm": {"width_mm": 900, "height_mm": 600},
            "shapes": [],
        }
        result = render_svg_from_card(card)
        assert "<svg" in result
        # Should still have the table background but no shape elements
        assert "<rect" not in result or "width" in result

    def test_circle_shape(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": [{"type": "circle", "cx": 600, "cy": 600, "r": 100}],
        }
        result = render_svg_from_card(card)
        assert "<circle" in result

    def test_polygon_shape(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": [
                {
                    "type": "polygon",
                    "points": [
                        {"x": 0, "y": 0},
                        {"x": 100, "y": 0},
                        {"x": 50, "y": 100},
                    ],
                },
            ],
        }
        result = render_svg_from_card(card)
        assert "<polygon" in result

    def test_objective_point_shape(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": [{"type": "objective_point", "cx": 600, "cy": 600}],
        }
        result = render_svg_from_card(card)
        assert "<circle" in result
        assert 'fill="black"' in result

    # --- fallback to placeholder ---

    def test_none_returns_placeholder(self):
        assert render_svg_from_card(None) == _PLACEHOLDER_HTML

    def test_empty_dict_returns_placeholder(self):
        assert render_svg_from_card({}) == _PLACEHOLDER_HTML

    def test_non_dict_returns_placeholder(self):
        assert render_svg_from_card("not a dict") == _PLACEHOLDER_HTML

    def test_error_status_returns_placeholder(self):
        card = {"status": "error", "detail": "Something broke"}
        assert render_svg_from_card(card) == _PLACEHOLDER_HTML

    def test_missing_table_mm_returns_placeholder(self):
        card = {"shapes": []}
        assert render_svg_from_card(card) == _PLACEHOLDER_HTML

    def test_table_mm_not_dict_returns_placeholder(self):
        card = {"table_mm": "invalid"}
        assert render_svg_from_card(card) == _PLACEHOLDER_HTML

    def test_missing_width_mm_returns_placeholder(self):
        card = {"table_mm": {"height_mm": 1200}}
        assert render_svg_from_card(card) == _PLACEHOLDER_HTML

    def test_missing_height_mm_returns_placeholder(self):
        card = {"table_mm": {"width_mm": 1200}}
        assert render_svg_from_card(card) == _PLACEHOLDER_HTML

    def test_invalid_shapes_treated_as_empty(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": "not a list",
        }
        result = render_svg_from_card(card)
        assert "<svg" in result

    def test_shapes_key_absent_treated_as_empty(self):
        card = {"table_mm": {"width_mm": 1200, "height_mm": 1200}}
        result = render_svg_from_card(card)
        assert "<svg" in result

    # --- new format: shapes as dict with subcategories ---

    def test_shapes_as_dict_with_deployment(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": {
                "deployment_shapes": [
                    {"type": "rect", "x": 0, "y": 0, "width": 600, "height": 300}
                ],
            },
        }
        result = render_svg_from_card(card)
        assert "<svg" in result
        assert "<rect" in result

    def test_shapes_as_dict_with_objectives(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": {
                "objective_shapes": [{"type": "objective_point", "cx": 600, "cy": 600}]
            },
        }
        result = render_svg_from_card(card)
        assert "<svg" in result
        assert "<circle" in result
        assert 'fill="black"' in result

    def test_shapes_as_dict_with_scenography(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": {
                "scenography_specs": [
                    {"type": "circle", "cx": 600, "cy": 600, "r": 100}
                ]
            },
        }
        result = render_svg_from_card(card)
        assert "<svg" in result
        assert "<circle" in result

    def test_shapes_as_dict_with_all_categories(self):
        """Test the full structure from the API (deployment, objectives, scenography)."""
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": {
                "deployment_shapes": [
                    {"type": "rect", "x": 0, "y": 0, "width": 1200, "height": 300}
                ],
                "objective_shapes": [{"type": "objective_point", "cx": 600, "cy": 600}],
                "scenography_specs": [
                    {"type": "circle", "cx": 900, "cy": 900, "r": 150},
                    {
                        "type": "polygon",
                        "points": [
                            {"x": 600, "y": 300},
                            {"x": 1000, "y": 700},
                            {"x": 200, "y": 700},
                        ],
                    },
                ],
            },
        }
        result = render_svg_from_card(card)
        assert "<svg" in result
        assert "<rect" in result
        assert "<circle" in result
        assert "<polygon" in result

    def test_shapes_dict_with_empty_subcategories(self):
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": {
                "deployment_shapes": [],
                "objective_shapes": [],
                "scenography_specs": [],
            },
        }
        result = render_svg_from_card(card)
        assert "<svg" in result

    def test_shapes_dict_with_invalid_subcategory_types(self):
        """Should skip non-list subcategories."""
        card = {
            "table_mm": {"width_mm": 1200, "height_mm": 1200},
            "shapes": {
                "deployment_shapes": "not a list",
                "objective_shapes": None,
                "scenography_specs": [{"type": "circle", "cx": 600, "cy": 600, "r": 50}],
            },
        }
        result = render_svg_from_card(card)
        assert "<svg" in result
        assert "<circle" in result
