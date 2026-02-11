"""
MVP RED tests for MapSpec domain object.

MapSpec defines shapes on a game table, using mm (int) coordinates.
Only the minimal contract is tested here; extra hardening is deferred.
"""

from __future__ import annotations

import pytest
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def table() -> TableSize:
    return TableSize.standard()


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


# =============================================================================
# MVP TESTS
# =============================================================================
def test_mapspec_accepts_valid_shapes_standard_table(
    table: TableSize, circle_ok: dict, rect_ok: dict, poly_ok: dict
):
    MapSpec(table=table, shapes=[circle_ok, rect_ok, poly_ok])


def test_circle_out_of_bounds_raises(table: TableSize):
    circle_out = {"type": "circle", "cx": 50, "cy": 50, "r": 100}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[circle_out])


def test_rect_out_of_bounds_raises(table: TableSize):
    rect_out = {"type": "rect", "x": 1000, "y": 1000, "width": 300, "height": 300}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[rect_out])


def test_polygon_out_of_bounds_raises(table: TableSize):
    poly_out = {
        "type": "polygon",
        "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 1300, "y": 10}],
    }
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[poly_out])


def test_circle_radius_must_be_positive(table: TableSize):
    circle = {"type": "circle", "cx": 600, "cy": 600, "r": 0}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[circle])


def test_rect_width_height_must_be_positive(table: TableSize):
    rect = {"type": "rect", "x": 100, "y": 100, "width": 0, "height": 200}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[rect])


def test_polygon_requires_at_least_3_points(table: TableSize):
    poly_two = {"type": "polygon", "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}]}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[poly_two])


def test_rejects_more_than_100_shapes(table: TableSize):
    shapes = [{"type": "circle", "cx": 600, "cy": 600, "r": 10} for _ in range(101)]
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=shapes)


def test_rejects_polygon_with_more_than_200_points(table: TableSize):
    W, H = 1200, 1200
    points = [{"x": (i * 7) % W, "y": (i * 11) % H} for i in range(201)]
    poly = {"type": "polygon", "points": points}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[poly])


def test_rejects_unknown_shape_type(table: TableSize):
    shape = {"type": "triangle", "x1": 0, "y1": 0, "x2": 100, "y2": 0}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[shape])


@pytest.mark.parametrize(
    "shape",
    [
        {"type": "circle", "cx": "600", "cy": 600, "r": 100},
        {"type": "rect", "x": 100, "y": 100, "width": "300", "height": 200},
        {
            "type": "polygon",
            "points": [
                {"x": "0", "y": 0},
                {"x": 100, "y": 0},
                {"x": 50, "y": 100},
            ],
        },
    ],
)
def test_rejects_non_int_coordinates_or_sizes(table: TableSize, shape: dict):
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[shape])


# TODO(hardening): añadir tests de missing fields, payload shape strictness y edge cases adicionales.


# =============================================================================
# ADDITIONAL COVERAGE TESTS
# =============================================================================
def test_requires_type_field_in_shape(table: TableSize):
    shape_no_type = {"cx": 600, "cy": 600, "r": 100}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[shape_no_type])


def test_requires_type_to_be_string(table: TableSize):
    shape_bad_type = {"type": 123, "cx": 600, "cy": 600, "r": 100}
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[shape_bad_type])


def test_circle_requires_all_fields(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[{"type": "circle", "cx": 600, "cy": 600}])


