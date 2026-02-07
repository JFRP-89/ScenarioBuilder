"""
Unit tests for unit selector component.

This component provides reusable State and Radio components for unit conversion
across Table Configuration, Deployment Zones, Objective Points, and Scenography sections.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.ui.components import (
    build_unit_selector,
    create_unit_radio,
    create_unit_state,
)


class TestCreateUnitState:
    """Tests for create_unit_state() function."""

    def test_returns_gradio_state_component(self):
        """Should return a Gradio State component."""
        state = create_unit_state()
        assert isinstance(state, gr.State)

    def test_state_initialized_with_cm(self):
        """State should be initialized with 'cm' as default value."""
        state = create_unit_state()
        assert state.value == "cm"


class TestCreateUnitRadio:
    """Tests for create_unit_radio() function."""

    def test_returns_gradio_radio_component(self):
        """Should return a Gradio Radio component."""
        radio = create_unit_radio("test")
        assert isinstance(radio, gr.Radio)

    def test_radio_has_correct_choices(self):
        """Radio should have cm, in, ft as choices."""
        radio = create_unit_radio("test")
        # Gradio internally converts choices to tuples (value, label)
        expected_choices = [("cm", "cm"), ("in", "in"), ("ft", "ft")]
        assert radio.choices == expected_choices

    def test_radio_has_cm_as_default_value(self):
        """Radio should have 'cm' as default value."""
        radio = create_unit_radio("test")
        assert radio.value == "cm"

    def test_radio_has_correct_label(self):
        """Radio should have 'Unit' as label."""
        radio = create_unit_radio("test")
        assert radio.label == "Unit"

    def test_radio_elem_id_uses_prefix(self):
        """Radio elem_id should use the provided prefix."""
        radio = create_unit_radio("table")
        assert radio.elem_id == "table-unit"

        radio = create_unit_radio("zone")
        assert radio.elem_id == "zone-unit"

        radio = create_unit_radio("objective")
        assert radio.elem_id == "objective-unit"

        radio = create_unit_radio("scenography")
        assert radio.elem_id == "scenography-unit"


class TestBuildUnitSelector:
    """Tests for build_unit_selector() convenience function."""

    def test_returns_tuple_of_state_and_radio(self):
        """Should return a tuple of (State, Radio)."""
        result = build_unit_selector("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], gr.State)
        assert isinstance(result[1], gr.Radio)

    def test_state_and_radio_have_correct_configuration(self):
        """Both components should have correct configuration."""
        state, radio = build_unit_selector("test")

        # State should be initialized with cm
        assert state.value == "cm"

        # Radio should have correct choices, value, label, and elem_id
        expected_choices = [("cm", "cm"), ("in", "in"), ("ft", "ft")]
        assert radio.choices == expected_choices
        assert radio.value == "cm"
        assert radio.label == "Unit"
        assert radio.elem_id == "test-unit"

    def test_works_with_different_prefixes(self):
        """Should work correctly with different elem_id prefixes."""
        prefixes = ["table", "zone", "objective", "scenography"]

        for prefix in prefixes:
            state, radio = build_unit_selector(prefix)
            assert state.value == "cm"
            assert radio.elem_id == f"{prefix}-unit"


class TestComponentIntegration:
    """Integration tests to verify components work in typical usage scenarios."""

    def test_can_be_used_independently(self):
        """State and Radio can be created independently for custom layouts."""
        # Create state outside of a row
        state = create_unit_state()

        # Create radio inside a row (simulated by just creating it after)
        radio = create_unit_radio("custom")

        assert state.value == "cm"
        assert radio.elem_id == "custom-unit"

    def test_can_be_used_together(self):
        """Convenience function creates both components at once."""
        state, radio = build_unit_selector("combined")

        assert state.value == "cm"
        expected_choices = [("cm", "cm"), ("in", "in"), ("ft", "ft")]
        assert radio.choices == expected_choices
        assert radio.elem_id == "combined-unit"
