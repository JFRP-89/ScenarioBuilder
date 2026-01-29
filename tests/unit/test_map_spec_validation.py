from domain.maps.spec import validate_map_spec, validate_table_size


def test_map_spec_shapes_inside_bounds():
    map_spec = {
        "shapes": [
            {"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10},
            {"type": "circle", "cx": 5, "cy": 5, "r": 2},
        ]
    }
    assert validate_map_spec(map_spec, 20, 20) is True


def test_validate_table_size_positive():
    assert validate_table_size(100, 100) is True


def test_validate_table_size_zero_or_negative():
    assert validate_table_size(0, 100) is False
    assert validate_table_size(100, 0) is False


def test_validate_map_spec_rect_out_of_bounds():
    map_spec = {
        "shapes": [
            {"type": "rect", "x": 15, "y": 15, "w": 10, "h": 10},
        ]
    }
    assert validate_map_spec(map_spec, 20, 20) is False


def test_validate_map_spec_circle_out_of_bounds():
    map_spec = {
        "shapes": [
            {"type": "circle", "cx": 18, "cy": 18, "r": 5},
        ]
    }
    assert validate_map_spec(map_spec, 20, 20) is False


def test_validate_map_spec_rect_position_out_of_bounds():
    # Test rect with x > width
    map_spec = {
        "shapes": [
            {"type": "rect", "x": 25, "y": 5, "w": 5, "h": 5},
        ]
    }
    assert validate_map_spec(map_spec, 20, 20) is False


def test_validate_map_spec_circle_position_out_of_bounds():
    # Test circle with cx > width
    map_spec = {
        "shapes": [
            {"type": "circle", "cx": 25, "cy": 5, "r": 2},
        ]
    }
    assert validate_map_spec(map_spec, 20, 20) is False
