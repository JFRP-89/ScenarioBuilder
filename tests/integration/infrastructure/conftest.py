"""Shared fixtures for infrastructure integration tests."""

from __future__ import annotations

import pytest

from domain.cards.card import GameMode
from domain.maps.table_size import TableSize
from infrastructure.scenario_generation.basic_scenario_generator import (
    BasicScenarioGenerator,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
