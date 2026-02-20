"""BasicScenarioGenerator - Robust deterministic shape generation.

A placement-based implementation of ScenarioGenerator that:
- Places shapes one-by-one with collision checks
- Uses derive_attempt_seed for deterministic retries
- Validates final output with MapSpec
"""

from __future__ import annotations

import random

from domain.cards.card import GameMode
from domain.errors import ValidationError
from domain.maps.collision import (
    MIN_CLEARANCE_MM,
    has_no_collisions,
    shape_in_bounds,
    shapes_overlap,
)
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.seed import derive_attempt_seed
from infrastructure.scenario_generation._catalogs import (
    SCENERY_THEMES as _SCENERY_THEMES,
)

# Generation constants
GENERATOR_VERSION: str = "sceno-v1"
MAX_GLOBAL_ATTEMPTS: int = 50
MAX_PLACEMENT_TRIES_PER_SHAPE: int = 200


class BasicScenarioGenerator:
    """Robust scenario generator with placement-based collision avoidance.

    Generates 2-5 random shapes (rectangles, circles, polygons) that are:
    - Guaranteed to fit within table bounds
    - Non-overlapping (with MIN_CLEARANCE_MM gap)
    - Valid for MapSpec construction
    - Deterministic for a given (seed, table, mode) tuple

    After generation, stores metadata about the last generation:
    - last_attempt_index: which retry attempt succeeded (0 = first try)
    - generator_version: version string for reproducibility tracking
    """

    def __init__(self) -> None:
        self.last_attempt_index: int = 0
        self.generator_version: str = GENERATOR_VERSION

    # -----------------------------------------------------------------
    # Shape factories (private)
    # -----------------------------------------------------------------

    def _pick_theme(self, rng: random.Random) -> str:
        return rng.choice(list(_SCENERY_THEMES.keys()))

    def _rect_shape(self, rng: random.Random, w: int, h: int, theme: str) -> dict:
        max_width = max(50, min(300, w // 3))
        max_height = max(50, min(300, h // 3))
        width = rng.randint(50, max_width)
        height = rng.randint(50, max_height)
        x = rng.randint(0, w - width)
        y = rng.randint(0, h - height)
        description = rng.choice(_SCENERY_THEMES[theme]["rect"])
        return {
            "type": "rect",
            "description": description,
            "allow_overlap": False,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

    def _circle_shape(self, rng: random.Random, w: int, h: int, theme: str) -> dict:
        max_r = max(30, min(200, w // 6, h // 6))
        r = rng.randint(30, max_r)
        cx = rng.randint(r, w - r)
        cy = rng.randint(r, h - r)
        description = rng.choice(_SCENERY_THEMES[theme]["circle"])
        return {
            "type": "circle",
            "description": description,
            "allow_overlap": False,
            "cx": cx,
            "cy": cy,
            "r": r,
        }

    def _polygon_shape(self, rng: random.Random, w: int, h: int, theme: str) -> dict:
        n = rng.randint(3, 6)
        points = [{"x": rng.randint(0, w), "y": rng.randint(0, h)} for _ in range(n)]
        description = rng.choice(_SCENERY_THEMES[theme]["polygon"])
        return {
            "type": "polygon",
            "description": description,
            "allow_overlap": False,
            "points": points,
        }

    # -----------------------------------------------------------------
    # Placement engine (private)
    # -----------------------------------------------------------------

    def _try_place_shape(
        self,
        rng: random.Random,
        kind: str,
        placed: list[dict],
        w: int,
        h: int,
        theme: str,
    ) -> dict | None:
        """Try to place a single shape without collision.

        Makes up to MAX_PLACEMENT_TRIES_PER_SHAPE attempts.
        Returns the shape dict if successful, None if all attempts fail.
        """
        for _ in range(MAX_PLACEMENT_TRIES_PER_SHAPE):
            if kind == "rect":
                candidate = self._rect_shape(rng, w, h, theme)
            elif kind == "circle":
                candidate = self._circle_shape(rng, w, h, theme)
            else:
                candidate = self._polygon_shape(rng, w, h, theme)

            # Check bounds
            if not shape_in_bounds(candidate, w, h):
                continue

            # Check collision with already-placed shapes
            collision = False
            for existing in placed:
                if shapes_overlap(candidate, existing, MIN_CLEARANCE_MM):
                    collision = True
                    break
            if not collision:
                return candidate

        return None

    def _generate_with_placement(
        self, rng: random.Random, w: int, h: int, theme: str
    ) -> list[dict] | None:
        """Generate a set of shapes using placement-based approach.

        Returns list of shapes if all can be placed, None if placement fails.
        """
        shapes: list[dict] = []
        count = rng.randint(2, 5)

        for _ in range(count):
            kind = rng.choice(["rect", "circle", "polygon"])
            shape = self._try_place_shape(rng, kind, shapes, w, h, theme)
            if shape is None:
                return None  # Could not place this shape → global retry
            shapes.append(shape)

        return shapes

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def generate_shapes(
        self, seed: int, table: TableSize, mode: GameMode
    ) -> list[dict]:
        """Generate shapes for a scenario map.

        Uses a placement-based algorithm with collision avoidance.
        If placement fails, retries with a derived seed up to
        MAX_GLOBAL_ATTEMPTS times. Validates output with MapSpec.

        Args:
            seed: Random seed for deterministic generation.
            table: Table size defining the valid area.
            mode: Game mode (required by protocol, unused).

        Returns:
            List of shape dictionaries valid for MapSpec.

        Raises:
            RuntimeError: If all retry attempts are exhausted without
                producing a valid, collision-free layout.
        """
        del mode  # Required by ScenarioGenerator protocol
        w = table.width_mm
        h = table.height_mm

        for attempt in range(MAX_GLOBAL_ATTEMPTS):
            attempt_seed = derive_attempt_seed(seed, attempt)
            rng = random.Random(attempt_seed)  # nosec B311
            theme = self._pick_theme(rng)
            shapes = self._generate_with_placement(rng, w, h, theme)
            if shapes is None:
                continue

            # Validate with MapSpec (catches any edge-case domain violations)
            try:
                MapSpec(table=table, shapes=shapes)
            except ValidationError:
                continue

            # Verify no collisions (belt-and-suspenders)
            if not has_no_collisions(shapes, MIN_CLEARANCE_MM):
                continue

            # Success — record metadata
            self.last_attempt_index = attempt
            return shapes

        # Exhausted all attempts — should be extremely rare on valid tables
        raise RuntimeError(
            f"Failed to generate valid shapes after {MAX_GLOBAL_ATTEMPTS} "
            f"attempts for seed={seed}, table={w}x{h}mm"
        )
