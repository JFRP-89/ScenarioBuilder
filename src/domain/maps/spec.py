from __future__ import annotations

from typing import Dict, List


TABLE_PRESETS = {
    "standard": {"width": 120, "height": 120},
    "massive": {"width": 180, "height": 120},
}


def validate_table_size(width: int, height: int) -> bool:
    return width > 0 and height > 0


def validate_map_spec(map_spec: Dict, width: int, height: int) -> bool:
    shapes: List[Dict] = map_spec.get("shapes", [])
    for shape in shapes:
        if shape.get("type") == "rect":
            if not (0 <= shape["x"] <= width and 0 <= shape["y"] <= height):
                return False
            if shape["x"] + shape["w"] > width or shape["y"] + shape["h"] > height:
                return False
        if shape.get("type") == "circle":
            if not (0 <= shape["cx"] <= width and 0 <= shape["cy"] <= height):
                return False
            if shape["cx"] + shape["r"] > width or shape["cy"] + shape["r"] > height:
                return False
    return True
