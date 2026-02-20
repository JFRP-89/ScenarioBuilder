"""Theme data and seed-based content resolution.

Contains the static ``_CONTENT_THEMES`` catalog and deterministic
resolution helpers used by ``generate_scenario_card``.
"""

from __future__ import annotations

import random
from typing import Any

# =============================================================================
# Shared theme strings (extracted to satisfy DRY / no-duplicate-literals)
# =============================================================================
_HOLD_THE_PASS = "Hold the pass"
_BREAK_THE_LINE = "Break the line"
_HOLD_THE_GATE = "Hold the gate"
_SECURE_THE_RIDGE = "Secure the ridge"
_CAPTURE_THE_BANNER = "Capture the banner"
_FLANK_ASSAULT = "Flank assault"
_HOLD_THE_FORD = "Hold the ford"
_SKIRMISH_LINE = "Skirmish line"
_BROKEN_BRIDGE = "Broken Bridge"
_DELAY_THE_ENEMY = "Delay the enemy"
_HOLD_THE_BRIDGE = "Hold the bridge"
_RESCUE_THE_SCOUTS = "Rescue the scouts"
_SECURE_THE_RUINS = "Secure the ruins"
_SHIELDWALL = "Shieldwall"
_DELAY_THE_ASSAULT = "Delay the assault"
_DEFENSIVE_LINE = "Defensive line"
_ENCIRCLEMENT = "Encirclement"
_HIDDEN_RESERVE = "Hidden reserve"
_HOLD_THE_CLEARING = "Hold the clearing"
_HOLD_THE_GLADE = "Hold the glade"
_HOLD_THE_HARBOR = "Hold the harbor"
_HOLD_THE_HILL = "Hold the hill"
_HOLD_THE_OASIS = "Hold the oasis"
_PROTECT_THE_BANNER = "Protect the banner"
_PROTECT_THE_GATE = "Protect the gate"
_PROTECT_THE_GROVE = "Protect the grove"
_RAID_THE_CARAVAN = "Raid the caravan"
_SECURE_THE_BRIDGE = "Secure the bridge"
_SECURE_THE_FORGE = "Secure the forge"

