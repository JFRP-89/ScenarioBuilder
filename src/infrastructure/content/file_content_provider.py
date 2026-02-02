from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, cast

from domain.cards.models import CardItem

DEFAULT_BASE_PATH = "content/mesbg"
ENCODING_UTF8 = "utf-8"

FILE_LAYOUTS = "layouts.json"
FILE_DEPLOYMENTS = "deployments.json"
FILE_OBJECTIVES = "objectives.json"
FILE_TWISTS = "twists.json"
FILE_STORY_HOOKS = "story_hooks.json"
FILE_CONSTRAINTS = "constraints.json"


class FileContentProvider:
    def __init__(self, base_path: str = DEFAULT_BASE_PATH) -> None:
        self.base_path = Path(base_path)

    def _path_for(self, name: str) -> Path:
        return self.base_path / name

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]], json.loads(path.read_text(encoding=ENCODING_UTF8))
        )

    def _parse_items(self, data: list[dict[str, Any]]) -> Iterable[CardItem]:
        return [CardItem(**item) for item in data]

    def _load(self, name: str) -> Iterable[CardItem]:
        data = self._read_json(self._path_for(name))
        return self._parse_items(data)

    def get_layouts(self):
        return self._load(FILE_LAYOUTS)

    def get_deployments(self):
        return self._load(FILE_DEPLOYMENTS)

    def get_objectives(self):
        return self._load(FILE_OBJECTIVES)

    def get_twists(self):
        return self._load(FILE_TWISTS)

    def get_story_hooks(self):
        return self._load(FILE_STORY_HOOKS)

    def get_constraints(self):
        return self._load(FILE_CONSTRAINTS)
