"""GenerateScenarioCard use case.

Generates a new scenario card by orchestrating domain logic and ports.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Collection, Optional, Union

from application.ports.repositories import CardRepository
from application.ports.scenario_generation import (
    IdGenerator,
    ScenarioGenerator,
    SeedGenerator,
)
from application.use_cases._validation import validate_actor_id
from domain.cards.card import Card, GameMode, parse_game_mode
from domain.cards.card_content_validation import (
    validate_objectives,
    validate_shared_with_visibility,
    validate_special_rules,
)
from domain.errors import ValidationError
from domain.maps.map_spec import MapSpec
from domain.maps.table_size import TableSize
from domain.security.authz import Visibility, parse_visibility
from infrastructure.generators.deterministic_seed_generator import (
    calculate_seed_from_config,
)

# =============================================================================
# TABLE PRESETS
# =============================================================================
_TABLE_PRESETS = frozenset(["standard", "massive", "custom"])

_CONTENT_THEMES: dict[str, dict[str, list[str]]] = {
    "shire": {
        "armies": [
            "Shire Militia",
            "Bounders",
            "Hobbit Archers",
            "Bywater Wardens",
            "Green Hills Patrol",
        ],
        "deployment": [
            "Quiet patrol",
            "Sudden ambush",
            "Guard the homestead",
            "Hold the hedgerow",
            "Skirmish at the green",
        ],
        "layout": [
            "Bywater Lanes",
            "Green Hillstead",
            "Hedge Maze",
            "Market Day",
            "Old Windmill",
        ],
        "objectives": [
            "Protect the village",
            "Rescue the locals",
            "Secure the storehouse",
            "Hold the green",
            "Escort the messenger",
        ],
        "initial_priority": [
            "Secure the lanes",
            "Protect the homesteads",
            "Hold the market square",
            "Keep the militia safe",
            "Delay the attackers",
        ],
    },
    "rohan": {
        "armies": [
            "Riders of Rohan",
            "Westfold Militia",
            "Royal Guard",
            "Eastfold Riders",
            "Helm Guard",
        ],
        "deployment": [
            "Cavalry sweep",
            "Hold the ridgeline",
            "Flank charge",
            "Shieldwall",
            "Rearguard stand",
        ],
        "layout": [
            "Westfold Plain",
            "Riders Camp",
            "Windy Ridge",
            "Fords of Isen",
            "Eastfold Track",
        ],
        "objectives": [
            "Break the line",
            "Hold the ford",
            "Secure the hill",
            "Rescue the standard",
            "Drive back the raiders",
        ],
        "initial_priority": [
            "Control the ridgeline",
            "Protect the cavalry",
            "Hold the ford",
            "Delay the enemy",
            "Secure the camp",
        ],
    },
    "gondor": {
        "armies": [
            "Gondor Line",
            "Osgiliath Veterans",
            "Ithilien Rangers",
            "Citadel Guard",
            "Pelargir Guard",
        ],
        "deployment": [
            "Hold the ruins",
            "Shieldwall",
            "Guard the bridge",
            "Counterattack",
            "Defensive line",
        ],
        "layout": [
            "Ruins of Osgiliath",
            "River Crossing",
            "Broken Causeway",
            "Gatehouse",
            "White City Outskirts",
        ],
        "objectives": [
            "Hold the bridge",
            "Secure the causeway",
            "Protect the standard",
            "Relieve the garrison",
            "Push the line forward",
        ],
        "initial_priority": [
            "Hold the bridge",
            "Protect the garrison",
            "Secure the ruins",
            "Control the riverbank",
            "Retake the plaza",
        ],
    },
    "minas_tirith": {
        "armies": [
            "Tower Guard",
            "Citadel Guard",
            "Gondor Reinforcements",
            "White City Watch",
            "Fountain Court",
        ],
        "deployment": [
            "Hold the gate",
            "Inner wall defense",
            "Countercharge",
            "Hold the courtyard",
            "Last stand",
        ],
        "layout": [
            "White City Courtyard",
            "Gatehouse Steps",
            "Upper Circle",
            "Tower Square",
            "Citadel Terrace",
        ],
        "objectives": [
            "Defend the gate",
            "Protect the citadel",
            "Hold the stairs",
            "Rescue the captain",
            "Secure the courtyard",
        ],
        "initial_priority": [
            "Hold the gate",
            "Protect the banner",
            "Secure the tower",
            "Delay the assault",
            "Hold the upper circle",
        ],
    },
    "osgiliath": {
        "armies": [
            "Gondor Veterans",
            "Rangers of Ithilien",
            "Mordor Raiders",
            "City Guard",
            "Bridge Defenders",
        ],
        "deployment": [
            "Ruin to ruin",
            "River crossing",
            "Hold the bridge",
            "Skirmish line",
            "Flank assault",
        ],
        "layout": [
            "Eastern Ruins",
            "Broken Bridge",
            "Sunken Plaza",
            "Fallen Tower",
            "Riverbank",
        ],
        "objectives": [
            "Hold the crossing",
            "Secure the ruins",
            "Rescue the wounded",
            "Control the plaza",
            "Push across the river",
        ],
        "initial_priority": [
            "Hold the crossing",
            "Secure the ruins",
            "Control the riverbank",
            "Retake the bridge",
            "Break the enemy line",
        ],
    },
    "helms_deep": {
        "armies": [
            "Rohan Defenders",
            "Westfold Militia",
            "Isengard Assault",
            "Wall Guard",
            "Fortress Reserve",
        ],
        "deployment": [
            "Hold the wall",
            "Relief force",
            "Storm the gate",
            "Sally forth",
            "Last stand",
        ],
        "layout": [
            "Deeping Wall",
            "Hornburg Courtyard",
            "Gatehouse",
            "Culvert",
            "Causeway",
        ],
        "objectives": [
            "Defend the wall",
            "Hold the gate",
            "Break the siege",
            "Rescue the defenders",
            "Secure the courtyard",
        ],
        "initial_priority": [
            "Hold the wall",
            "Protect the gate",
            "Secure the culvert",
            "Delay the assault",
            "Hold the courtyard",
        ],
    },
    "isengard": {
        "armies": [
            "Uruk-hai Host",
            "Isengard Raiders",
            "Dunland Allies",
            "White Hand Guard",
            "Siege Crew",
        ],
        "deployment": [
            "Pike advance",
            "Siege line",
            "Flank assault",
            "Night raid",
            "Drive the breach",
        ],
        "layout": [
            "Orthanc Ring",
            "Warg Pens",
            "Forge Yard",
            "Industrial Ditch",
            "Broken Causeway",
        ],
        "objectives": [
            "Break the gate",
            "Hold the yard",
            "Secure the forge",
            "Capture the banner",
            "Drive the defenders",
        ],
        "initial_priority": [
            "Take the yard",
            "Hold the forge",
            "Break the wall",
            "Secure the breach",
            "Drive the line",
        ],
    },
    "mordor": {
        "armies": [
            "Mordor Host",
            "Orc Warband",
            "Black Gate Guard",
            "Morannon Orcs",
            "Harad Allies",
        ],
        "deployment": [
            "Dark assault",
            "Encirclement",
            "Wave attack",
            "Hold the pass",
            "Breach the line",
        ],
        "layout": [
            "Black Gate Approach",
            "Ash Plains",
            "Broken Watchtower",
            "Lava Fields",
            "Wasted Ground",
        ],
        "objectives": [
            "Crush the enemy",
            "Hold the pass",
            "Seize the banner",
            "Burn the outpost",
            "Secure the ridge",
        ],
        "initial_priority": [
            "Hold the pass",
            "Break the line",
            "Secure the ridge",
            "Drive the assault",
            "Capture the outpost",
        ],
    },
    "moria": {
        "armies": [
            "Moria Goblins",
            "Dwarven Delvers",
            "Balins Guard",
            "Expedition Guard",
            "Cave Patrol",
        ],
        "deployment": [
            "Tunnel fight",
            "Hall skirmish",
            "Ambush in the dark",
            "Hold the chamber",
            "Break the line",
        ],
        "layout": [
            "Pillared Hall",
            "Broken Bridge",
            "Deep Tunnel",
            "Collapsed Stair",
            "Dwarven Hall",
        ],
        "objectives": [
            "Secure the chamber",
            "Hold the bridge",
            "Rescue the scouts",
            "Claim the relic",
            "Drive out the foe",
        ],
        "initial_priority": [
            "Hold the hall",
            "Secure the bridge",
            "Control the tunnel",
            "Protect the expedition",
            "Claim the relic",
        ],
    },
    "rivendell": {
        "armies": [
            "Rivendell Elves",
            "Last Alliance",
            "Elven Guard",
            "High Elves",
            "Imladris Patrol",
        ],
        "deployment": [
            "Defensive line",
            "Flank strike",
            "Hold the ford",
            "Swift response",
            "Hidden reserve",
        ],
        "layout": [
            "Hidden Valley",
            "River Crossing",
            "Elven Terrace",
            "Shaded Glade",
            "Broken Bridge",
        ],
        "objectives": [
            "Protect the sanctuary",
            "Hold the ford",
            "Secure the glade",
            "Rescue the envoy",
            "Drive the invaders",
        ],
        "initial_priority": [
            "Hold the ford",
            "Protect the sanctuary",
            "Secure the glade",
            "Delay the enemy",
            "Retake the crossing",
        ],
    },
    "lothlorien": {
        "armies": [
            "Galadhrim",
            "Lorien Guard",
            "Woodland Sentinels",
            "Golden Wood Host",
            "Elven Archers",
        ],
        "deployment": [
            "Forest ambush",
            "Hold the glade",
            "Flank in the trees",
            "Silent advance",
            "Hidden reserve",
        ],
        "layout": [
            "Mallorn Grove",
            "Golden Glade",
            "Woodland Path",
            "Riverbank",
            "Hidden Hollow",
        ],
        "objectives": [
            "Defend the grove",
            "Hold the glade",
            "Secure the riverbank",
            "Rescue the scouts",
            "Drive out the intruders",
        ],
        "initial_priority": [
            "Hold the glade",
            "Protect the grove",
            "Secure the path",
            "Delay the enemy",
            "Cut off the advance",
        ],
    },
    "mirkwood": {
        "armies": [
            "Woodland Realm",
            "Elven Patrol",
            "Dark Forest Host",
            "Forest Wardens",
            "Hunters of the Wood",
        ],
        "deployment": [
            "Ambush in the dark",
            "Hold the clearing",
            "Stalk the enemy",
            "Silent strike",
            "Shadow line",
        ],
        "layout": [
            "Black Thicket",
            "Spider Glade",
            "Shadowed Trail",
            "Foggy Grove",
            "Poison Pools",
        ],
        "objectives": [
            "Clear the glade",
            "Rescue the captives",
            "Secure the trail",
            "Destroy the nests",
            "Hold the clearing",
        ],
        "initial_priority": [
            "Secure the trail",
            "Clear the glade",
            "Hold the clearing",
            "Protect the patrol",
            "Drive out the spiders",
        ],
    },
    "fangorn": {
        "armies": [
            "Ents",
            "Forest Guardians",
            "Rangers of the Wood",
            "Isengard Raiders",
            "Woodland Defenders",
        ],
        "deployment": [
            "Ambush among trees",
            "Hold the forest",
            "Slow advance",
            "Hidden reserve",
            "Guard the path",
        ],
        "layout": [
            "Ancient Grove",
            "Rooted Trail",
            "Mossy Clearing",
            "Stone Circle",
            "Deep Wood",
        ],
        "objectives": [
            "Protect the grove",
            "Hold the trail",
            "Rescue the scouts",
            "Secure the clearing",
            "Drive out the intruders",
        ],
        "initial_priority": [
            "Hold the trail",
            "Protect the grove",
            "Secure the clearing",
            "Delay the enemy",
            "Protect the guardians",
        ],
    },
    "misty_mountains": {
        "armies": [
            "Dwarven Scouts",
            "Mountain Guard",
            "Goblin Raiders",
            "High Pass Patrol",
            "Eagle Watch",
        ],
        "deployment": [
            "Hold the pass",
            "Ambush from above",
            "Skirmish line",
            "Mountain defense",
            "Flank the ridge",
        ],
        "layout": [
            "High Pass",
            "Stone Ridge",
            "Broken Bridge",
            "Mountain Lake",
            "Cliffside Trail",
        ],
        "objectives": [
            "Hold the pass",
            "Secure the ridge",
            "Rescue the scouts",
            "Claim the bridge",
            "Drive back the raiders",
        ],
        "initial_priority": [
            "Hold the pass",
            "Secure the ridge",
            "Protect the scouts",
            "Delay the assault",
            "Control the bridge",
        ],
    },
    "erebor": {
        "armies": [
            "Dwarves of Erebor",
            "Iron Hills",
            "Guard of the Mountain",
            "Dwarven Warriors",
            "Erebor Reserve",
        ],
        "deployment": [
            "Hold the gate",
            "Forge defense",
            "Shieldwall",
            "Countercharge",
            "Stand fast",
        ],
        "layout": [
            "Great Hall",
            "Forge Yard",
            "Stone Gate",
            "Mountain Passage",
            "Treasure Vault",
        ],
        "objectives": [
            "Hold the gate",
            "Secure the forge",
            "Protect the vault",
            "Rescue the miners",
            "Drive out the foe",
        ],
        "initial_priority": [
            "Hold the gate",
            "Protect the vault",
            "Secure the forge",
            "Hold the passage",
            "Break the assault",
        ],
    },
    "dale": {
        "armies": [
            "Dale Guard",
            "Lake-town Militia",
            "River Wardens",
            "Merchant Guard",
            "City Patrol",
        ],
        "deployment": [
            "Hold the square",
            "Bridge defense",
            "Flank assault",
            "Guard the market",
            "Skirmish line",
        ],
        "layout": [
            "Market Square",
            "River Bridge",
            "Stone Street",
            "Merchant Row",
            "Town Gate",
        ],
        "objectives": [
            "Hold the market",
            "Secure the bridge",
            "Rescue the traders",
            "Protect the gate",
            "Drive off the raiders",
        ],
        "initial_priority": [
            "Hold the square",
            "Protect the gate",
            "Secure the bridge",
            "Defend the market",
            "Delay the raiders",
        ],
    },
    "harad": {
        "armies": [
            "Harad Warriors",
            "Serpent Guard",
            "Desert Riders",
            "Harad Raiders",
            "Umbar Corsairs",
        ],
        "deployment": [
            "Desert ambush",
            "Flank assault",
            "Hold the oasis",
            "Skirmish line",
            "Raid the caravan",
        ],
        "layout": [
            "Oasis Ridge",
            "Caravan Trail",
            "Scorched Dunes",
            "Salt Flats",
            "Broken Outpost",
        ],
        "objectives": [
            "Hold the oasis",
            "Raid the caravan",
            "Secure the ridge",
            "Capture the banner",
            "Drive off the patrol",
        ],
        "initial_priority": [
            "Hold the oasis",
            "Secure the ridge",
            "Raid the caravan",
            "Break the line",
            "Control the trail",
        ],
    },
    "rhun": {
        "armies": [
            "Easterlings",
            "Rhun Warband",
            "Dragon Cult",
            "Red Shield Guard",
            "Steppe Riders",
        ],
        "deployment": [
            "Spear wall",
            "Flank assault",
            "Hold the hill",
            "Skirmish line",
            "Encirclement",
        ],
        "layout": [
            "Red Plain",
            "Steppe Ridge",
            "Broken Shrine",
            "Stone Circle",
            "Warded Camp",
        ],
        "objectives": [
            "Hold the hill",
            "Secure the shrine",
            "Capture the banner",
            "Break the line",
            "Drive back the enemy",
        ],
        "initial_priority": [
            "Hold the hill",
            "Secure the shrine",
            "Maintain the line",
            "Break the enemy",
            "Protect the standard",
        ],
    },
    "numenor": {
        "armies": [
            "Faithful of Numenor",
            "Sea Guard",
            "King's Men",
            "Coastal Watch",
            "Numenor Veterans",
        ],
        "deployment": [
            "Hold the harbor",
            "Shieldwall",
            "Coastal defense",
            "Flank by the docks",
            "Guard the gate",
        ],
        "layout": [
            "Harbor Quays",
            "Sea Gate",
            "Stone Promenade",
            "Dockyard",
            "Coastal Road",
        ],
        "objectives": [
            "Hold the harbor",
            "Secure the sea gate",
            "Protect the banner",
            "Control the docks",
            "Drive off the raiders",
        ],
        "initial_priority": [
            "Hold the harbor",
            "Secure the sea gate",
            "Control the docks",
            "Protect the banner",
            "Hold the road",
        ],
    },
    "angmar": {
        "armies": [
            "Angmar Host",
            "Orc Warband",
            "Hill Trolls",
            "Dark Rangers",
            "Witch-king Guard",
        ],
        "deployment": [
            "Shadow advance",
            "Encirclement",
            "Hold the ruin",
            "Night raid",
            "Break the line",
        ],
        "layout": [
            "Frozen Ruins",
            "Broken Watchtower",
            "Ice Field",
            "Dark Pass",
            "Shattered Road",
        ],
        "objectives": [
            "Claim the ruins",
            "Hold the pass",
            "Capture the banner",
            "Crush the defenders",
            "Secure the road",
        ],
        "initial_priority": [
            "Hold the pass",
            "Secure the ruins",
            "Crush the line",
            "Capture the banner",
            "Control the road",
        ],
    },
}


def _is_blank_text(value: Optional[str]) -> bool:
    return value is None or not value.strip()


def _objectives_match_seed(
    request_objectives: Optional[Union[str, dict]],
    seed_objectives: str,
) -> bool:
    """Check if request objectives are unmodified relative to seed output.

    ``resolve_seed_preview`` always returns a plain string for objectives.
    Blank/None → will be auto-filled by seed → counts as unmodified.
    dict (VP-style) → user structured objectives → always modified.
    """
    if request_objectives is None or (
        isinstance(request_objectives, str) and not request_objectives.strip()
    ):
        return True  # blank → will be auto-filled by seed → unmodified
    if isinstance(request_objectives, dict):
        return False  # VP-style objectives never match a seed string
    return request_objectives.strip() == seed_objectives


def _card_to_preview(card: "Card") -> dict[str, str]:
    """Extract preview-compatible dict (text fields) from an existing Card."""
    obj = card.objectives
    if isinstance(obj, dict):
        obj = obj.get("objective", str(obj))
    return {
        "armies": card.armies or "",
        "deployment": card.deployment or "",
        "layout": card.layout or "",
        "objectives": obj or "",
        "initial_priority": card.initial_priority or "",
        "name": card.name or "",
    }


def _card_to_full_data(card: "Card") -> dict[str, Any]:
    """Extract ALL scenario data from an existing Card entity.

    Returns text fields, structured objectives (with VP), shapes,
    special_rules, and name — everything needed to fully replicate
    a scenario.
    """
    return {
        "armies": card.armies or "",
        "deployment": card.deployment or "",
        "layout": card.layout or "",
        "objectives": card.objectives,  # preserves dict w/ VP
        "initial_priority": card.initial_priority or "",
        "name": card.name or "",
        "special_rules": card.special_rules,
        "deployment_shapes": card.map_spec.deployment_shapes or [],
        "objective_shapes": card.map_spec.objective_shapes or [],
        "scenography_specs": card.map_spec.shapes or [],
    }


# =============================================================================
# DETERMINISTIC SHAPE GENERATION
# =============================================================================
_DEPLOYMENT_DESCRIPTIONS = [
    "Vanguard deployment",
    "Flanking position",
    "Defensive line",
    "Staging ground",
]

_OBJECTIVE_DESCRIPTIONS = [
    "Strategic high ground",
    "Supply cache",
    "Ancient relic",
    "Key crossing",
    "Fortified position",
    "Signal beacon",
    "Sacred ground",
    "Prisoner camp",
    "Resource node",
    "Rally point",
]

_SCENOGRAPHY_DESCRIPTIONS_SOLID = [
    "Dense woodland",
    "Ruined building",
    "Rocky outcrop",
    "Stone wall",
    "Fortified tower",
    "Boulder field",
]

_SCENOGRAPHY_DESCRIPTIONS_OVERLAP = [
    "Shallow marsh",
    "Light scrubland",
    "Rough ground",
    "Tall grass",
    "River ford",
    "Sandy dunes",
]


def _generate_random_scenography(
    rng: random.Random,
    width: int,
    height: int,
    allow_overlap: bool,
    index: int,
) -> dict[str, Any]:
    """Generate a single random scenography shape within table bounds."""
    descriptions = (
        _SCENOGRAPHY_DESCRIPTIONS_OVERLAP
        if allow_overlap
        else _SCENOGRAPHY_DESCRIPTIONS_SOLID
    )
    desc = rng.choice(descriptions)
    margin = 50
    shape_type = rng.choice(["circle", "rect", "polygon"])

    if shape_type == "circle":
        max_r = min(width, height) // 8
        r = rng.randint(50, max(51, max_r))
        cx = rng.randint(margin + r, width - margin - r)
        cy = rng.randint(margin + r, height - margin - r)
        return {
            "type": "circle",
            "description": desc,
            "cx": cx,
            "cy": cy,
            "r": r,
            "allow_overlap": allow_overlap,
        }

    if shape_type == "rect":
        max_w = width // 4
        max_h = height // 4
        sw = rng.randint(100, max(101, max_w))
        sh = rng.randint(100, max(101, max_h))
        x = rng.randint(margin, max(margin + 1, width - margin - sw))
        y = rng.randint(margin, max(margin + 1, height - margin - sh))
        return {
            "type": "rect",
            "description": desc,
            "x": x,
            "y": y,
            "width": sw,
            "height": sh,
            "allow_overlap": allow_overlap,
        }

    # polygon (triangle)
    cx = rng.randint(width // 4, 3 * width // 4)
    cy = rng.randint(height // 4, 3 * height // 4)
    size = rng.randint(80, min(width, height) // 5)
    points = [
        {"x": min(width, max(0, cx)), "y": max(0, cy - size)},
        {"x": min(width, cx + size), "y": min(height, cy + size)},
        {"x": max(0, cx - size), "y": min(height, cy + size)},
    ]
    return {
        "type": "polygon",
        "description": desc,
        "points": points,
        "allow_overlap": allow_overlap,
    }


def _build_non_overlapping_deployments(
    selected_edges: list[str],
    dep_depth: int,
    table_width: int,
    table_height: int,
) -> list[dict[str, Any]]:
    """Build deployment zone rectangles that never overlap each other.

    East/West zones are placed first at full height, then North/South
    zones are inset horizontally to avoid colliding with any E/W zones.
    This guarantees zero pixel overlap between any two deployment rects.
    """
    has_east = "east" in selected_edges
    has_west = "west" in selected_edges

    # Horizontal inset for N/S zones: shrink to avoid E/W columns
    ns_x = dep_depth if has_west else 0
    ns_w = table_width - (dep_depth if has_west else 0) - (dep_depth if has_east else 0)

    # Vertical inset for E/W zones: shrink to avoid N/S rows
    has_north = "north" in selected_edges
    has_south = "south" in selected_edges
    ew_y = dep_depth if has_north else 0
    ew_h = (
        table_height - (dep_depth if has_north else 0) - (dep_depth if has_south else 0)
    )

    result: list[dict[str, Any]] = []
    for i, edge in enumerate(selected_edges):
        desc = _DEPLOYMENT_DESCRIPTIONS[i]
        if edge == "north":
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": ns_x,
                    "y": 0,
                    "width": ns_w,
                    "height": dep_depth,
                    "border": "north",
                }
            )
        elif edge == "south":
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": ns_x,
                    "y": table_height - dep_depth,
                    "width": ns_w,
                    "height": dep_depth,
                    "border": "south",
                }
            )
        elif edge == "east":
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": table_width - dep_depth,
                    "y": ew_y,
                    "width": dep_depth,
                    "height": ew_h,
                    "border": "east",
                }
            )
        else:  # west
            result.append(
                {
                    "type": "rect",
                    "description": desc,
                    "x": 0,
                    "y": ew_y,
                    "width": dep_depth,
                    "height": ew_h,
                    "border": "west",
                }
            )
    return result


def _generate_seeded_shapes(
    seed: int,
    table_width: int,
    table_height: int,
) -> dict[str, list[dict[str, Any]]]:
    """Generate deterministic shapes from a seed and table dimensions.

    Uses a separate RNG (seeded from ``f"shapes-{seed}"``) so that shape
    generation is completely independent of text-field auto-fill order.

    Produces:
    - 0-4 deployment_shapes (border rectangles)
    - 0-10 objective_shapes (objective_point markers)
    - 0-3 scenography with allow_overlap=False (solid terrain)
    - 0-3 scenography with allow_overlap=True (passable terrain)
    """
    rng = random.Random(f"shapes-{seed}")  # nosec B311

    # ── Deployment zones (0-4 border rectangles, non-overlapping) ──────
    n_deployment = rng.randint(0, 4)
    dep_depth = min(table_width, table_height) // 6
    edges = ["north", "south", "east", "west"]
    rng.shuffle(edges)
    selected_edges = edges[:n_deployment]
    deployment_shapes = _build_non_overlapping_deployments(
        selected_edges, dep_depth, table_width, table_height
    )

    # ── Objective points (0-10) ──────────────────────────────────────────
    n_objectives = rng.randint(0, 10)
    objective_shapes: list[dict[str, Any]] = []
    for i in range(n_objectives):
        cx = rng.randint(dep_depth, table_width - dep_depth)
        cy = rng.randint(dep_depth, table_height - dep_depth)
        desc = _OBJECTIVE_DESCRIPTIONS[i % len(_OBJECTIVE_DESCRIPTIONS)]
        objective_shapes.append(
            {
                "type": "objective_point",
                "cx": cx,
                "cy": cy,
                "description": desc,
            }
        )

    # ── Scenography (0-3 solid + 0-3 passable) ──────────────────────────
    n_solid = rng.randint(0, 3)
    n_passable = rng.randint(0, 3)
    scenography_specs: list[dict[str, Any]] = []
    for i in range(n_solid):
        scenography_specs.append(
            _generate_random_scenography(
                rng, table_width, table_height, allow_overlap=False, index=i
            )
        )
    for i in range(n_passable):
        scenography_specs.append(
            _generate_random_scenography(
                rng, table_width, table_height, allow_overlap=True, index=i
            )
        )

    return {
        "deployment_shapes": deployment_shapes,
        "objective_shapes": objective_shapes,
        "scenography_specs": scenography_specs,
    }


def _resolve_seeded_content(
    seed: int,
    request: GenerateScenarioCardRequest,
    existing_card: Optional["Card"] = None,
) -> dict[str, Optional[Union[str, dict]]]:
    if seed <= 0:
        return {
            "armies": request.armies,
            "deployment": request.deployment,
            "layout": request.layout,
            "objectives": request.objectives,
            "initial_priority": request.initial_priority,
        }

    # If an existing card with this seed exists, use its data as defaults.
    if existing_card is not None:
        armies = (
            existing_card.armies if _is_blank_text(request.armies) else request.armies
        )
        deployment = (
            existing_card.deployment
            if _is_blank_text(request.deployment)
            else request.deployment
        )
        layout = (
            existing_card.layout if _is_blank_text(request.layout) else request.layout
        )
        objectives: Optional[Union[str, dict]] = request.objectives
        if objectives is None or (
            isinstance(objectives, str) and not objectives.strip()
        ):
            objectives = existing_card.objectives
        initial_priority = (
            existing_card.initial_priority
            if _is_blank_text(request.initial_priority)
            else request.initial_priority
        )
        return {
            "armies": armies,
            "deployment": deployment,
            "layout": layout,
            "objectives": objectives,
            "initial_priority": initial_priority,
        }

    # Fall back to theme-based generation.
    rng = random.Random(seed)  # nosec B311
    theme = rng.choice(list(_CONTENT_THEMES.keys()))
    theme_values = _CONTENT_THEMES[theme]

    armies = (
        rng.choice(theme_values["armies"])
        if _is_blank_text(request.armies)
        else request.armies
    )
    deployment = (
        rng.choice(theme_values["deployment"])
        if _is_blank_text(request.deployment)
        else request.deployment
    )
    layout = (
        rng.choice(theme_values["layout"])
        if _is_blank_text(request.layout)
        else request.layout
    )

    objectives = request.objectives
    if objectives is None or (isinstance(objectives, str) and not objectives.strip()):
        objectives = rng.choice(theme_values["objectives"])

    initial_priority = (
        rng.choice(theme_values["initial_priority"])
        if _is_blank_text(request.initial_priority)
        else request.initial_priority
    )

    return {
        "armies": armies,
        "deployment": deployment,
        "layout": layout,
        "objectives": objectives,
        "initial_priority": initial_priority,
    }


def _resolve_seed_from_themes(seed: int) -> dict[str, str]:
    """Resolve content fields from a seed using theme-based generation.

    This is the internal implementation that generates content from
    ``_CONTENT_THEMES`` without checking existing cards.
    """
    if seed <= 0:
        return {
            "armies": "",
            "deployment": "",
            "layout": "",
            "objectives": "",
            "initial_priority": "",
        }
    rng = random.Random(seed)  # nosec B311
    theme = rng.choice(list(_CONTENT_THEMES.keys()))
    theme_values = _CONTENT_THEMES[theme]
    return {
        "armies": rng.choice(theme_values["armies"]),
        "deployment": rng.choice(theme_values["deployment"]),
        "layout": rng.choice(theme_values["layout"]),
        "objectives": rng.choice(theme_values["objectives"]),
        "initial_priority": rng.choice(theme_values["initial_priority"]),
    }


def resolve_seed_preview(seed: int) -> dict[str, str]:
    """Resolve content fields from a seed (theme-only, no repo lookup).

    Backward-compatible public function. Does NOT check existing cards.
    For repo-aware resolution, use ``GenerateScenarioCard.resolve_seed_preview``.
    """
    return _resolve_seed_from_themes(seed)


def _resolve_table(
    preset: str,
    width_mm: Optional[int] = None,
    height_mm: Optional[int] = None,
) -> TableSize:
    """Resolve table preset to TableSize.

    Args:
        preset: Table preset ("standard", "massive", or "custom")
        width_mm: Width in mm (required if preset is "custom")
        height_mm: Height in mm (required if preset is "custom")

    Returns:
        TableSize instance

    Raises:
        ValidationError: If preset is unknown or custom dimensions are invalid
    """
    if preset == "standard":
        return TableSize.standard()
    elif preset == "massive":
        return TableSize.massive()
    elif preset == "custom":
        if width_mm is None or height_mm is None:
            raise ValidationError(
                "Custom table preset requires table_width_mm and table_height_mm"
            )
        # TableSize constructor validates dimensions
        return TableSize(width_mm=width_mm, height_mm=height_mm)
    else:
        raise ValidationError(
            f"unknown table preset '{preset}', "
            f"must be one of: {', '.join(sorted(_TABLE_PRESETS))}"
        )


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================
@dataclass
class GenerateScenarioCardRequest:
    """Request DTO for GenerateScenarioCard use case."""

    actor_id: Optional[str]
    mode: Union[str, GameMode]
    seed: Optional[int]
    table_preset: str
    visibility: Optional[Union[str, Visibility]]
    shared_with: Optional[Collection[str]]
    armies: Optional[str] = None
    deployment: Optional[str] = None
    layout: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    initial_priority: Optional[str] = None
    name: Optional[str] = None
    special_rules: Optional[Union[str, list[dict]]] = None
    map_specs: Optional[list[dict]] = None
    scenography_specs: Optional[list[dict]] = None
    deployment_shapes: Optional[list[dict]] = None
    objective_shapes: Optional[list[dict]] = None
    # Custom table dimensions (when table_preset is "custom")
    table_width_mm: Optional[int] = None
    table_height_mm: Optional[int] = None
    # If provided, reuses this card_id (for update/edit flows)
    card_id: Optional[str] = None
    # If True, user designs scenario manually from scratch (no seed auto-fill).
    # If False or None, the optional generate_from_seed field can be used.
    is_replicable: Optional[bool] = None
    # Optional seed for "Generate Scenario From Seed" — auto-fills all content
    # fields when provided.  Mutually exclusive with is_replicable=True.
    generate_from_seed: Optional[int] = None


@dataclass
class GenerateScenarioCardResponse:
    """Response DTO for GenerateScenarioCard use case.

    Fields match the production schema:
    - shapes dict contains deployment_shapes, objective_shapes, scenography_specs
    - objectives can be a string or dict with 'objective' and 'victory_points'
    - special_rules is a list of dicts (not a string)
    - card: The validated Card domain entity ready for persistence
    """

    card_id: str
    seed: int
    owner_id: str
    name: str
    mode: str
    table_mm: dict
    initial_priority: str
    visibility: str
    # Shape mapping: deployment_shapes, objective_shapes, scenography_specs
    shapes: dict
    card: Card  # Domain entity ready for persistence
    is_replicable: bool  # Whether scenario was generated as replicable
    table_preset: Optional[str] = None
    armies: Optional[str] = None
    layout: Optional[str] = None
    deployment: Optional[str] = None
    objectives: Optional[Union[str, dict]] = None
    special_rules: Optional[list[dict]] = None
    shared_with: Optional[list[str]] = None


# =============================================================================
# USE CASE
# =============================================================================
class GenerateScenarioCard:
    """Use case for generating a new scenario card."""

    def __init__(
        self,
        id_generator: IdGenerator,
        seed_generator: SeedGenerator,
        scenario_generator: ScenarioGenerator,
        card_repository: Optional[CardRepository] = None,
    ) -> None:
        self._id_generator = id_generator
        self._seed_generator = seed_generator
        self._scenario_generator = scenario_generator
        self._card_repository = card_repository

    # ── public seed resolution (repo-aware) ──────────────────────────────
    def resolve_seed_preview(self, seed: int) -> dict[str, str]:
        """Resolve text content fields from a seed (for Apply Seed / comparison).

        If a card with the given seed already exists in the repository,
        returns that card's text content fields (incl. name).
        Otherwise falls back to theme-based generation.
        """
        if seed <= 0:
            return {
                "armies": "",
                "deployment": "",
                "layout": "",
                "objectives": "",
                "initial_priority": "",
                "name": "",
            }
        # 1) Check existing cards
        if self._card_repository is not None:
            existing = self._card_repository.find_by_seed(seed)
            if existing is not None:
                return _card_to_preview(existing)
        # 2) Fall back to theme-based generation
        result = _resolve_seed_from_themes(seed)
        result["name"] = ""  # themes don't generate names
        return result

    def resolve_full_seed_scenario(
        self,
        seed: int,
        table_width: int,
        table_height: int,
    ) -> dict[str, Any]:
        """Resolve COMPLETE scenario data from a seed (repo-aware).

        If an existing card has this seed, replicates ALL card data:
        text fields, shapes, special_rules, VP objectives, name.

        Otherwise generates theme text + deterministic shapes.

        Returns dict with keys:
            armies, deployment, layout, objectives, initial_priority,
            name, special_rules, deployment_shapes, objective_shapes,
            scenography_specs
        """
        if seed <= 0:
            return {
                "armies": "",
                "deployment": "",
                "layout": "",
                "objectives": "",
                "initial_priority": "",
                "name": "",
                "special_rules": None,
                "deployment_shapes": [],
                "objective_shapes": [],
                "scenography_specs": [],
            }
        # 1) Check existing cards → replicate fully
        if self._card_repository is not None:
            existing = self._card_repository.find_by_seed(seed)
            if existing is not None:
                return _card_to_full_data(existing)
        # 2) Fall back to theme text + generated shapes
        text = _resolve_seed_from_themes(seed)
        shapes = _generate_seeded_shapes(seed, table_width, table_height)
        return {
            **text,
            "name": "",
            "special_rules": None,
            **shapes,
        }

    # ── helpers for execute() ────────────────────────────────────────────

    def _resolve_seed_value(
        self,
        request: GenerateScenarioCardRequest,
        table: TableSize,
        effective_is_replicable: bool,
    ) -> int:
        """Resolve the seed value from request parameters.

        Three cases:
        - generate_from_seed > 0 → keep or recalculate depending on content.
        - is_replicable + no gfs → hash-based or edit-mode seed.
        - Not replicable → 0.
        """
        if request.generate_from_seed and request.generate_from_seed > 0:
            original = self.resolve_seed_preview(request.generate_from_seed)
            content_unmodified = (
                (
                    _is_blank_text(request.armies)
                    or (request.armies or "").strip() == original["armies"]
                )
                and (
                    _is_blank_text(request.deployment)
                    or (request.deployment or "").strip() == original["deployment"]
                )
                and (
                    _is_blank_text(request.layout)
                    or (request.layout or "").strip() == original["layout"]
                )
                and _objectives_match_seed(request.objectives, original["objectives"])
                and (
                    _is_blank_text(request.initial_priority)
                    or (request.initial_priority or "").strip()
                    == original["initial_priority"]
                )
            )
            if content_unmodified:
                return request.generate_from_seed
            return int(
                calculate_seed_from_config(self._build_seed_config(request, table))
            )

        if effective_is_replicable:
            if request.seed and request.seed > 0:
                return request.seed
            return int(
                calculate_seed_from_config(self._build_seed_config(request, table))
            )

        return 0

    def _resolve_gfs_data(
        self,
        request: GenerateScenarioCardRequest,
        seed: int,
        table: TableSize,
    ) -> tuple[bool, dict[str, Any], dict[str, Any]]:
        """Resolve generate-from-seed data and seeded text content.

        Returns (using_gfs, full_seed_data, seeded_content).
        """
        using_gfs = bool(request.generate_from_seed and request.generate_from_seed > 0)
        full_seed_data: dict[str, Any] = {}
        existing_card: Optional[Card] = None
        if using_gfs:
            if self._card_repository is not None:
                existing_card = self._card_repository.find_by_seed(seed)
            if existing_card is not None:
                full_seed_data = _card_to_full_data(existing_card)
            else:
                text = _resolve_seed_from_themes(seed)
                shapes = _generate_seeded_shapes(seed, table.width_mm, table.height_mm)
                full_seed_data = {
                    **text,
                    "name": "",
                    "special_rules": None,
                    **shapes,
                }
        seeded_content = (
            _resolve_seeded_content(seed, request, existing_card) if seed > 0 else {}
        )
        return using_gfs, full_seed_data, seeded_content

    def execute(
        self, request: GenerateScenarioCardRequest
    ) -> GenerateScenarioCardResponse:
        """Execute the use case.

        Args:
            request: Request DTO with generation parameters.

        Returns:
            Response DTO with generated card data.

        Raises:
            ValidationError: If any input validation fails.
        """
        # 1) Validate actor_id
        actor_id = validate_actor_id(request.actor_id)

        # 2) Resolve table from preset (and custom dimensions if applicable)
        table = _resolve_table(
            request.table_preset,
            width_mm=request.table_width_mm,
            height_mm=request.table_height_mm,
        )

        # 3) Resolve seed
        effective_is_replicable = (
            request.is_replicable if request.is_replicable is not None else False
        )
        if not effective_is_replicable and request.generate_from_seed:
            raise ValidationError(
                "Cannot use 'Generate Scenario From Seed' when "
                "'Replicable Scenario' is disabled. "
                "Enable 'Replicable Scenario' to use a seed."
            )
        seed = self._resolve_seed_value(request, table, effective_is_replicable)

        # 4) Resolve mode
        mode = self._resolve_mode(request.mode)

        # 5) Resolve visibility
        visibility = self._resolve_visibility(request.visibility)

        # 5b) Resolve seeded content fields + shapes + secondary data.
        using_gfs, full_seed_data, seeded_content = self._resolve_gfs_data(
            request, seed, table
        )
        final_armies = seeded_content.get("armies", request.armies)
        final_deployment = seeded_content.get("deployment", request.deployment)
        final_layout = seeded_content.get("layout", request.layout)
        final_objectives = seeded_content.get("objectives", request.objectives)
        final_initial_priority = seeded_content.get(
            "initial_priority", request.initial_priority
        )

        # 5a) Validate content fields
        validate_objectives(final_objectives)
        validate_special_rules(
            request.special_rules
            if not isinstance(request.special_rules, str)
            else None
        )
        validate_shared_with_visibility(visibility, request.shared_with)

        # 6) Resolve shapes: user-provided shapes take priority.
        #    When generate_from_seed is active and user has no shapes,
        #    auto-fill from seed (existing card or deterministic generation).
        has_user_scenography = bool(request.scenography_specs or request.map_specs)
        has_user_deployment = bool(request.deployment_shapes)
        has_user_objectives = bool(request.objective_shapes)

        if using_gfs and not has_user_scenography:
            final_scenography = full_seed_data.get("scenography_specs", [])
        else:
            final_scenography = request.scenography_specs or request.map_specs or []

        if using_gfs and not has_user_deployment:
            final_deployment_shapes = full_seed_data.get("deployment_shapes")
        else:
            final_deployment_shapes = request.deployment_shapes

        if using_gfs and not has_user_objectives:
            final_objective_shapes = full_seed_data.get("objective_shapes")
        else:
            final_objective_shapes = request.objective_shapes

        # 7) Validate shapes with domain MapSpec (all shape categories)
        map_spec = MapSpec(
            table=table,
            shapes=final_scenography,
            objective_shapes=final_objective_shapes,
            deployment_shapes=final_deployment_shapes,
        )

        # 8) Use provided card_id or generate a new one
        card_id = request.card_id or self._id_generator.generate_card_id()

        # 8a) Resolve name: user-provided → seed name → auto-generated
        seed_name = full_seed_data.get("name", "") if using_gfs else ""
        if request.name and request.name.strip():
            name = request.name.strip()
        elif seed_name:
            name = seed_name
        else:
            name = self._generate_card_name(final_layout, final_deployment)

        # 8b) Resolve special_rules: user-provided → seed → None
        if request.special_rules:
            final_special_rules = self._resolve_special_rules(request.special_rules)
        elif using_gfs and full_seed_data.get("special_rules"):
            final_special_rules = full_seed_data["special_rules"]
        else:
            final_special_rules = None
        final_shared_with = list(request.shared_with) if request.shared_with else None

        # 9) Construct Card to validate invariants (now includes content fields)
        card = Card(
            card_id=card_id,
            owner_id=actor_id,
            visibility=visibility,
            shared_with=final_shared_with,
            mode=mode,
            seed=seed,
            table=table,
            map_spec=map_spec,
            name=name,
            armies=final_armies,
            deployment=final_deployment,
            layout=final_layout,
            objectives=final_objectives,
            initial_priority=final_initial_priority
            or "Check the rulebook rules for it",
            special_rules=final_special_rules,
        )

        # 10) Build response DTO
        return self._build_response(
            card_id=card_id,
            owner_id=actor_id,
            seed=seed,
            mode=mode,
            visibility=visibility,
            table=table,
            card=card,
            request=request,
        )

    def _build_response(
        self,
        card_id: str,
        owner_id: str,
        seed: int,
        mode: GameMode,
        visibility: Visibility,
        table: TableSize,
        card: Card,
        request: GenerateScenarioCardRequest,
    ) -> GenerateScenarioCardResponse:
        """Build response DTO from components.

        Returns structure with shapes as nested dict containing:
        - deployment_shapes
        - objective_shapes
        - scenography_specs
        - card: validated Card domain entity ready for persistence
        """
        # Name is already in the Card object
        name = card.name or ""
        priority = card.initial_priority or "Check the rulebook rules for it"
        final_shapes = self._resolve_final_shapes(card)
        final_special_rules = card.special_rules  # Use card's resolved rules
        final_shared_with = list(request.shared_with) if request.shared_with else []

        return GenerateScenarioCardResponse(
            card_id=card_id,
            seed=seed,
            owner_id=owner_id,
            name=name,
            mode=mode.value,
            table_mm={"width_mm": table.width_mm, "height_mm": table.height_mm},
            initial_priority=priority,
            visibility=visibility.value,
            shapes=final_shapes,
            card=card,
            is_replicable=request.is_replicable or False,  # Default to False if None
            table_preset=request.table_preset,
            armies=card.armies,
            layout=card.layout,
            deployment=card.deployment,
            objectives=card.objectives,
            special_rules=final_special_rules,
            shared_with=final_shared_with,
        )

    def _resolve_final_shapes(self, card: Card) -> dict:
        """Resolve and validate final shape lists from card's map_spec.

        The card's map_spec already contains the merged shapes from:
        - Generated shapes (if seed >= 1 and user provided no manual shapes)
        - User-provided shapes (if provided)
        - Empty shapes (if seed == 0, manual scenario)
        """
        return {
            "deployment_shapes": card.map_spec.deployment_shapes or [],
            "objective_shapes": card.map_spec.objective_shapes or [],
            "scenography_specs": card.map_spec.shapes or [],
        }

    @staticmethod
    def _resolve_special_rules(
        special_rules: Optional[Union[str, list[dict]]],
    ) -> Optional[list[dict]]:
        """Parse special_rules to list[dict] format."""
        if not special_rules:
            return None
        if isinstance(special_rules, list):
            return special_rules
        if isinstance(special_rules, str):
            return [{"name": "Custom Rule", "description": special_rules}]
        return None

    def _resolve_name(
        self,
        provided_name: Optional[str],
        layout: Optional[str],
        deployment: Optional[str],
    ) -> str:
        """Resolve card name from provided name or layout/deployment."""
        if provided_name and provided_name.strip():
            return provided_name.strip()
        return self._generate_card_name(layout, deployment)

    def _generate_card_name(
        self, layout: Optional[str], deployment: Optional[str]
    ) -> str:
        """Generate a descriptive card name from layout and deployment."""
        if layout and deployment or layout:
            return f"Battle for {layout}"
        elif deployment:
            return f"Battle with {deployment}"
        else:
            return "Battle Scenario"

    def _build_seed_config(
        self, request: GenerateScenarioCardRequest, table: TableSize
    ) -> dict[str, Any]:
        """Build configuration dict for deterministic seed calculation.

        Only includes fields that define the scenario's configuration.
        Excludes transient fields like card_id, name, shared_with, etc.

        CRITICAL: Must use resolved table dimensions (not request params) to match
        preview calculation which always uses real dimensions.

        Returns:
            Dict containing scenario definition fields for hashing.
        """
        scenography_specs = request.scenography_specs or request.map_specs or []
        deployment_shapes = request.deployment_shapes or []
        objective_shapes = request.objective_shapes or []

        return {
            "mode": (
                request.mode.value
                if isinstance(request.mode, GameMode)
                else request.mode
            ),
            "table_preset": request.table_preset,
            "table_width_mm": table.width_mm,  # Use resolved dimensions
            "table_height_mm": table.height_mm,  # Use resolved dimensions
            "armies": request.armies,
            "deployment": request.deployment,
            "layout": request.layout,
            "objectives": request.objectives,
            "initial_priority": request.initial_priority,
            "special_rules": request.special_rules,
            "deployment_shapes": deployment_shapes,
            "objective_shapes": objective_shapes,
            "scenography_specs": scenography_specs,
        }

    def _resolve_mode(self, mode: Union[str, GameMode]) -> GameMode:
        """Resolve mode to GameMode enum."""
        if isinstance(mode, GameMode):
            return mode
        return parse_game_mode(mode)

    def _resolve_visibility(
        self, visibility: Optional[Union[str, Visibility]]
    ) -> Visibility:
        """Resolve visibility to Visibility enum, defaulting to PRIVATE."""
        if visibility is None:
            return Visibility.PRIVATE
        if isinstance(visibility, Visibility):
            return visibility
        return parse_visibility(visibility)
