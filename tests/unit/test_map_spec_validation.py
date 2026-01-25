from domain.maps.spec import validate_map_spec


def test_map_spec_shapes_inside_bounds():
    map_spec = {
        "shapes": [
            {"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10},
            {"type": "circle", "cx": 5, "cy": 5, "r": 2},
        ]
    }
    assert validate_map_spec(map_spec, 20, 20) is True
