from __future__ import annotations

from typing import Protocol


class CurrentUserProvider(Protocol):
    def get_current_user_id(self) -> str: ...
