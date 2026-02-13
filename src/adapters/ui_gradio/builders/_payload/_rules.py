"""Special-rules helpers for payload construction.

Pure functions — no side effects, no UI dependencies.
"""

from __future__ import annotations

from typing import Any

from adapters.ui_gradio.ui_types import ErrorDict, SpecialRuleItem


def apply_special_rules(
    payload: dict[str, Any],
    rules_state: list[SpecialRuleItem],
) -> ErrorDict | None:
    """Validate and add special_rules to payload.

    Args:
        payload: Request payload (modified in-place)
        rules_state: Rules state list with name, rule_type, value

    Returns:
        Error dict if validation fails, None otherwise
    """
    if not rules_state:
        return None

    normalized = []
    for idx, rule in enumerate(rules_state, 1):
        name = str(rule.get("name", "")).strip()
        rule_type = str(rule.get("rule_type", "")).strip()
        value = str(rule.get("value", "")).strip()

        if not name:
            return {"status": "error", "message": f"Rule {idx}: Name is required"}
        if not rule_type or rule_type not in ("description", "source"):
            return {
                "status": "error",
                "message": f"Rule {idx}: Must specify description or source",
            }
        if not value:
            return {"status": "error", "message": f"Rule {idx}: Value cannot be empty"}

        normalized_rule: dict[str, str] = {"name": name}
        if rule_type == "description":
            normalized_rule["description"] = value
        else:
            normalized_rule["source"] = value

        normalized.append(normalized_rule)

    payload["special_rules"] = normalized
    return None
