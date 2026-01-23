from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CardItem:
    id: str
    title: str
    description: str
    tags: List[str]
    modes: List[str]
    weights: Dict[str, int]
    risk_flags: List[str] = field(default_factory=list)
    map_spec: Optional[dict] = None


@dataclass(frozen=True)
class ScenarioCard:
    id: str
    mode: str
    seed: int
    layout: CardItem
    deployment: CardItem
    objective: CardItem
    twist: Optional[CardItem] = None
    story_hook: Optional[CardItem] = None
    constraints: List[CardItem] = field(default_factory=list)
    owner_id: str = ""
    visibility: str = "private"  # private | public