# =============================================================================
# CONTENT THEMES (Middle-earth themed data catalogs)
# =============================================================================

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
            _SHIELDWALL,
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
            _BREAK_THE_LINE,
            _HOLD_THE_FORD,
            "Secure the hill",
            "Rescue the standard",
            "Drive back the raiders",
        ],
        "initial_priority": [
            "Control the ridgeline",
            "Protect the cavalry",
            _HOLD_THE_FORD,
            _DELAY_THE_ENEMY,
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
            _SHIELDWALL,
            "Guard the bridge",
            "Counterattack",
            _DEFENSIVE_LINE,
        ],
        "layout": [
            "Ruins of Osgiliath",
            "River Crossing",
            "Broken Causeway",
            "Gatehouse",
            "White City Outskirts",
        ],
        "objectives": [
            _HOLD_THE_BRIDGE,
            "Secure the causeway",
            "Protect the standard",
            "Relieve the garrison",
            "Push the line forward",
        ],
        "initial_priority": [
            _HOLD_THE_BRIDGE,
            "Protect the garrison",
            _SECURE_THE_RUINS,
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
            _HOLD_THE_GATE,
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
            _HOLD_THE_GATE,
            _PROTECT_THE_BANNER,
            "Secure the tower",
            _DELAY_THE_ASSAULT,
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
            _HOLD_THE_BRIDGE,
            _SKIRMISH_LINE,
            _FLANK_ASSAULT,
        ],
        "layout": [
            "Eastern Ruins",
            _BROKEN_BRIDGE,
            "Sunken Plaza",
            "Fallen Tower",
            "Riverbank",
        ],
        "objectives": [
            "Hold the crossing",
            _SECURE_THE_RUINS,
            "Rescue the wounded",
            "Control the plaza",
            "Push across the river",
        ],
        "initial_priority": [
            "Hold the crossing",
            _SECURE_THE_RUINS,
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
            _HOLD_THE_GATE,
            "Break the siege",
            "Rescue the defenders",
            "Secure the courtyard",
        ],
        "initial_priority": [
            "Hold the wall",
            _PROTECT_THE_GATE,
            "Secure the culvert",
            _DELAY_THE_ASSAULT,
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
            _FLANK_ASSAULT,
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
            _SECURE_THE_FORGE,
            _CAPTURE_THE_BANNER,
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
            _ENCIRCLEMENT,
            "Wave attack",
            _HOLD_THE_PASS,
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
            _HOLD_THE_PASS,
            "Seize the banner",
            "Burn the outpost",
            _SECURE_THE_RIDGE,
        ],
        "initial_priority": [
            _HOLD_THE_PASS,
            _BREAK_THE_LINE,
            _SECURE_THE_RIDGE,
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
            _BREAK_THE_LINE,
        ],
        "layout": [
            "Pillared Hall",
            _BROKEN_BRIDGE,
            "Deep Tunnel",
            "Collapsed Stair",
            "Dwarven Hall",
        ],
        "objectives": [
            "Secure the chamber",
            _HOLD_THE_BRIDGE,
            _RESCUE_THE_SCOUTS,
            "Claim the relic",
            "Drive out the foe",
        ],
        "initial_priority": [
            "Hold the hall",
            _SECURE_THE_BRIDGE,
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
            _DEFENSIVE_LINE,
            "Flank strike",
            _HOLD_THE_FORD,
            "Swift response",
            _HIDDEN_RESERVE,
        ],
        "layout": [
            "Hidden Valley",
            "River Crossing",
            "Elven Terrace",
            "Shaded Glade",
            _BROKEN_BRIDGE,
        ],
        "objectives": [
            "Protect the sanctuary",
            _HOLD_THE_FORD,
            "Secure the glade",
            "Rescue the envoy",
            "Drive the invaders",
        ],
        "initial_priority": [
            _HOLD_THE_FORD,
            "Protect the sanctuary",
            "Secure the glade",
            _DELAY_THE_ENEMY,
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
            _HOLD_THE_GLADE,
            "Flank in the trees",
            "Silent advance",
            _HIDDEN_RESERVE,
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
            _HOLD_THE_GLADE,
            "Secure the riverbank",
            _RESCUE_THE_SCOUTS,
            "Drive out the intruders",
        ],
        "initial_priority": [
            _HOLD_THE_GLADE,
            _PROTECT_THE_GROVE,
            "Secure the path",
            _DELAY_THE_ENEMY,
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
            _HOLD_THE_CLEARING,
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
            _HOLD_THE_CLEARING,
        ],
        "initial_priority": [
            "Secure the trail",
            "Clear the glade",
            _HOLD_THE_CLEARING,
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
            _HIDDEN_RESERVE,
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
            _PROTECT_THE_GROVE,
            "Hold the trail",
            _RESCUE_THE_SCOUTS,
            "Secure the clearing",
            "Drive out the intruders",
        ],
        "initial_priority": [
            "Hold the trail",
            _PROTECT_THE_GROVE,
            "Secure the clearing",
            _DELAY_THE_ENEMY,
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
            _HOLD_THE_PASS,
            "Ambush from above",
            _SKIRMISH_LINE,
            "Mountain defense",
            "Flank the ridge",
        ],
        "layout": [
            "High Pass",
            "Stone Ridge",
            _BROKEN_BRIDGE,
            "Mountain Lake",
            "Cliffside Trail",
        ],
        "objectives": [
            _HOLD_THE_PASS,
            _SECURE_THE_RIDGE,
            _RESCUE_THE_SCOUTS,
            "Claim the bridge",
            "Drive back the raiders",
        ],
        "initial_priority": [
            _HOLD_THE_PASS,
            _SECURE_THE_RIDGE,
            "Protect the scouts",
            _DELAY_THE_ASSAULT,
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
            _HOLD_THE_GATE,
            "Forge defense",
            _SHIELDWALL,
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
            _HOLD_THE_GATE,
            _SECURE_THE_FORGE,
            "Protect the vault",
            "Rescue the miners",
            "Drive out the foe",
        ],
        "initial_priority": [
            _HOLD_THE_GATE,
            "Protect the vault",
            _SECURE_THE_FORGE,
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
            _FLANK_ASSAULT,
            "Guard the market",
            _SKIRMISH_LINE,
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
            _SECURE_THE_BRIDGE,
            "Rescue the traders",
            _PROTECT_THE_GATE,
            "Drive off the raiders",
        ],
        "initial_priority": [
            "Hold the square",
            _PROTECT_THE_GATE,
            _SECURE_THE_BRIDGE,
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
            _FLANK_ASSAULT,
            _HOLD_THE_OASIS,
            _SKIRMISH_LINE,
            _RAID_THE_CARAVAN,
        ],
        "layout": [
            "Oasis Ridge",
            "Caravan Trail",
            "Scorched Dunes",
            "Salt Flats",
            "Broken Outpost",
        ],
        "objectives": [
            _HOLD_THE_OASIS,
            _RAID_THE_CARAVAN,
            _SECURE_THE_RIDGE,
            _CAPTURE_THE_BANNER,
            "Drive off the patrol",
        ],
        "initial_priority": [
            _HOLD_THE_OASIS,
            _SECURE_THE_RIDGE,
            _RAID_THE_CARAVAN,
            _BREAK_THE_LINE,
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
            _FLANK_ASSAULT,
            _HOLD_THE_HILL,
            _SKIRMISH_LINE,
            _ENCIRCLEMENT,
        ],
        "layout": [
            "Red Plain",
            "Steppe Ridge",
            "Broken Shrine",
            "Stone Circle",
            "Warded Camp",
        ],
        "objectives": [
            _HOLD_THE_HILL,
            "Secure the shrine",
            _CAPTURE_THE_BANNER,
            _BREAK_THE_LINE,
            "Drive back the enemy",
        ],
        "initial_priority": [
            _HOLD_THE_HILL,
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
            _HOLD_THE_HARBOR,
            _SHIELDWALL,
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
            _HOLD_THE_HARBOR,
            "Secure the sea gate",
            _PROTECT_THE_BANNER,
            "Control the docks",
            "Drive off the raiders",
        ],
        "initial_priority": [
            _HOLD_THE_HARBOR,
            "Secure the sea gate",
            "Control the docks",
            _PROTECT_THE_BANNER,
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
            _ENCIRCLEMENT,
            "Hold the ruin",
            "Night raid",
            _BREAK_THE_LINE,
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
            _HOLD_THE_PASS,
            _CAPTURE_THE_BANNER,
            "Crush the defenders",
            "Secure the road",
        ],
        "initial_priority": [
            _HOLD_THE_PASS,
            _SECURE_THE_RUINS,
            "Crush the line",
            _CAPTURE_THE_BANNER,
            "Control the road",
        ],
    },
}


