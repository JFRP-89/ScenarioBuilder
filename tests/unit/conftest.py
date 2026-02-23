"""Shared fixtures for tests/unit/."""

from __future__ import annotations

import pytest

from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize


@pytest.fixture
def table() -> TableSize:
    return TableSize.standard()


@pytest.fixture
def shapes() -> list[dict]:
    return [{"type": "circle", "cx": 600, "cy": 600, "r": 100}]


@pytest.fixture
def map_spec(request: pytest.FixtureRequest) -> MapSpec:
    return MapSpec(
        table=request.getfixturevalue("table"),
        shapes=request.getfixturevalue("shapes"),
    )


@pytest.fixture
def owner() -> str:
    return "user_a"


@pytest.fixture
def other() -> str:
    return "user_b"


@pytest.fixture
def friend() -> str:
    return "user_c"


@pytest.fixture
def blank() -> str:
    return "   "


@pytest.fixture
def circle_ok() -> dict:
    return {"type": "circle", "cx": 600, "cy": 600, "r": 100}


@pytest.fixture
def rect_ok() -> dict:
    return {"type": "rect", "x": 100, "y": 200, "width": 300, "height": 400}


@pytest.fixture
def poly_ok() -> dict:
    return {
        "type": "polygon",
        "points": [{"x": 0, "y": 0}, {"x": 200, "y": 0}, {"x": 200, "y": 200}],
    }
