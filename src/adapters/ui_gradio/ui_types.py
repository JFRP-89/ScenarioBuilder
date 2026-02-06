"""Type definitions for Gradio UI internal state and contracts.

These TypedDicts define the structure of internal state items used in the UI.
They are NOT used for API payloads (see domain models for that).
"""

from __future__ import annotations

from typing import Literal, TypedDict


# =============================================================================
# Special Rules
# =============================================================================
class SpecialRuleItem(TypedDict):
    """Special rule state item in UI."""

    id: str
    name: str
    rule_type: Literal["description", "source"]
    value: str


# =============================================================================
# Victory Points
# =============================================================================
class VictoryPointItem(TypedDict):
    """Victory point state item in UI."""

    id: str
    description: str


# =============================================================================
# Scenography Elements
# =============================================================================
class ScenographyCircleData(TypedDict):
    """Circle shape data."""

    type: Literal["circle"]
    cx: float
    cy: float
    radius: float
    description: str


class ScenographyRectData(TypedDict):
    """Rectangle shape data."""

    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float
    description: str


class ScenographyPolygonData(TypedDict):
    """Polygon shape data."""

    type: Literal["polygon"]
    points: list[list[float]]
    description: str


ScenographyShapeData = (
    ScenographyCircleData | ScenographyRectData | ScenographyPolygonData
)


class ScenographyItem(TypedDict):
    """Scenography element state item in UI."""

    id: str
    type: Literal["circle", "rect", "polygon"]
    label: str
    data: ScenographyShapeData
    allow_overlap: bool


# =============================================================================
# Deployment Zones
# =============================================================================
class DeploymentZoneData(TypedDict):
    """Deployment zone shape data."""

    type: Literal["deployment_zone"]
    description: str
    x: float
    y: float
    width: float
    height: float
    border: Literal["north", "south", "east", "west"]
    depth: float  # UI-only field
    separation: float  # UI-only field


class DeploymentZoneItem(TypedDict):
    """Deployment zone state item in UI."""

    id: str
    label: str
    data: DeploymentZoneData


# =============================================================================
# Objective Points
# =============================================================================
class ObjectivePointItem(TypedDict, total=False):
    """Objective point state item in UI.

    Uses total=False to make description optional.
    """

    id: str  # Required
    cx: float  # Required
    cy: float  # Required
    description: str  # Optional


# =============================================================================
# Handler return types
# =============================================================================
class HandlerUpdateDict(TypedDict, total=False):
    """Generic dict for handler returns that update multiple components.

    Keys are component names (as strings), values are gradio updates or state.
    """

    # This is intentionally flexible - handlers return dicts with various keys
    pass


class ErrorDict(TypedDict):
    """Error response dict."""

    status: Literal["error"]
    message: str


class SuccessDict(TypedDict):
    """Success response dict."""

    status: Literal["success"]


StatusDict = ErrorDict | SuccessDict
