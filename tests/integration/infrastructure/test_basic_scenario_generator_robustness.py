"""Fuzz and integration tests for BasicScenarioGenerator robustness.

Tests cover:
- Deterministic reproducibility across seeds 1..200
- No overlap for every generated layout
- MapSpec validity for every generated layout
- Metadata (attempt_index, generator_version) populated
- Bad/edge-case seeds handled gracefully
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from domain.cards.card import GameMode
from domain.maps.collision import MIN_CLEARANCE_MM, has_no_collisions
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from infrastructure.scenario_generation.basic_scenario_generator import (
    GENERATOR_VERSION,
    BasicScenarioGenerator,
)


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def table_standard() -> TableSize:
    return TableSize.standard()


@pytest.fixture
def table_massive() -> TableSize:
    return TableSize.massive()


@pytest.fixture
def table_small() -> TableSize:
    """Smallest valid table: 600x600mm."""
    return TableSize(width_mm=600, height_mm=600)


@pytest.fixture
def mode() -> GameMode:
    return GameMode.MATCHED


@pytest.fixture
def gen() -> BasicScenarioGenerator:
    return BasicScenarioGenerator()


# =============================================================================
# FUZZ: Deterministic reproducibility (seeds 1..200)
# =============================================================================
class TestFuzzDeterminism:
    """Same seed + table + mode → identical shapes every time."""

    @pytest.mark.parametrize("seed", range(1, 201))
    def test_reproducible_for_seed(
        self,
        seed: int,
        table_standard: TableSize,
        mode: GameMode,
        gen: BasicScenarioGenerator,
    ) -> None:
        shapes_a = gen.generate_shapes(seed=seed, table=table_standard, mode=mode)
        shapes_b = gen.generate_shapes(seed=seed, table=table_standard, mode=mode)
        assert shapes_a == shapes_b, f"seed={seed} not deterministic"


# =============================================================================
# FUZZ: No overlap for each generated layout (seeds 1..200)
# =============================================================================
class TestFuzzNoOverlap:
    """Every generated layout has no overlapping shapes."""

    @pytest.mark.parametrize("seed", range(1, 201))
    def test_no_overlap_for_seed(
        self,
        seed: int,
        table_standard: TableSize,
        mode: GameMode,
        gen: BasicScenarioGenerator,
    ) -> None:
        shapes = gen.generate_shapes(seed=seed, table=table_standard, mode=mode)
        assert has_no_collisions(
            shapes, MIN_CLEARANCE_MM
        ), f"seed={seed} has overlapping shapes: {shapes}"


# =============================================================================
# FUZZ: MapSpec validity (seeds 1..200)
# =============================================================================
class TestFuzzMapSpecValidity:
    """Every generated layout is valid for MapSpec."""

    @pytest.mark.parametrize("seed", range(1, 201))
    def test_valid_map_spec_for_seed(
        self,
        seed: int,
        table_standard: TableSize,
        mode: GameMode,
        gen: BasicScenarioGenerator,
    ) -> None:
        shapes = gen.generate_shapes(seed=seed, table=table_standard, mode=mode)
        # Should not raise
        spec = MapSpec(table=table_standard, shapes=shapes)
        assert spec is not None


# =============================================================================
# TABLE SIZE VARIANTS
# =============================================================================
class TestTableSizeVariants:
    """Generator works across different table sizes."""

    SEEDS: ClassVar[list[int]] = [1, 42, 123, 999]

    @pytest.mark.parametrize("seed", SEEDS)
    def test_standard_table(
        self, seed: int, table_standard: TableSize, mode: GameMode
    ) -> None:
        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=seed, table=table_standard, mode=mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2
        MapSpec(table=table_standard, shapes=shapes)

    @pytest.mark.parametrize("seed", SEEDS)
    def test_massive_table(
        self, seed: int, table_massive: TableSize, mode: GameMode
    ) -> None:
        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=seed, table=table_massive, mode=mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2
        MapSpec(table=table_massive, shapes=shapes)

    @pytest.mark.parametrize("seed", SEEDS)
    def test_small_table(
        self, seed: int, table_small: TableSize, mode: GameMode
    ) -> None:
        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=seed, table=table_small, mode=mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2
        MapSpec(table=table_small, shapes=shapes)


# =============================================================================
# METADATA
# =============================================================================
class TestGeneratorMetadata:
    """Generator populates metadata after generation."""

    def test_last_attempt_index_is_populated(
        self,
        table_standard: TableSize,
        mode: GameMode,
        gen: BasicScenarioGenerator,
    ) -> None:
        gen.generate_shapes(seed=42, table=table_standard, mode=mode)
        assert gen.last_attempt_index >= 0

    def test_generator_version_is_set(
        self,
        gen: BasicScenarioGenerator,
    ) -> None:
        assert gen.generator_version == GENERATOR_VERSION

    def test_generator_version_equals_sceno_v1(
        self,
        gen: BasicScenarioGenerator,
    ) -> None:
        assert gen.generator_version == "sceno-v1"


# =============================================================================
# SCENOGRAPHY FIELDS
# =============================================================================
class TestScenographyFields:
    """Generated shapes include description and allow_overlap fields."""

    def test_shapes_include_description_and_allow_overlap(
        self,
        table_standard: TableSize,
        mode: GameMode,
        gen: BasicScenarioGenerator,
    ) -> None:
        shapes = gen.generate_shapes(seed=42, table=table_standard, mode=mode)

        for shape in shapes:
            assert isinstance(shape.get("description"), str)
            assert shape["description"].strip() != ""
            assert shape.get("allow_overlap") is False


# =============================================================================
# GAME MODES
# =============================================================================
class TestGameModes:
    """Generator works for all game modes."""

    @pytest.mark.parametrize("game_mode", list(GameMode))
    def test_all_modes_produce_valid_shapes(
        self,
        game_mode: GameMode,
        table_standard: TableSize,
        gen: BasicScenarioGenerator,
    ) -> None:
        shapes = gen.generate_shapes(seed=42, table=table_standard, mode=game_mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2
        MapSpec(table=table_standard, shapes=shapes)


# =============================================================================
# EDGE CASES
# =============================================================================
class TestEdgeCases:
    """Edge-case seeds and parameters."""

    def test_seed_zero(self, table_standard: TableSize, mode: GameMode) -> None:
        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=0, table=table_standard, mode=mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2

    def test_seed_one(self, table_standard: TableSize, mode: GameMode) -> None:
        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=1, table=table_standard, mode=mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2

    def test_max_seed(self, table_standard: TableSize, mode: GameMode) -> None:
        from domain.seed import MAX_SEED

        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=MAX_SEED, table=table_standard, mode=mode)
        assert isinstance(shapes, list)
        assert len(shapes) >= 2
        MapSpec(table=table_standard, shapes=shapes)

    def test_large_seed(self, table_standard: TableSize, mode: GameMode) -> None:
        gen = BasicScenarioGenerator()
        shapes = gen.generate_shapes(seed=2**30, table=table_standard, mode=mode)
        assert isinstance(shapes, list)
        MapSpec(table=table_standard, shapes=shapes)
