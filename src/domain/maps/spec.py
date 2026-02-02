from __future__ import annotations

from typing import Dict, List, cast

TABLE_PRESETS = {
    "standard": {"width": 120, "height": 120},
    "massive": {"width": 180, "height": 120},
}


def validate_table_size(width: int, height: int) -> bool:
    return width > 0 and height > 0


def _iter_shapes(map_spec: Dict) -> List[Dict]:
    return cast(List[Dict], map_spec.get("shapes", []))


def _is_rect_valid(shape: Dict, width: int, height: int) -> bool:
    if not (0 <= cast(int, shape["x"]) <= width and 0 <= cast(int, shape["y"]) <= height):
        return False
    return (
        cast(int, shape["x"]) + cast(int, shape["w"]) <= width
        and cast(int, shape["y"]) + cast(int, shape["h"]) <= height
    )


def _is_circle_valid(shape: Dict, width: int, height: int) -> bool:
    if not (0 <= cast(int, shape["cx"]) <= width and 0 <= cast(int, shape["cy"]) <= height):
        return False
    return (
        cast(int, shape["cx"]) + cast(int, shape["r"]) <= width
        and cast(int, shape["cy"]) + cast(int, shape["r"]) <= height
    )


def validate_map_spec(map_spec: Dict, width: int, height: int) -> bool:
    for shape in _iter_shapes(map_spec):
        if shape.get("type") == "rect" and not _is_rect_valid(shape, width, height):
            return False
        if shape.get("type") == "circle" and not _is_circle_valid(shape, width, height):
            return False
    return True
