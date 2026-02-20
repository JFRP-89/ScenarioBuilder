"""Special rules add/remove handlers."""

from __future__ import annotations

import uuid
from typing import Any, Callable

import gradio as gr
from adapters.ui_gradio.ui_types import SpecialRuleItem


# =============================================================================
# Special Rules handlers
# =============================================================================
def add_special_rule(
    current_state: list[SpecialRuleItem],
    rule_type: str,
    name_input: str,
    value_input: str,
    get_choices_fn: Callable[[list[SpecialRuleItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Add special rule with validation.

    Args:
        current_state: Current rules state
        rule_type: Rule type (description or source)
        name_input: Rule name
        value_input: Rule value
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and UI updates
    """
    name_stripped = (name_input or "").strip()
    value_stripped = (value_input or "").strip()

    if not name_stripped or not value_stripped:
        if not name_stripped and not value_stripped:
            error_msg = "Special Rule requires both Name and Value to be filled."
        elif not name_stripped:
            error_msg = "Special Rule requires Name to be filled."
        else:
            error_msg = "Special Rule requires Value to be filled."

        return {
            "special_rules_state": current_state,
            "rules_list": gr.update(),
            "rule_name_input": name_input,
            "rule_value_input": value_input,
            "output": {"status": "error", "message": error_msg},
        }

    # Create rule with current input values
    new_rule = {
        "id": str(uuid.uuid4())[:8],
        "name": name_stripped,
        "rule_type": rule_type,
        "value": value_stripped,
    }
    new_state = [*current_state, new_rule]
    choices = get_choices_fn(new_state)  # type: ignore[arg-type]

    return {
        "special_rules_state": new_state,
        "rules_list": gr.update(choices=choices),
        "rule_name_input": "",
        "rule_value_input": "",
        "output": {"status": "success"},
    }


def remove_last_special_rule(
    current_state: list[SpecialRuleItem],
    remove_fn: Callable[[list[SpecialRuleItem]], list[SpecialRuleItem]],
    get_choices_fn: Callable[[list[SpecialRuleItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Remove last special rule.

    Args:
        current_state: Current rules state
        remove_fn: Function to remove last rule
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and choices
    """
    new_state = remove_fn(current_state)
    choices = get_choices_fn(new_state)
    return {
        "special_rules_state": new_state,
        "rules_list": gr.update(choices=choices),
    }


def remove_selected_special_rule(
    selected_id: str | None,
    current_state: list[SpecialRuleItem],
    remove_fn: Callable[[list[SpecialRuleItem], str], list[SpecialRuleItem]],
    get_choices_fn: Callable[[list[SpecialRuleItem]], list[tuple[str, str]]],
) -> dict[str, Any]:
    """Remove selected special rule.

    Args:
        selected_id: ID of rule to remove
        current_state: Current rules state
        remove_fn: Function to remove selected rule
        get_choices_fn: Function to get dropdown choices

    Returns:
        Dict with updated state and choices
    """
    if not selected_id:
        return {
            "special_rules_state": current_state,
            "rules_list": gr.update(),
        }
    new_state = remove_fn(current_state, selected_id)
    choices = get_choices_fn(new_state)
    return {
        "special_rules_state": new_state,
        "rules_list": gr.update(choices=choices),
    }
