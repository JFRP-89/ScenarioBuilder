"""
Unit tests for deployment shape validation.

Tests for validate_deployment_shapes() and _validate_deployment_shape()
in domain.maps.map_spec_shape_validation.

Rules:
- Max 4 deployment shapes
- Each must have either 'border' or 'corner' (not both)
- border: north/south/east/west → type must be 'rect'
- corner: north-east/north-west/south-east/south-west → type must be 'polygon'
- Geometric bounds still apply
"""

from __future__ import annotations

import pytest
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.map_spec_shape_validation import validate_deployment_shapes
from domain.maps.table_size import TableSize

TABLE = TableSize.standard()  # 1200x1200 mm
W = TABLE.width_mm
H = TABLE.height_mm


# =============================================================================
# VALID DEPLOYMENT SHAPES (HAPPY PATH)
# =============================================================================
class TestValidDeploymentShapes:
    """Happy path tests for deployment shape validation."""

    def test_none_is_valid(self):
        validate_deployment_shapes(None, W, H)

    def test_empty_list_is_valid(self):
        validate_deployment_shapes([], W, H)

    def test_single_border_rect(self):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
            },
        ]
        validate_deployment_shapes(shapes, W, H)

    def test_single_corner_polygon(self):
        shapes = [
            {
                "type": "polygon",
                "corner": "south-east",
                "points": [
                    {"x": 1200, "y": 1200},
                    {"x": 1200, "y": 900},
                    {"x": 900, "y": 1200},
                ],
            },
        ]
        validate_deployment_shapes(shapes, W, H)

    def test_max_four_deployment_shapes(self):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
            },
            {
                "type": "rect",
                "border": "south",
                "x": 0,
                "y": 1000,
                "width": 1200,
                "height": 200,
            },
            {
                "type": "polygon",
                "corner": "south-west",
                "points": [
                    {"x": 0, "y": 1200},
                    {"x": 0, "y": 900},
                    {"x": 300, "y": 1200},
                ],
            },
            {
                "type": "polygon",
                "corner": "south-east",
                "points": [
                    {"x": 1200, "y": 1200},
                    {"x": 1200, "y": 900},
                    {"x": 900, "y": 1200},
                ],
            },
        ]
        validate_deployment_shapes(shapes, W, H)  # type: ignore[arg-type]

    @pytest.mark.parametrize("border", ["north", "south", "east", "west"])
    def test_all_valid_borders(self, border):
        shapes = [
            {
                "type": "rect",
                "border": border,
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 200,
            },
        ]
        validate_deployment_shapes(shapes, W, H)

    @pytest.mark.parametrize(
        "corner",
        ["north-east", "north-west", "south-east", "south-west"],
    )
    def test_all_valid_corners(self, corner):
        shapes = [
            {
                "type": "polygon",
                "corner": corner,
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 300, "y": 0},
                    {"x": 0, "y": 300},
                ],
            },
        ]
        validate_deployment_shapes(shapes, W, H)

    def test_deployment_shape_with_description(self):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "description": "Ejército A",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
            },
        ]
        validate_deployment_shapes(shapes, W, H)


# =============================================================================
# BORDER VS CORNER EXCLUSIVITY
# =============================================================================
class TestBorderCornerExclusivity:
    """Tests that border and corner are mutually exclusive."""

    def test_both_border_and_corner_raises(self):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "corner": "south-east",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
            },
        ]
        with pytest.raises(
            ValidationError,
            match="(?i)either.*border.*corner.*not both",
        ):
            validate_deployment_shapes(shapes, W, H)

    def test_neither_border_nor_corner_raises(self):
        shapes = [
            {
                "type": "rect",
                "x": 0,
                "y": 0,
                "width": 1200,
                "height": 200,
            },
        ]
        with pytest.raises(
            ValidationError,
            match="(?i)either.*border.*corner",
        ):
            validate_deployment_shapes(shapes, W, H)


# =============================================================================
# MAX DEPLOYMENT SHAPES
# =============================================================================
class TestMaxDeploymentShapes:
    """Tests for the max 4 deployment shapes limit."""

    def test_five_deployment_shapes_raises(self):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "x": 0,
                "y": 0 + i * 200,
                "width": 1200,
                "height": 100,
            }
            for i in range(5)
        ]
        with pytest.raises(
            ValidationError,
            match="(?i)too many deployment shapes.*max 4",
        ):
            validate_deployment_shapes(shapes, W, H)


