"""Tests for pure event handlers in handlers module."""

from __future__ import annotations

from adapters.ui_gradio import handlers


class TestOnTablePresetChange:
    """Tests for on_table_preset_change handler."""

    def test_custom_preset_returns_visible_and_defaults(self):
        """Custom preset shows custom fields and returns default values."""
        table_standard = (120, 120)
        table_massive = (180, 120)

        def convert_from_cm(value, unit):
            return value

        visibility, width, height = handlers.on_table_preset_change(
            "custom", "cm", table_standard, table_massive, convert_from_cm
        )

        assert visibility["visible"] is True
        assert width == 120.0
        assert height == 120.0

    def test_standard_preset_returns_hidden_and_standard_dimensions_cm(self):
        """Standard preset returns 120x120 cm."""
        table_standard = (120, 120)
        table_massive = (180, 120)

        def convert_from_cm(value, unit):
            return value

        visibility, width, height = handlers.on_table_preset_change(
            "standard", "cm", table_standard, table_massive, convert_from_cm
        )

        assert visibility["visible"] is False
        assert width == 120.0
        assert height == 120.0

    def test_massive_preset_returns_hidden_and_massive_dimensions_cm(self):
        """Massive preset returns 180x120 cm."""
        table_standard = (120, 120)
        table_massive = (180, 120)

        def convert_from_cm(value, unit):
            return value

        visibility, width, height = handlers.on_table_preset_change(
            "massive", "cm", table_standard, table_massive, convert_from_cm
        )

        assert visibility["visible"] is False
        assert width == 180.0
        assert height == 120.0

    def test_standard_preset_converts_to_inches(self):
        """Standard preset converts cm to inches."""
        table_standard = (120, 120)
        table_massive = (180, 120)

        def convert_from_cm(value, unit):
            if unit == "in":
                return value / 2.5
            return value

        visibility, width, height = handlers.on_table_preset_change(
            "standard", "in", table_standard, table_massive, convert_from_cm
        )

        assert visibility["visible"] is False
        assert width == 48.0
        assert height == 48.0


class TestOnTableUnitChange:
    """Tests for on_table_unit_change handler."""

    def test_same_unit_returns_unchanged(self):
        """No conversion when new unit equals previous unit."""
        unit_limits = {"cm": {"min": 60, "max": 300}}

        def convert_unit_to_unit(value, from_unit, to_unit):
            return value

        new_w, new_h, new_unit = handlers.on_table_unit_change(
            "cm", 120.0, 120.0, "cm", unit_limits, convert_unit_to_unit
        )

        assert new_w == 120.0
        assert new_h == 120.0
        assert new_unit == "cm"

    def test_cm_to_inches_converts_values(self):
        """Converts cm to inches correctly."""
        unit_limits = {"in": {"min": 24, "max": 120}}

        def convert_unit_to_unit(value, from_unit, to_unit):
            if from_unit == "cm" and to_unit == "in":
                return value / 2.5
            return value

        new_w, new_h, new_unit = handlers.on_table_unit_change(
            "in", 120.0, 60.0, "cm", unit_limits, convert_unit_to_unit
        )

        assert new_w == 48.0
        assert new_h == 24.0
        assert new_unit == "in"

    def test_clamps_below_min(self):
        """Values below minimum are clamped to min."""
        unit_limits = {"cm": {"min": 60, "max": 300}}

        def convert_unit_to_unit(value, from_unit, to_unit):
            return value * 0.5  # Simulate conversion that goes below min

        new_w, new_h, new_unit = handlers.on_table_unit_change(
            "cm", 100.0, 100.0, "in", unit_limits, convert_unit_to_unit
        )

        assert new_w == 60.0
        assert new_h == 60.0
        assert new_unit == "cm"

    def test_clamps_above_max(self):
        """Values above maximum are clamped to max."""
        unit_limits = {"cm": {"min": 60, "max": 300}}

        def convert_unit_to_unit(value, from_unit, to_unit):
            return value * 10  # Simulate conversion that goes above max

        new_w, new_h, new_unit = handlers.on_table_unit_change(
            "cm", 100.0, 100.0, "in", unit_limits, convert_unit_to_unit
        )

        assert new_w == 300.0
        assert new_h == 300.0
        assert new_unit == "cm"