def test_rect_requires_all_fields(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(
            table=table, shapes=[{"type": "rect", "x": 100, "y": 100, "width": 200}]
        )


def test_polygon_requires_points_field(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[{"type": "polygon"}])


def test_polygon_points_must_be_list(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=[{"type": "polygon", "points": "not_a_list"}])


def test_polygon_point_must_be_dict(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(
            table=table,
            shapes=[{"type": "polygon", "points": [(0, 0), (10, 10), (10, 0)]}],
        )


def test_polygon_point_requires_x_and_y(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(
            table=table,
            shapes=[
                {
                    "type": "polygon",
                    "points": [{"x": 0}, {"x": 10, "y": 10}, {"x": 10, "y": 0}],
                }
            ],
        )


def test_circle_with_bool_coordinate_is_rejected(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(
            table=table, shapes=[{"type": "circle", "cx": True, "cy": 600, "r": 100}]
        )


def test_rect_with_bool_dimension_is_rejected(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(
            table=table,
            shapes=[
                {"type": "rect", "x": 100, "y": 100, "width": False, "height": 200}
            ],
        )


def test_shapes_none_is_rejected(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=None)


def test_shape_not_dict_is_rejected(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(table=table, shapes=["not_a_dict"])


def test_rect_with_negative_x_or_y_is_rejected(table: TableSize):
    with pytest.raises(ValidationError):
        MapSpec(
            table=table,
            shapes=[{"type": "rect", "x": -10, "y": 100, "width": 200, "height": 200}],
        )
    with pytest.raises(ValidationError):
        MapSpec(
            table=table,
            shapes=[{"type": "rect", "x": 100, "y": -10, "width": 200, "height": 200}],
        )


# =============================================================================
# OBJECTIVE_SHAPES TESTS
# =============================================================================
def test_mapspec_accepts_valid_objective_shapes(table: TableSize):
    """MapSpec accepts valid objective_shapes within bounds."""
    objective_shapes = [
        {"cx": 600, "cy": 600},
        {"cx": 1000, "cy": 800},
    ]
    MapSpec(table=table, shapes=[], objective_shapes=objective_shapes)


def test_mapspec_accepts_none_objective_shapes(table: TableSize):
    """MapSpec accepts None for objective_shapes (optional)."""
    MapSpec(table=table, shapes=[], objective_shapes=None)


def test_mapspec_rejects_objective_shape_out_of_bounds(table: TableSize):
    """MapSpec rejects objective_shape with center outside table."""
    objective_shapes = [
        {"cx": 2000, "cy": 600},  # cx > table width (1200mm for standard)
    ]
    with pytest.raises(ValidationError, match="out of bounds"):
        MapSpec(table=table, shapes=[], objective_shapes=objective_shapes)


def test_mapspec_rejects_objective_shape_with_negative_coords(table: TableSize):
    """MapSpec rejects objective_shape with negative coordinates."""
    objective_shapes = [
        {"cx": -100, "cy": 600},
    ]
    with pytest.raises(ValidationError, match="out of bounds"):
        MapSpec(table=table, shapes=[], objective_shapes=objective_shapes)


def test_mapspec_rejects_too_many_objective_shapes(table: TableSize):
    """MapSpec rejects more than 10 objective_shapes."""
    objective_shapes = [{"cx": 100 + i * 50, "cy": 100} for i in range(11)]
    with pytest.raises(ValidationError, match="too many objective points"):
        MapSpec(table=table, shapes=[], objective_shapes=objective_shapes)


def test_mapspec_rejects_objective_shape_missing_cx(table: TableSize):
    """MapSpec rejects objective_shape without cx coordinate."""
    objective_shapes = [
        {"cy": 600},  # Missing cx
    ]
    with pytest.raises(ValidationError, match="requires cx, cy"):
        MapSpec(table=table, shapes=[], objective_shapes=objective_shapes)


def test_mapspec_rejects_objective_shape_missing_cy(table: TableSize):
    """MapSpec rejects objective_shape without cy coordinate."""
    objective_shapes = [
        {"cx": 600},  # Missing cy
    ]
    with pytest.raises(ValidationError, match="requires cx, cy"):
        MapSpec(table=table, shapes=[], objective_shapes=objective_shapes)


def test_mapspec_rejects_objective_shapes_not_list(table: TableSize):
    """MapSpec rejects objective_shapes that is not a list."""
    with pytest.raises(ValidationError, match="must be list"):
        MapSpec(table=table, shapes=[], objective_shapes={"cx": 600, "cy": 600})


def test_mapspec_rejects_objective_shape_not_dict(table: TableSize):
    """MapSpec rejects objective_shape that is not a dict."""
    with pytest.raises(ValidationError, match="must be dict"):
        MapSpec(table=table, shapes=[], objective_shapes=["not_a_dict"])
