"""Special rules state helpers."""

from __future__ import annotations

import uuid
from typing import Any


def add_special_rule(
    current_state: list[dict[str, Any]],
    rule_type: str = "description",
) -> list[dict[str, Any]]:
    """Add a new empty rule to the state.

    Args:
        current_state: Current rules state.
        rule_type: Type of rule (description or source).

    Returns:
        Updated rules state.
    """
    new_rule = {
        "id": str(uuid.uuid4())[:8],
        "name": "New Rule",
        "rule_type": rule_type,
        "value": "",
    }
    return [*current_state, new_rule]


def remove_last_special_rule(
    current_state: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove the last rule from the state."""
    if not current_state:
        return []
    return current_state[:-1]


def remove_selected_special_rule(
    current_state: list[dict[str, Any]], rule_id: str
) -> list[dict[str, Any]]:
    """Remove selected rule from state."""
    return [rule for rule in current_state if rule.get("id") != rule_id]


def get_special_rules_choices(
    state: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Get dropdown choices from special rules state."""
    if not state:
        return []
    return [(f"{rule['name']} ({rule['rule_type']})", rule["id"]) for rule in state]


def update_special_rule(
    current_state: list[dict[str, Any]],
    rule_id: str,
    name: str,
    rule_type: str,
    value: str,
) -> list[dict[str, Any]]:
    """Update an existing special rule in place."""
    return [
        (
            {**rule, "name": name, "rule_type": rule_type, "value": value}
            if rule["id"] == rule_id
            else rule
        )
        for rule in current_state
    ]
