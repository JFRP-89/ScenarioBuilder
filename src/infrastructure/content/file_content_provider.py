from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from domain.cards.models import CardItem


class FileContentProvider:
    def __init__(self, base_path: str = "content/mesbg") -> None:
        self.base_path = Path(base_path)

    def _load(self, name: str) -> Iterable[CardItem]:
        data = json.loads((self.base_path / name).read_text(encoding="utf-8"))
        return [CardItem(**item) for item in data]

    def get_layouts(self):
        return self._load("layouts.json")

    def get_deployments(self):
        return self._load("deployments.json")

    def get_objectives(self):
        return self._load("objectives.json")

    def get_twists(self):
        return self._load("twists.json")

    def get_story_hooks(self):
        return self._load("story_hooks.json")

    def get_constraints(self):
        return self._load("constraints.json")