# =============================================================================
# SHAPE DESCRIPTION CONSTANTS
# =============================================================================

DEPLOYMENT_DESCRIPTIONS = [
    "Vanguard deployment",
    "Flanking position",
    _DEFENSIVE_LINE,
    "Staging ground",
]

OBJECTIVE_DESCRIPTIONS = [
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

SCENOGRAPHY_DESCRIPTIONS_SOLID = [
    "Dense woodland",
    "Ruined building",
    "Rocky outcrop",
    "Stone wall",
    "Fortified tower",
    "Boulder field",
]

SCENOGRAPHY_DESCRIPTIONS_OVERLAP = [
    "Shallow marsh",
    "Light scrubland",
    "Rough ground",
    "Tall grass",
    "River ford",
    "Sandy dunes",
]


# =============================================================================
# SEED → THEME RESOLUTION
# =============================================================================


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


# =============================================================================
# FULL SEED DEFAULTS (mode + table + text + shapes)
# =============================================================================

_MODES = ["casual", "narrative", "matched"]
_TABLE_PRESETS = [
    ("standard", 1200, 1200),
    ("massive", 1800, 1200),
]


def _resolve_full_seed_defaults(seed: int) -> dict[str, Any]:
    """Deterministically derive **all** card config fields from a seed.

    Returns a dict matching the shape of ``_build_final_seed_config``
    so that ``calculate_seed_from_config(result)`` can be compared
    against the hash of user-submitted content to verify a seed match.

    Keys: mode, table_preset, table_width_mm, table_height_mm, armies,
    deployment, layout, objectives, initial_priority, special_rules,
    deployment_shapes, objective_shapes, scenography_specs.
    """
    from application.use_cases._generate._shape_generation import (
        _generate_seeded_shapes,
    )

    # Use a separate RNG namespace to avoid colliding with
    # _resolve_seed_from_themes (which also seeds with ``seed``).
    rng = random.Random(f"defaults-{seed}")  # nosec B311

    mode = rng.choice(_MODES)
    preset_name, tw, th = rng.choice(_TABLE_PRESETS)

    text = _resolve_seed_from_themes(seed)
    shapes = _generate_seeded_shapes(seed, tw, th)

    return {
        "mode": mode,
        "table_preset": preset_name,
        "table_width_mm": tw,
        "table_height_mm": th,
        **text,
        "special_rules": None,
        "deployment_shapes": shapes.get("deployment_shapes", []),
        "objective_shapes": shapes.get("objective_shapes", []),
        "scenography_specs": sorted(
            shapes.get("scenography_specs", []),
            key=lambda x: not x.get("allow_overlap", False),
        ),
    }
