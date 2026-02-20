"""Scenery theme catalogs for the BasicScenarioGenerator.

Each theme maps shape-type keys (``rect``, ``circle``, ``polygon``)
to lists of descriptive names used when generating random scenography.
"""

from __future__ import annotations

# =============================================================================
# Shared scenery names (extracted to satisfy DRY / no-duplicate-literals)
# =============================================================================
_BARRICADE = "Barricade"
_BROKEN_WALL = "Broken wall"
_CRUMBLING_WALL = "Crumbling wall"
_DEBRIS_FIELD = "Debris field"
_DIFFICULT_TERRAIN = "Difficult terrain"
_FOUNTAIN = "Fountain"
_MEETING_CIRCLE = "Meeting circle"
_PAVED_SQUARE = "Paved square"
_ROCKY_GROUND = "Rocky ground"
_RUBBLE_FIELD = "Rubble field"
_SACRED_GROVE = "Sacred grove"
_SIGNAL_FIRE = "Signal fire"
_SUPPLY_DEPOT = "Supply depot"
_WELL = "Well"
_WOODEN_PALISADE = "Wooden palisade"

SCENERY_THEMES: dict[str, dict[str, list[str]]] = {
    "urban": {
        "rect": [
            "Low ruins",
            "Stone wall",
            "Collapsed building",
            _BARRICADE,
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
            _RUBBLE_FIELD,
            "Collapsed plaza",
            "Broken pavement",
            "Urban debris",
            "Construction site",
        ],
    },
    "forest": {
        "rect": [
            "Hunting lodge",
            _WOODEN_PALISADE,
            "Abandoned cabin",
            "Rangers outpost",
            "Fallen log pile",
        ],
        "circle": [
            "Dense woods",
            _SACRED_GROVE,
            "Thicket",
            "Mossy clearing",
            "Ancient tree ring",
        ],
        "polygon": [
            _ROCKY_GROUND,
            "Marshland",
            _DIFFICULT_TERRAIN,
            "Thorny brush",
            "Wetland",
        ],
    },
    "desert": {
        "rect": [
            "Broken outpost",
            "Sandbag line",
            _CRUMBLING_WALL,
            _SUPPLY_DEPOT,
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
            _WELL,
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
            _WOODEN_PALISADE,
            "Horse stables",
            "Watch hut",
            "Supply wagons",
        ],
        "circle": [
            "Bonfire pit",
            "Horse corral",
            "Grass ring",
            "Training circle",
            _MEETING_CIRCLE,
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
            _BROKEN_WALL,
            _SUPPLY_DEPOT,
            _BARRICADE,
        ],
        "circle": [
            _SIGNAL_FIRE,
            _FOUNTAIN,
            "Statue base",
            _WELL,
            "Courtyard",
        ],
        "polygon": [
            "Battle debris",
            "Broken causeway",
            _RUBBLE_FIELD,
            _PAVED_SQUARE,
            "Collapsed arch",
        ],
    },
    "minas_tirith": {
        "rect": [
            "White wall",
            "Guardhouse",
            "Gatehouse ruins",
            "Supply crates",
            _BARRICADE,
        ],
        "circle": [
            _FOUNTAIN,
            "Tower base",
            "Beacon brazier",
            "Courtyard",
            "Statue plinth",
        ],
        "polygon": [
            "Broken stairs",
            _RUBBLE_FIELD,
            "Collapsed terrace",
            _PAVED_SQUARE,
            "Shattered arch",
        ],
    },
    "osgiliath": {
        "rect": [
            "Broken bridge",
            "Collapsed hall",
            _CRUMBLING_WALL,
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
            _DEBRIS_FIELD,
        ],
    },
    "helms_deep": {
        "rect": [
            "Fortified wall",
            "Gatehouse",
            "Supply crates",
            _BARRICADE,
            "Siege debris",
        ],
        "circle": [
            "Culvert",
            _SIGNAL_FIRE,
            _WELL,
            "Guard circle",
            "Training ring",
        ],
        "polygon": [
            "Rocky slope",
            "Broken ramp",
            _DEBRIS_FIELD,
            "Rubble heap",
            "Stony ground",
        ],
    },
    "isengard": {
        "rect": [
            "Forge platform",
            "Wooden stockade",
            "Steel scaffolds",
            _SUPPLY_DEPOT,
            "Barracks",
        ],
        "circle": [
            "Blast pit",
            "Water pool",
            "Engine base",
            _SIGNAL_FIRE,
            "Machinery ring",
        ],
        "polygon": [
            "Industrial debris",
            "Ashen ground",
            "Scrap heap",
            "Broken track",
            _RUBBLE_FIELD,
        ],
    },
    "mordor": {
        "rect": [
            "Dark watchtower",
            "Spiked palisade",
            _BROKEN_WALL,
            "Supply pens",
            "Slave pens",
        ],
        "circle": [
            "Lava pit",
            "Ash crater",
            "Dark well",
            _SIGNAL_FIRE,
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
            _CRUMBLING_WALL,
            "Ancient dais",
            "Broken gate",
        ],
        "circle": [
            _WELL,
            "Chasm edge",
            "Rune circle",
            "Collapsed dome",
            "Deep pit",
        ],
        "polygon": [
            _RUBBLE_FIELD,
            "Broken walkway",
            _ROCKY_GROUND,
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
            _SACRED_GROVE,
            _FOUNTAIN,
            "Sunwell",
            _MEETING_CIRCLE,
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
            _SACRED_GROVE,
            "Moonlit pool",
            "Tree ring",
            "Glade",
            "Shrine",
        ],
        "polygon": [
            "Leafy ground",
            "Mossy field",
            "Shaded glade",
            _DIFFICULT_TERRAIN,
            "Fallen leaves",
        ],
    },
    "mirkwood": {
        "rect": [
            "Webbed ruins",
            "Fallen tree",
            _WOODEN_PALISADE,
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
            _DIFFICULT_TERRAIN,
            _ROCKY_GROUND,
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
            _MEETING_CIRCLE,
            "Ring of stones",
        ],
        "polygon": [
            _ROCKY_GROUND,
            "Thorny brush",
            _DIFFICULT_TERRAIN,
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
            _WELL,
        ],
        "polygon": [
            "Broken walkway",
            _RUBBLE_FIELD,
            "Stone floor",
            "Collapsed stair",
            "Debris pile",
        ],
    },
    "dale": {
        "rect": [
            "Market stall",
            "Trade post",
            _BROKEN_WALL,
            "Guardhouse",
            _BARRICADE,
        ],
        "circle": [
            "Town square",
            _FOUNTAIN,
            _WELL,
            _SIGNAL_FIRE,
            _MEETING_CIRCLE,
        ],
        "polygon": [
            _PAVED_SQUARE,
            _RUBBLE_FIELD,
            "Broken street",
            "Collapsed plaza",
            _DEBRIS_FIELD,
        ],
    },
}
