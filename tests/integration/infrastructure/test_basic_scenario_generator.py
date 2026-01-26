"""RED tests for BasicScenarioGenerator.

Tests the basic implementation of ScenarioGenerator for the modern API.
This generator produces random shapes for scenario maps.
"""

from __future__ import annotations

import pytest

from domain.cards.card import GameMode
from domain.maps.table_size import TableSize
from domain.maps.map_spec import MapSpec


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def table() -> TableSize:
    """Standard table size for testing."""
    return TableSize.standard()


@pytest.fixture
def mode() -> GameMode:
    """Standard game mode for testing."""
    return GameMode.MATCHED


# =============================================================================
# VALIDITY TESTS
# =============================================================================
class TestBasicScenarioGeneratorValidity:
    """Tests for generating valid shapes."""

    def test_generates_shapes_valid_for_map_spec(
        self,
        table: TableSize,
        mode: GameMode,
    ) -> None:
        """Generated shapes are valid for MapSpec (no exception)."""
        from infrastructure.scenario_generation.basic_scenario_generator import (
            BasicScenarioGenerator,
        )

        # Arrange
        gen = BasicScenarioGenerator()
        seed = 123

        # Act
        shapes = gen.generate_shapes(seed=seed, table=table, mode=mode)

        # Assert - shapes should be valid for MapSpec
        assert isinstance(shapes, list)
        # This should not raise ValidationError
        map_spec = MapSpec(table=table, shapes=shapes)
        assert map_spec is not None


# =============================================================================
# DETERMINISM TESTS
# =============================================================================
class TestBasicScenarioGeneratorDeterminism:
    """Tests for deterministic generation by seed."""

    def test_same_seed_produces_same_shapes(
        self,
        table: TableSize,
        mode: GameMode,
    ) -> None:
        """Same seed/table/mode produces identical shapes."""
        from infrastructure.scenario_generation.basic_scenario_generator import (
            BasicScenarioGenerator,
        )

        # Arrange
        gen = BasicScenarioGenerator()
        seed = 123

        # Act
        shapes1 = gen.generate_shapes(seed=seed, table=table, mode=mode)
        shapes2 = gen.generate_shapes(seed=seed, table=table, mode=mode)

        # Assert - exact equality
        assert shapes1 == shapes2

    def test_different_seed_produces_different_shapes(
        self,
        table: TableSize,
        mode: GameMode,
    ) -> None:
        """Different seeds normally produce different shapes."""
        from infrastructure.scenario_generation.basic_scenario_generator import (
            BasicScenarioGenerator,
        )

        # Arrange
        gen = BasicScenarioGenerator()
        seeds = [1, 10, 100, 123, 124, 200, 500, 999, 1234, 9999]

        # Act - generate shapes for multiple seeds
        shapes_list = [gen.generate_shapes(seed=s, table=table, mode=mode) for s in seeds]

        # Assert - there should be variation across different seeds
        # Using repr() to get string representation for set deduplication
        unique_shapes = {repr(shapes) for shapes in shapes_list}
        assert len(unique_shapes) > 1, "All seeds produced identical shapes"


# =============================================================================
# SANITY / LIMITS TESTS
# =============================================================================
class TestBasicScenarioGeneratorLimits:
    """Tests for reasonable limits and sanity checks."""

    def test_does_not_exceed_max_shapes_limit(
        self,
        table: TableSize,
        mode: GameMode,
    ) -> None:
        """Generated shapes count does not exceed reasonable limit."""
        from infrastructure.scenario_generation.basic_scenario_generator import (
            BasicScenarioGenerator,
        )

        # Arrange
        gen = BasicScenarioGenerator()
        seed = 123

        # Act
        shapes = gen.generate_shapes(seed=seed, table=table, mode=mode)

        # Assert - reasonable limit (aligned with domain max_shapes if any)
        assert len(shapes) <= 100

    def test_polygon_points_within_limits(
        self,
        table: TableSize,
        mode: GameMode,
    ) -> None:
        """Polygon shapes do not exceed point count limit (if any exist)."""
        from infrastructure.scenario_generation.basic_scenario_generator import (
            BasicScenarioGenerator,
        )

        # Arrange
        gen = BasicScenarioGenerator()
        seed = 123

        # Act
        shapes = gen.generate_shapes(seed=seed, table=table, mode=mode)

        # Assert - check polygon point limits only for polygons with points
        for shape in shapes:
            if isinstance(shape, dict) and shape.get("type") == "polygon":
                if "points" in shape and isinstance(shape["points"], list):
                    assert len(shape["points"]) <= 200

    def test_multiple_seeds_produce_valid_shapes(
        self,
        table: TableSize,
        mode: GameMode,
    ) -> None:
        """Multiple different seeds all produce valid shapes."""
        from infrastructure.scenario_generation.basic_scenario_generator import (
            BasicScenarioGenerator,
        )

        # Arrange
        gen = BasicScenarioGenerator()
        seeds = [1, 42, 123, 999, 12345]

        # Act & Assert
        for seed in seeds:
            shapes = gen.generate_shapes(seed=seed, table=table, mode=mode)
            # Should not raise
            map_spec = MapSpec(table=table, shapes=shapes)
            assert map_spec is not None
