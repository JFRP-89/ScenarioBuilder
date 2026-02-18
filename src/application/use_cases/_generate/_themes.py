"""Theme data and seed-based content resolution.

Contains the static ``_CONTENT_THEMES`` catalog and deterministic
resolution helpers used by ``generate_scenario_card``.
"""

from __future__ import annotations

import random

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


# =============================================================================
# SHAPE DESCRIPTION CONSTANTS
# =============================================================================

DEPLOYMENT_DESCRIPTIONS = [
    "Vanguard deployment",
    "Flanking position",
    "Defensive line",
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