# =============================================================================
# TYPE CONSTRAINTS
# =============================================================================
class TestDeploymentShapeTypeConstraints:
    """Tests that border requires rect and corner requires polygon."""

    def test_border_with_polygon_type_raises(self):
        shapes = [
            {
                "type": "polygon",
                "border": "north",
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 300, "y": 0},
                    {"x": 0, "y": 300},
                ],
            },
        ]
        with pytest.raises(
            ValidationError,
            match="(?i)border.*must be type.*rect",
        ):
            validate_deployment_shapes(shapes, W, H)

    def test_corner_with_rect_type_raises(self):
        shapes = [
            {
                "type": "rect",
                "corner": "south-east",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 200,
            },
        ]
        with pytest.raises(
            ValidationError,
            match="(?i)corner.*must be type.*polygon",
        ):
            validate_deployment_shapes(shapes, W, H)


# =============================================================================
# INVALID BORDER / CORNER VALUES
# =============================================================================
class TestInvalidBorderCornerValues:
    """Tests that invalid border/corner values are rejected."""

    def test_invalid_border_value_raises(self):
        shapes = [
            {
                "type": "rect",
                "border": "center",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 200,
            },
        ]
        with pytest.raises(ValidationError, match="(?i)unknown border"):
            validate_deployment_shapes(shapes, W, H)

    def test_invalid_corner_value_raises(self):
        shapes = [
            {
                "type": "polygon",
                "corner": "center",
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 300, "y": 0},
                    {"x": 0, "y": 300},
                ],
            },
        ]
        with pytest.raises(ValidationError, match="(?i)unknown corner"):
            validate_deployment_shapes(shapes, W, H)

    def test_border_not_string_raises(self):
        shapes = [
            {
                "type": "rect",
                "border": 123,
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 200,
            },
        ]
        with pytest.raises(ValidationError, match="(?i)border must be a string"):
            validate_deployment_shapes(shapes, W, H)

    def test_corner_not_string_raises(self):
        shapes = [
            {
                "type": "polygon",
                "corner": 456,
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 300, "y": 0},
                    {"x": 0, "y": 300},
                ],
            },
        ]
        with pytest.raises(ValidationError, match="(?i)corner must be a string"):
            validate_deployment_shapes(shapes, W, H)


# =============================================================================
# TYPE VALIDATION
# =============================================================================
class TestDeploymentShapesTypeValidation:
    """Tests for type validation of the deployment_shapes parameter itself."""

    def test_non_list_raises(self):
        with pytest.raises(ValidationError, match="(?i)deployment_shapes must be list"):
            validate_deployment_shapes("not a list", W, H)  # type: ignore[arg-type]

    def test_non_dict_element_raises(self):
        with pytest.raises(ValidationError, match="(?i)deployment_shape must be dict"):
            validate_deployment_shapes(["not a dict"], W, H)  # type: ignore[list-item]


# =============================================================================
# GEOMETRIC BOUNDS (delegated but verified)
# =============================================================================
class TestDeploymentShapeGeometricBounds:
    """Tests that geometric bounds validation still applies to deployment shapes."""

    def test_border_rect_out_of_bounds_raises(self):
        shapes = [
            {
                "type": "rect",
                "border": "north",
                "x": 0,
                "y": 0,
                "width": 1500,  # wider than table
                "height": 200,
            },
        ]
        with pytest.raises(ValidationError, match="(?i)out of bounds"):
            validate_deployment_shapes(shapes, W, H)

    def test_corner_polygon_out_of_bounds_raises(self):
        shapes = [
            {
                "type": "polygon",
                "corner": "south-east",
                "points": [
                    {"x": 1200, "y": 1500},  # y > table height
                    {"x": 1200, "y": 900},
                    {"x": 900, "y": 1200},
                ],
            },
        ]
        with pytest.raises(ValidationError, match="(?i)out of bounds"):
            validate_deployment_shapes(shapes, W, H)


# =============================================================================
# MapSpec INTEGRATION
# =============================================================================
class TestDeploymentShapesInMapSpec:
    """Tests that MapSpec properly validates deployment_shapes."""

    def test_mapspec_accepts_valid_deployment_shapes(self):
        MapSpec(
            table=TABLE,
            shapes=[],
            deployment_shapes=[
                {
                    "type": "rect",
                    "border": "north",
                    "x": 0,
                    "y": 0,
                    "width": 1200,
                    "height": 200,
                }
            ],
        )

    def test_mapspec_rejects_invalid_deployment_shapes(self):
        with pytest.raises(ValidationError):
            MapSpec(
                table=TABLE,
                shapes=[],
                deployment_shapes=[
                    {
                        "type": "rect",
                        "x": 0,
                        "y": 0,
                        "width": 200,
                        "height": 200,
                    }  # missing border or corner
                ],
            )

    def test_mapspec_none_deployment_shapes_is_valid(self):
        MapSpec(table=TABLE, shapes=[], deployment_shapes=None)
