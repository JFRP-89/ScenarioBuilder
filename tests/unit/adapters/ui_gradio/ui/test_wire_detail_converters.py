"""Unit tests for _detail/_converters.py — API → UI state converters.

Tests cover:
- Correct format transformation
- Edge cases (empty lists, missing keys, non-dict items)
- ID generation (each entry gets a unique id)
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# _extract_objectives_text_for_form
# ---------------------------------------------------------------------------
class TestExtractObjectivesTextForForm:
    def test_dict_with_vp(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _extract_objectives_text_for_form,
        )

        obj = {
            "objective": "Hold the hill",
            "victory_points": ["Capture flag", "Destroy bridge"],
        }
        text, vp_enabled, vp_list = _extract_objectives_text_for_form(obj)
        assert text == "Hold the hill"
        assert vp_enabled is True
        assert len(vp_list) == 2
        assert vp_list[0]["description"] == "Capture flag"
        assert "id" in vp_list[0]

    def test_dict_without_vp(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _extract_objectives_text_for_form,
        )

        text, vp_enabled, vp_list = _extract_objectives_text_for_form(
            {"objective": "Simple"}
        )
        assert text == "Simple"
        assert vp_enabled is False
        assert vp_list == []

    def test_string_input(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _extract_objectives_text_for_form,
        )

        text, vp_enabled, vp_list = _extract_objectives_text_for_form("Just text")
        assert text == "Just text"
        assert vp_enabled is False

    def test_none_input(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _extract_objectives_text_for_form,
        )

        text, vp_enabled, vp_list = _extract_objectives_text_for_form(None)
        assert text == ""
        assert vp_enabled is False
        assert vp_list == []


# ---------------------------------------------------------------------------
# _api_special_rules_to_state
# ---------------------------------------------------------------------------
class TestApiSpecialRulesToState:
    def test_description_rule(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_special_rules_to_state,
        )

        rules = [{"name": "Rally", "description": "Units regroup"}]
        result = _api_special_rules_to_state(rules)
        assert len(result) == 1
        assert result[0]["name"] == "Rally"
        assert result[0]["rule_type"] == "description"
        assert result[0]["value"] == "Units regroup"
        assert "id" in result[0]

    def test_source_rule(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_special_rules_to_state,
        )

        rules = [{"name": "Ambush", "source": "Core p.42"}]
        result = _api_special_rules_to_state(rules)
        assert result[0]["rule_type"] == "source"
        assert result[0]["value"] == "Core p.42"

    def test_empty_list(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_special_rules_to_state,
        )

        assert _api_special_rules_to_state([]) == []

    def test_skips_non_dict_items(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_special_rules_to_state,
        )

        result = _api_special_rules_to_state(["not a dict", 42])
        assert result == []


# ---------------------------------------------------------------------------
# _api_deployment_to_state
# ---------------------------------------------------------------------------
class TestApiDeploymentToState:
    def test_rect_shape(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_deployment_to_state,
        )

        shapes = [{"type": "rect", "description": "A", "x": 0, "y": 0}]
        result = _api_deployment_to_state(shapes)
        assert len(result) == 1
        assert result[0]["form_type"] == "rectangle"
        assert "A" in result[0]["label"]
        assert "data" in result[0]

    def test_polygon_triangle(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_deployment_to_state,
        )

        shapes = [{"type": "polygon", "points": [[0, 0], [1, 0], [0, 1]]}]
        result = _api_deployment_to_state(shapes)
        assert result[0]["form_type"] == "triangle"

    def test_polygon_many_points(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_deployment_to_state,
        )

        shapes = [
            {"type": "polygon", "points": [[0, 0], [1, 0], [1, 1], [0, 1], [0.5, 0.5]]}
        ]
        result = _api_deployment_to_state(shapes)
        assert result[0]["form_type"] == "circle"

    def test_empty_list(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_deployment_to_state,
        )

        assert _api_deployment_to_state([]) == []


# ---------------------------------------------------------------------------
# _api_scenography_to_state
# ---------------------------------------------------------------------------
class TestApiScenographyToState:
    def test_circle_shape(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_scenography_to_state,
        )

        shapes = [
            {"type": "circle", "cx": 300, "cy": 400, "r": 150, "description": "Tree"}
        ]
        result = _api_scenography_to_state(shapes)
        assert len(result) == 1
        assert result[0]["type"] == "circle"
        assert "Tree" in result[0]["label"]
        assert result[0]["allow_overlap"] is False
        # allow_overlap should NOT be in data
        assert "allow_overlap" not in result[0]["data"]

    def test_allow_overlap(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_scenography_to_state,
        )

        shapes = [{"type": "rect", "allow_overlap": True}]
        result = _api_scenography_to_state(shapes)
        assert result[0]["allow_overlap"] is True

    def test_empty_list(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_scenography_to_state,
        )

        assert _api_scenography_to_state([]) == []


# ---------------------------------------------------------------------------
# _api_objectives_to_state
# ---------------------------------------------------------------------------
class TestApiObjectivesToState:
    def test_with_description(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_objectives_to_state,
        )

        shapes = [{"type": "objective_point", "cx": 600, "cy": 600, "description": "T"}]
        result = _api_objectives_to_state(shapes)
        assert len(result) == 1
        assert result[0]["cx"] == 600
        assert result[0]["cy"] == 600
        assert result[0]["description"] == "T"
        assert "id" in result[0]

    def test_without_description(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_objectives_to_state,
        )

        shapes = [{"type": "objective_point", "cx": 0, "cy": 0}]
        result = _api_objectives_to_state(shapes)
        assert "description" not in result[0]

    def test_empty_list(self):
        from adapters.ui_gradio.ui.wiring._detail._converters import (
            _api_objectives_to_state,
        )

        assert _api_objectives_to_state([]) == []


# ---------------------------------------------------------------------------
# Backward-compat: importing from wire_detail still works
# ---------------------------------------------------------------------------
class TestBackwardCompatReExports:
    def test_converter_functions_importable_from_wire_detail(self):
        from adapters.ui_gradio.ui.wiring.wire_detail import (
            _api_deployment_to_state,
            _api_objectives_to_state,
            _api_scenography_to_state,
            _api_special_rules_to_state,
            _extract_objectives_text_for_form,
        )

        assert callable(_extract_objectives_text_for_form)
        assert callable(_api_special_rules_to_state)
        assert callable(_api_deployment_to_state)
        assert callable(_api_scenography_to_state)
        assert callable(_api_objectives_to_state)
