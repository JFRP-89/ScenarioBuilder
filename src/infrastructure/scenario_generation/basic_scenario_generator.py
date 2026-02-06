"""BasicScenarioGenerator - Simple deterministic shape generation.

A basic implementation of ScenarioGenerator that produces random shapes
deterministically based on a seed value.
"""

from __future__ import annotations

import random

from domain.cards.card import GameMode
from domain.maps.table_size import TableSize


class BasicScenarioGenerator:
    """Basic scenario generator with deterministic shape generation.

    Generates 2-5 random shapes (rectangles, circles, polygons) that are
    guaranteed to fit within the table bounds.
    """

    def _rect_shape(self, rng: random.Random, w: int, h: int) -> dict:
        max_width = max(50, min(300, w // 3))
        max_height = max(50, min(300, h // 3))
        width = rng.randint(50, max_width)
        height = rng.randint(50, max_height)
        x = rng.randint(0, w - width)
        y = rng.randint(0, h - height)
        return {
            "type": "rect",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

    def _circle_shape(self, rng: random.Random, w: int, h: int) -> dict:
        max_r = max(30, min(200, w // 6, h // 6))
        r = rng.randint(30, max_r)
        cx = rng.randint(r, w - r)
        cy = rng.randint(r, h - r)
        return {
            "type": "circle",
            "cx": cx,
            "cy": cy,
            "r": r,
        }

    def _polygon_shape(self, rng: random.Random, w: int, h: int) -> dict:
        n = rng.randint(3, 6)
        points = [{"x": rng.randint(0, w), "y": rng.randint(0, h)} for _ in range(n)]
        return {
            "type": "polygon",
            "points": points,
        }

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        """Generate shapes for a scenario map.

        Args:
            seed: Random seed for deterministic generation.
            table: Table size defining the valid area.
            mode: Game mode (currently not used for variation).

        Returns:
            List of shape dictionaries valid for MapSpec.
        """
        rng = random.Random(seed)  # nosec B311 - deterministic, non-crypto use
        w = table.width_mm
        h = table.height_mm

        shapes: list[dict] = []

        # Generate 2-5 shapes
        count = rng.randint(2, 5)

        for _ in range(count):
            kind = rng.choice(["rect", "circle", "polygon"])

            if kind == "rect":
                shapes.append(self._rect_shape(rng, w, h))

            elif kind == "circle":
                shapes.append(self._circle_shape(rng, w, h))

            else:  # polygon
                shapes.append(self._polygon_shape(rng, w, h))

        return shapes
