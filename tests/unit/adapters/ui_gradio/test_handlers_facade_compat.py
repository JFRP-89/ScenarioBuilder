"""Facade compatibility tests for handlers package.

Verifies that all public symbols are importable from the old path
``adapters.ui_gradio.handlers`` after the split into sub-modules.
"""

from __future__ import annotations


class TestHandlersFacadeCompat:
    """Every public handler must be importable from the top-level package."""

    def test_table_handlers(self):
        import adapters.ui_gradio.handlers as h

        assert callable(h.on_table_preset_change)
        assert callable(h.on_table_unit_change)
        assert callable(h.update_objective_defaults)
        assert callable(h.on_zone_border_or_fill_change)

    def test_toggle_handlers(self):
        import adapters.ui_gradio.handlers as h

        assert callable(h.toggle_section)
        assert callable(h.toggle_scenography_forms)
        assert callable(h.update_shared_with_visibility)

    def test_toggle_aliases_are_same_function(self):
        import adapters.ui_gradio.handlers as h

        assert h.toggle_vp_section is h.toggle_section
        assert h.toggle_deployment_zones_section is h.toggle_section
        assert h.toggle_scenography_section is h.toggle_section
        assert h.toggle_objective_points_section is h.toggle_section
        assert h.toggle_special_rules_section is h.toggle_section

    def test_special_rules_handlers(self):
        import adapters.ui_gradio.handlers as h

        assert callable(h.add_special_rule)
        assert callable(h.remove_last_special_rule)
        assert callable(h.remove_selected_special_rule)

    def test_victory_points_handlers(self):
        import adapters.ui_gradio.handlers as h

        assert callable(h.add_victory_point)
        assert callable(h.remove_last_victory_point)
        assert callable(h.remove_selected_victory_point)
        assert callable(h.on_polygon_preset_change)

    def test_identity_with_internal_modules(self):
        import adapters.ui_gradio.handlers as h
        from adapters.ui_gradio.handlers._special_rules import (
            add_special_rule,
        )
        from adapters.ui_gradio.handlers._table import (
            on_table_preset_change,
        )
        from adapters.ui_gradio.handlers._toggles import toggle_section
        from adapters.ui_gradio.handlers._victory_points import (
            add_victory_point,
        )

        assert h.toggle_section is toggle_section
        assert h.add_special_rule is add_special_rule
        assert h.add_victory_point is add_victory_point
        assert h.on_table_preset_change is on_table_preset_change
