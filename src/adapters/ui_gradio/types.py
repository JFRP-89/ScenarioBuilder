"""Compatibility shim to avoid shadowing stdlib types.

This module previously held UI TypedDicts. Keeping it prevents breaking
older imports while ensuring stdlib ``types`` stays available when running
``app.py`` directly (its directory is inserted into sys.path).
"""

from __future__ import annotations

import importlib.util
import os
import sys

_STDLIB_TYPES_PATH = os.path.join(os.path.dirname(os.__file__), "types.py")
_spec = importlib.util.spec_from_file_location("_stdlib_types", _STDLIB_TYPES_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError("Unable to load stdlib types module")

_stdlib_types = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_stdlib_types)

# Populate this module with stdlib types attributes.
globals().update(_stdlib_types.__dict__)
sys.modules["types"] = sys.modules[__name__]

# Re-export UI TypedDicts for backward compatibility.
from adapters.ui_gradio.ui_types import (  # noqa: E402
    DeploymentZoneData,
    DeploymentZoneItem,
    ErrorDict,
    HandlerUpdateDict,
    ObjectivePointItem,
    ScenographyCircleData,
    ScenographyItem,
    ScenographyPolygonData,
    ScenographyRectData,
    ScenographyShapeData,
    SpecialRuleItem,
    StatusDict,
    SuccessDict,
    VictoryPointItem,
)

__all__ = [
    "DeploymentZoneData",
    "DeploymentZoneItem",
    "ErrorDict",
    "HandlerUpdateDict",
    "ObjectivePointItem",
    "ScenographyCircleData",
    "ScenographyItem",
    "ScenographyPolygonData",
    "ScenographyRectData",
    "ScenographyShapeData",
    "SpecialRuleItem",
    "StatusDict",
    "SuccessDict",
    "VictoryPointItem",
]