class TestUpdateObjectiveDefaults:
    """Tests for update_objective_defaults handler."""

    def test_calculates_center_in_mm(self):
        """Calculates table center point in millimeters."""

        def convert_to_cm(value, unit):
            return value  # Assume already in cm

        center_x, center_y = handlers.update_objective_defaults(
            120.0, 120.0, "cm", convert_to_cm
        )

        assert center_x == 600.0  # 120cm = 1200mm / 2
        assert center_y == 600.0

    def test_handles_different_dimensions(self):
        """Handles rectangular tables."""

        def convert_to_cm(value, unit):
            return value

        center_x, center_y = handlers.update_objective_defaults(
            180.0, 120.0, "cm", convert_to_cm
        )

        assert center_x == 900.0  # 180cm = 1800mm / 2
        assert center_y == 600.0  # 120cm = 1200mm / 2

    def test_converts_from_inches(self):
        """Converts from inches to cm before calculating center."""

        def convert_to_cm(value, unit):
            if unit == "in":
                return value * 2.5
            return value

        center_x, center_y = handlers.update_objective_defaults(
            48.0, 48.0, "in", convert_to_cm
        )

        assert center_x == 600.0  # 48in = 120cm = 1200mm / 2
        assert center_y == 600.0


class TestToggleSection:
    """Tests for the canonical toggle_section function and its aliases."""

    def test_enabled_returns_visible(self):
        result = handlers.toggle_section(True)
        assert result["visible"] is True

    def test_disabled_returns_hidden(self):
        result = handlers.toggle_section(False)
        assert result["visible"] is False

    def test_aliases_are_same_function(self):
        """All named toggle aliases point to toggle_section."""
        assert handlers.toggle_vp_section is handlers.toggle_section
        assert handlers.toggle_deployment_zones_section is handlers.toggle_section
        assert handlers.toggle_scenography_section is handlers.toggle_section
        assert handlers.toggle_objective_points_section is handlers.toggle_section
        assert handlers.toggle_special_rules_section is handlers.toggle_section


class TestToggleVpSection:
    """Tests for toggle_vp_section handler."""

    def test_enabled_returns_visible(self):
        """Enabled toggle returns visible update."""
        result = handlers.toggle_vp_section(True)
        assert result["visible"] is True

    def test_disabled_returns_hidden(self):
        """Disabled toggle returns hidden update."""
        result = handlers.toggle_vp_section(False)
        assert result["visible"] is False


class TestToggleSpecialRulesSection:
    """Tests for toggle_special_rules_section handler."""

    def test_enabled_returns_update_with_visible(self):
        """Enabled toggle returns gr.update with visible=True."""
        result = handlers.toggle_special_rules_section(True)
        # gr.update returns a dict with __class__ == gr.Update
        # Check that visible is set
        assert result.get("visible") is True

    def test_disabled_returns_update_with_hidden(self):
        """Disabled toggle returns gr.update with visible=False."""
        result = handlers.toggle_special_rules_section(False)
        assert result.get("visible") is False


class TestToggleScenographyForms:
    """Tests for toggle_scenography_forms handler."""

    def test_circle_shows_circle_form(self):
        """Circle type shows only circle form."""
        result = handlers.toggle_scenography_forms("circle")

        assert result["circle_form_row"]["visible"] is True
        assert result["rect_form_row"]["visible"] is False
        assert result["polygon_form_col"]["visible"] is False

    def test_rect_shows_rect_form(self):
        """Rect type shows only rect form."""
        result = handlers.toggle_scenography_forms("rect")

        assert result["circle_form_row"]["visible"] is False
        assert result["rect_form_row"]["visible"] is True
        assert result["polygon_form_col"]["visible"] is False

    def test_polygon_shows_polygon_form(self):
        """Polygon type shows only polygon form."""
        result = handlers.toggle_scenography_forms("polygon")

        assert result["circle_form_row"]["visible"] is False
        assert result["rect_form_row"]["visible"] is False
        assert result["polygon_form_col"]["visible"] is True


