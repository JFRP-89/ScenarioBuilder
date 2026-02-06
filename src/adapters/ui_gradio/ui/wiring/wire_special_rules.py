"""Special-rules section event wiring."""

from __future__ import annotations

import uuid
from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.state_helpers import (
    get_special_rules_choices,
    remove_last_special_rule,
    remove_selected_special_rule,
)


def wire_special_rules(
    *,
    special_rules_state: gr.State,
    special_rules_toggle: gr.Checkbox,
    rules_group: gr.Group,
    rule_type_radio: gr.Radio,
    rule_name_input: gr.Textbox,
    rule_value_input: gr.Textbox,
    add_rule_btn: gr.Button,
    remove_rule_btn: gr.Button,
    rules_list: gr.Dropdown,
    remove_selected_rule_btn: gr.Button,
    output: gr.JSON,
) -> None:
    """Wire special-rules add/remove/toggle events."""

    # -- closures ----------------------------------------------------------

    def _add_special_rule_wrapper(
        current_state: list[dict[str, Any]],
        rule_type: str,
        name_input_val: str,
        value_input_val: str,
    ) -> dict[Any, Any]:
        name_stripped = (name_input_val or "").strip()
        value_stripped = (value_input_val or "").strip()
        if not name_stripped or not value_stripped:
            if not name_stripped and not value_stripped:
                error_msg = "Special Rule requires both Name and Value to be filled."
            elif not name_stripped:
                error_msg = "Special Rule requires Name to be filled."
            else:
                error_msg = "Special Rule requires Value to be filled."
            return {
                special_rules_state: current_state,
                rules_list: gr.update(),
                rule_name_input: name_input_val,
                rule_value_input: value_input_val,
                output: {"status": "error", "message": error_msg},
            }
        new_rule = {
            "id": str(uuid.uuid4())[:8],
            "name": name_stripped,
            "rule_type": rule_type,
            "value": value_stripped,
        }
        new_state = [*current_state, new_rule]
        choices = get_special_rules_choices(new_state)
        return {
            special_rules_state: new_state,
            rules_list: gr.update(choices=choices),
            rule_name_input: "",
            rule_value_input: "",
            output: {"status": "success"},
        }

    def _remove_last_special_rule_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_special_rule(current_state)
        choices = get_special_rules_choices(new_state)
        return {
            special_rules_state: new_state,
            rules_list: gr.update(choices=choices),
        }

    def _remove_selected_special_rule_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                special_rules_state: current_state,
                rules_list: gr.update(),
            }
        new_state = remove_selected_special_rule(current_state, selected_id)
        choices = get_special_rules_choices(new_state)
        return {
            special_rules_state: new_state,
            rules_list: gr.update(choices=choices),
        }

    def _toggle_special_rules_section(enabled: bool) -> dict[Any, Any]:
        result: dict[str, dict[str, Any]] = handlers.toggle_special_rules_section(
            enabled
        )
        return result

    # -- bindings ----------------------------------------------------------

    add_rule_btn.click(
        fn=_add_special_rule_wrapper,
        inputs=[
            special_rules_state,
            rule_type_radio,
            rule_name_input,
            rule_value_input,
        ],
        outputs=[
            special_rules_state,
            rules_list,
            rule_name_input,
            rule_value_input,
            output,
        ],
    )
    remove_rule_btn.click(
        fn=_remove_last_special_rule_wrapper,
        inputs=[special_rules_state],
        outputs=[special_rules_state, rules_list],
    )
    remove_selected_rule_btn.click(
        fn=_remove_selected_special_rule_wrapper,
        inputs=[rules_list, special_rules_state],
        outputs=[special_rules_state, rules_list],
    )
    special_rules_toggle.change(
        fn=_toggle_special_rules_section,
        inputs=[special_rules_toggle],
        outputs=[rules_group],
    )
