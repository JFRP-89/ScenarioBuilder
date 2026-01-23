from __future__ import annotations

from src.infrastructure.config import get_env


class DemoCurrentUserProvider:
    def get_current_user_id(self) -> str:
        return get_env("DEMO_USER_ID", "demo-user") or "demo-user"