class TestUpdateSharedWithVisibility:
    """Tests for update_shared_with_visibility handler."""

    def test_shared_returns_visible(self):
        """Shared visibility shows shared_with field."""
        result = handlers.update_shared_with_visibility("shared")
        assert result["visible"] is True

    def test_private_returns_hidden(self):
        """Private visibility hides shared_with field."""
        result = handlers.update_shared_with_visibility("private")
        assert result["visible"] is False

    def test_public_returns_hidden(self):
        """Public visibility hides shared_with field."""
        result = handlers.update_shared_with_visibility("public")
        assert result["visible"] is False


class TestOnPolygonPresetChange:
    """Tests for on_polygon_preset_change handler."""

    def test_custom_returns_default_triangle(self):
        """Custom preset returns default 3-point triangle."""
        polygon_presets = {"triangle": 3, "pentagon": 5, "hexagon": 6}

        points = handlers.on_polygon_preset_change("custom", polygon_presets)

        assert len(points) == 3
        assert points == [[600.0, 300.0], [1000.0, 700.0], [200.0, 700.0]]

    def test_triangle_generates_3_points(self):
        """Triangle preset generates 3 evenly spaced points."""
        polygon_presets = {"triangle": 3, "pentagon": 5, "hexagon": 6}

        points = handlers.on_polygon_preset_change("triangle", polygon_presets)

        assert len(points) == 3
        # Points should be evenly distributed around a circle
        for point in points:
            assert len(point) == 2

    def test_pentagon_generates_5_points(self):
        """Pentagon preset generates 5 evenly spaced points."""
        polygon_presets = {"triangle": 3, "pentagon": 5, "hexagon": 6}

        points = handlers.on_polygon_preset_change("pentagon", polygon_presets)

        assert len(points) == 5

    def test_hexagon_generates_6_points(self):
        """Hexagon preset generates 6 evenly spaced points."""
        polygon_presets = {"triangle": 3, "pentagon": 5, "hexagon": 6}

        points = handlers.on_polygon_preset_change("hexagon", polygon_presets)

        assert len(points) == 6

    def test_points_centered_at_600_600(self):
        """Generated points are centered at (600, 600)."""
        polygon_presets = {"triangle": 3}

        points = handlers.on_polygon_preset_change("triangle", polygon_presets)

        # Calculate centroid
        avg_x = sum(p[0] for p in points) / len(points)
        avg_y = sum(p[1] for p in points) / len(points)

        assert abs(avg_x - 600.0) < 1.0
        assert abs(avg_y - 600.0) < 1.0


class TestOnZoneBorderOrFillChange:
    """Tests for on_zone_border_or_fill_change handler."""

    def test_north_border_with_fill_returns_full_width(self):
        """North border with fill_side returns table width."""
        width, height = handlers.on_zone_border_or_fill_change(
            "north", True, 1200, 1200
        )

        assert width == 1200.0
        assert height == 200.0

    def test_south_border_with_fill_returns_full_width(self):
        """South border with fill_side returns table width."""
        width, height = handlers.on_zone_border_or_fill_change(
            "south", True, 1800, 1200
        )

        assert width == 1800.0
        assert height == 200.0

    def test_east_border_with_fill_returns_full_height(self):
        """East border with fill_side returns table height."""
        width, height = handlers.on_zone_border_or_fill_change("east", True, 1200, 1200)

        assert width == 200.0
        assert height == 1200.0

    def test_west_border_with_fill_returns_full_height(self):
        """West border with fill_side returns table height."""
        width, height = handlers.on_zone_border_or_fill_change("west", True, 1200, 1800)

        assert width == 200.0
        assert height == 1800.0

    def test_north_border_without_fill_returns_defaults(self):
        """North border without fill_side returns default dimensions."""
        width, height = handlers.on_zone_border_or_fill_change(
            "north", False, 1200, 1200
        )

        assert width == 1200.0
        assert height == 200.0

    def test_east_border_without_fill_returns_defaults(self):
        """East border without fill_side returns default dimensions."""
        width, height = handlers.on_zone_border_or_fill_change(
            "east", False, 1200, 1200
        )

        assert width == 200.0
        assert height == 1200.0
