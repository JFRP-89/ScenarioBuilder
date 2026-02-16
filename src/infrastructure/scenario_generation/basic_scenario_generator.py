"""BasicScenarioGenerator - Robust deterministic shape generation.

A placement-based implementation of ScenarioGenerator that:
- Places shapes one-by-one with collision checks
- Uses derive_attempt_seed for deterministic retries
- Validates final output with MapSpec
"""

from __future__ import annotations

import random

from domain.cards.card import GameMode
from domain.maps.collision import (
    MIN_CLEARANCE_MM,
    has_no_collisions,
    shape_in_bounds,
    shapes_overlap,
)
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.seed import derive_attempt_seed

# Generation constants
GENERATOR_VERSION: str = "sceno-v1"
MAX_GLOBAL_ATTEMPTS: int = 50
MAX_PLACEMENT_TRIES_PER_SHAPE: int = 200

_SCENERY_THEMES: dict[str, dict[str, list[str]]] = {
    "urban": {
        "rect": [
            "Low ruins",
            "Stone wall",
            "Collapsed building",
            "Barricade",
            "Storage crates",
        ],
        "circle": [
            "Plaza fountain",
            "Fuel tank",
            "Radial monument",
            "Traffic roundabout",
            "Cooling silo",
        ],
        "polygon": [
            "Rubble field",
            "Collapsed plaza",
            "Broken pavement",
            "Urban debris",
            "Construction site",
        ],
    },
    "forest": {
        "rect": [
            "Hunting lodge",
            "Wooden palisade",
            "Abandoned cabin",
            "Rangers outpost",
            "Fallen log pile",
        ],
        "circle": [
            "Dense woods",
            "Sacred grove",
            "Thicket",
            "Mossy clearing",
            "Ancient tree ring",
        ],
        "polygon": [
            "Rocky ground",
            "Marshland",
            "Difficult terrain",
            "Thorny brush",
            "Wetland",
        ],
    },
    "desert": {
        "rect": [
            "Broken outpost",
            "Sandbag line",
            "Crumbling wall",
            "Supply depot",
            "Shelter ruins",
        ],
        "circle": [
            "Impact crater",
            "Dust bowl",
            "Sunken pit",
            "Dry well",
            "Oasis pool",
        ],
        "polygon": [
            "Rocky ridge",
            "Dune field",
            "Salt flats",
            "Scrap heap",
            "Scorched ground",
        ],
    },
    "shire": {
        "rect": [
            "Thatched cottage",
            "Stone hedge",
            "Market stall",
            "Barn",
            "Wooden fence",
        ],
        "circle": [
            "Village green",
            "Orchard grove",
            "Well",
            "Hobbit garden",
            "Flower ring",
        ],
        "polygon": [
            "Rolling hill",
            "Plowed field",
            "Footpath",
            "Farmland",
            "Meadow",
        ],
    },
    "rohan": {
        "rect": [
            "Riders camp",
            "Wooden palisade",
            "Horse stables",
            "Watch hut",
            "Supply wagons",
        ],
        "circle": [
            "Bonfire pit",
            "Horse corral",
            "Grass ring",
            "Training circle",
            "Meeting circle",
        ],
        "polygon": [
            "Rolling plain",
            "Wind swept ridge",
            "Tall grass",
            "Grazing field",
            "Rocky outcrop",
        ],
    },
    "gondor": {
        "rect": [
            "Guard post",
            "Stone bastion",
            "Broken wall",
            "Supply depot",
            "Barricade",
        ],
        "circle": [
            "Signal fire",
            "Fountain",
            "Statue base",
            "Well",
            "Courtyard",
        ],
        "polygon": [
            "Battle debris",
            "Broken causeway",
            "Rubble field",
            "Paved square",
            "Collapsed arch",
        ],
    },
    "minas_tirith": {
        "rect": [
            "White wall",
            "Guardhouse",
            "Gatehouse ruins",
            "Supply crates",
            "Barricade",
        ],
        "circle": [
            "Fountain",
            "Tower base",
            "Beacon brazier",
            "Courtyard",
            "Statue plinth",
        ],
        "polygon": [
            "Broken stairs",
            "Rubble field",
            "Collapsed terrace",
            "Paved square",
            "Shattered arch",
        ],
    },
    "osgiliath": {
        "rect": [
            "Broken bridge",
            "Collapsed hall",
            "Crumbling wall",
            "Stone pier",
            "Ruined tower",
        ],
        "circle": [
            "Sunken plaza",
            "Flooded pool",
            "Collapsed dome",
            "Fountain base",
            "Tower base",
        ],
        "polygon": [
            "River rubble",
            "Slick stone",
            "Shattered causeway",
            "Broken pavement",
            "Debris field",
        ],
    },
    "helms_deep": {
        "rect": [
            "Fortified wall",
            "Gatehouse",
            "Supply crates",
            "Barricade",
            "Siege debris",
        ],
        "circle": [
            "Culvert",
            "Signal fire",
            "Well",
            "Guard circle",
            "Training ring",
        ],
        "polygon": [
            "Rocky slope",
            "Broken ramp",
            "Debris field",
            "Rubble heap",
            "Stony ground",
        ],
    },
    "isengard": {
        "rect": [
            "Forge platform",
            "Wooden stockade",
            "Steel scaffolds",
            "Supply depot",
            "Barracks",
        ],
        "circle": [
            "Blast pit",
            "Water pool",
            "Engine base",
            "Signal fire",
            "Machinery ring",
        ],
        "polygon": [
            "Industrial debris",
            "Ashen ground",
            "Scrap heap",
            "Broken track",
            "Rubble field",
        ],
    },
    "mordor": {
        "rect": [
            "Dark watchtower",
            "Spiked palisade",
            "Broken wall",
            "Supply pens",
            "Slave pens",
        ],
        "circle": [
            "Lava pit",
            "Ash crater",
            "Dark well",
            "Signal fire",
            "Pit trap",
        ],
        "polygon": [
            "Ash field",
            "Scorched ground",
            "Jagged rocks",
            "Rubble heap",
            "Wasted land",
        ],
    },
    "moria": {
        "rect": [
            "Stone pillar",
            "Fallen arch",
            "Crumbling wall",
            "Ancient dais",
            "Broken gate",
        ],
        "circle": [
            "Well",
            "Chasm edge",
            "Rune circle",
            "Collapsed dome",
            "Deep pit",
        ],
        "polygon": [
            "Rubble field",
            "Broken walkway",
            "Rocky ground",
            "Shattered floor",
            "Debris pile",
        ],
    },
    "rivendell": {
        "rect": [
            "Elven pavilion",
            "Stone terrace",
            "Garden wall",
            "Rivendell bridge",
            "Archive ruins",
        ],
        "circle": [
            "Reflecting pool",
            "Sacred grove",
            "Fountain",
            "Sunwell",
            "Meeting circle",
        ],
        "polygon": [
            "Terraced garden",
            "Rocky streambed",
            "Shaded glade",
            "Leafy ground",
            "Broken steps",
        ],
    },
    "lothlorien": {
        "rect": [
            "Mallorn platform",
            "Wooden walkway",
            "Elven stair",
            "Garden wall",
            "Sentry post",
        ],
        "circle": [
            "Sacred grove",
            "Moonlit pool",
            "Tree ring",
            "Glade",
            "Shrine",
        ],
        "polygon": [
            "Leafy ground",
            "Mossy field",
            "Shaded glade",
            "Difficult terrain",
            "Fallen leaves",
        ],
    },
    "mirkwood": {
        "rect": [
            "Webbed ruins",
            "Fallen tree",
            "Wooden palisade",
            "Hunters camp",
            "Sentry post",
        ],
        "circle": [
            "Dark thicket",
            "Spider nest",
            "Poison pool",
            "Black grove",
            "Shadow ring",
        ],
        "polygon": [
            "Twisted roots",
            "Foggy ground",
            "Difficult terrain",
            "Rocky ground",
            "Deadfall",
        ],
    },
    "fangorn": {
        "rect": [
            "Ent shelter",
            "Wooden barricade",
            "Fallen log pile",
            "Abandoned camp",
            "Rangers post",
        ],
        "circle": [
            "Ancient grove",
            "Mossy clearing",
            "Spring",
            "Meeting circle",
            "Ring of stones",
        ],
        "polygon": [
            "Rocky ground",
            "Thorny brush",
            "Difficult terrain",
            "Wetland",
            "Forest floor",
        ],
    },
    "misty_mountains": {
        "rect": [
            "Stone outcrop",
            "Broken bridge",
            "Mountain shelter",
            "Watch post",
            "Ruined gate",
        ],
        "circle": [
            "Mountain lake",
            "Cave mouth",
            "Stone ring",
            "Cliff basin",
            "Glacial pool",
        ],
        "polygon": [
            "Rocky ridge",
            "Scree field",
            "Snowy ground",
            "Jagged rocks",
            "Steep slope",
        ],
    },
    "erebor": {
        "rect": [
            "Dwarven hall",
            "Stone pillar",
            "Forge platform",
            "Treasure vault",
            "Guard post",
        ],
        "circle": [
            "Great forge",
            "Anvil circle",
            "Rune circle",
            "Hot pit",
            "Well",
        ],
        "polygon": [
            "Broken walkway",
            "Rubble field",
            "Stone floor",
            "Collapsed stair",
            "Debris pile",
        ],
    },
    "dale": {
        "rect": [
            "Market stall",
            "Trade post",
            "Broken wall",
            "Guardhouse",
            "Barricade",
        ],
        "circle": [
            "Town square",
            "Fountain",
            "Well",
            "Signal fire",
            "Meeting circle",
        ],
        "polygon": [
            "Paved square",
            "Rubble field",
            "Broken street",
            "Collapsed plaza",
            "Debris field",
        ],
    },
}


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
            mode: Game mode (currently not used for variation).

        Returns:
            List of shape dictionaries valid for MapSpec.

        Raises:
            RuntimeError: If all retry attempts are exhausted without
                producing a valid, collision-free layout.
        """
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
            except Exception:
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
