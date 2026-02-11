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
    update_special_rule,
)


def wire_special_rules(  # noqa: C901
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
    rule_editing_state: gr.State,
    cancel_edit_rule_btn: gr.Button,
    output: gr.JSON,
) -> None:
    """Wire special-rules add/remove/toggle/edit events."""

    # -- closures ----------------------------------------------------------

    def _on_rule_selected(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        """Populate form when a rule is selected from dropdown."""
        if not selected_id:
            return {
                rule_name_input: gr.update(value=""),
                rule_value_input: gr.update(value=""),
                rule_type_radio: gr.update(value="description"),
                rule_editing_state: None,
                add_rule_btn: gr.update(value="+ Add Rule"),
                cancel_edit_rule_btn: gr.update(visible=False),
            }
        rule = next((r for r in current_state if r["id"] == selected_id), None)
        if not rule:
            return {
                rule_editing_state: None,
                rule_name_input: gr.update(),
                rule_value_input: gr.update(),
                rule_type_radio: gr.update(),
                add_rule_btn: gr.update(value="+ Add Rule"),
                cancel_edit_rule_btn: gr.update(visible=False),
            }
        return {
            rule_type_radio: gr.update(value=rule["rule_type"]),
            rule_name_input: gr.update(value=rule["name"]),
            rule_value_input: gr.update(value=rule["value"]),
            rule_editing_state: selected_id,
            add_rule_btn: gr.update(value="✏️ Update Rule"),
            cancel_edit_rule_btn: gr.update(visible=True),
        }

    def _cancel_edit_rule() -> dict[Any, Any]:
        """Cancel editing and return to add mode."""
        return {
            rule_name_input: gr.update(value=""),
            rule_value_input: gr.update(value=""),
            rule_type_radio: gr.update(value="description"),
            rule_editing_state: None,
            add_rule_btn: gr.update(value="+ Add Rule"),
            cancel_edit_rule_btn: gr.update(visible=False),
            rules_list: gr.update(value=None),
        }

    def _add_or_update_special_rule_wrapper(
        current_state: list[dict[str, Any]],
        rule_type: str,
        name_input_val: str,
        value_input_val: str,
        editing_id: str | None,
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
                rule_editing_state: editing_id,
                add_rule_btn: gr.update(),
                cancel_edit_rule_btn: gr.update(),
                output: {"status": "error", "message": error_msg},
            }

        if editing_id:
            # Update existing rule
            new_state = update_special_rule(
                current_state, editing_id, name_stripped, rule_type, value_stripped
            )
        else:
            # Add new rule
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
            rules_list: gr.update(choices=choices, value=None),
            rule_name_input: "",
            rule_value_input: "",
            rule_editing_state: None,
            add_rule_btn: gr.update(value="+ Add Rule"),
            cancel_edit_rule_btn: gr.update(visible=False),
            output: {"status": "success"},
        }

    def _remove_last_special_rule_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_special_rule(current_state)
        choices = get_special_rules_choices(new_state)
        return {
            special_rules_state: new_state,
            rules_list: gr.update(choices=choices, value=None),
            rule_editing_state: None,
            add_rule_btn: gr.update(value="+ Add Rule"),
            cancel_edit_rule_btn: gr.update(visible=False),
            rule_name_input: gr.update(value=""),
            rule_value_input: gr.update(value=""),
        }

    def _remove_selected_special_rule_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                special_rules_state: current_state,
                rules_list: gr.update(),
                rule_editing_state: None,
                add_rule_btn: gr.update(value="+ Add Rule"),
                cancel_edit_rule_btn: gr.update(visible=False),
                rule_name_input: gr.update(value=""),
                rule_value_input: gr.update(value=""),
            }
        new_state = remove_selected_special_rule(current_state, selected_id)
        choices = get_special_rules_choices(new_state)
        return {
            special_rules_state: new_state,
            rules_list: gr.update(choices=choices, value=None),
            rule_editing_state: None,
            add_rule_btn: gr.update(value="+ Add Rule"),
            cancel_edit_rule_btn: gr.update(visible=False),
            rule_name_input: gr.update(value=""),
            rule_value_input: gr.update(value=""),
        }

    def _toggle_special_rules_section(enabled: bool) -> dict[Any, Any]:
        result: dict[str, dict[str, Any]] = handlers.toggle_special_rules_section(
            enabled
        )
        return result

    # -- bindings ----------------------------------------------------------

    _edit_outputs = [
        rule_name_input,
        rule_value_input,
        rule_type_radio,
        rule_editing_state,
        add_rule_btn,
        cancel_edit_rule_btn,
    ]

    rules_list.change(
        fn=_on_rule_selected,
        inputs=[rules_list, special_rules_state],
        outputs=_edit_outputs,
    )

    cancel_edit_rule_btn.click(
        fn=_cancel_edit_rule,
        inputs=[],
        outputs=[*_edit_outputs, rules_list],
    )

    _add_update_outputs = [
        special_rules_state,
        rules_list,
        rule_name_input,
        rule_value_input,
        rule_editing_state,
        add_rule_btn,
        cancel_edit_rule_btn,
        output,
    ]

    add_rule_btn.click(
        fn=_add_or_update_special_rule_wrapper,
        inputs=[
            special_rules_state,
            rule_type_radio,
            rule_name_input,
            rule_value_input,
            rule_editing_state,
        ],
        outputs=_add_update_outputs,
    )

    _remove_outputs = [
        special_rules_state,
        rules_list,
        rule_editing_state,
        add_rule_btn,
        cancel_edit_rule_btn,
        rule_name_input,
        rule_value_input,
    ]

    remove_rule_btn.click(
        fn=_remove_last_special_rule_wrapper,
        inputs=[special_rules_state],
        outputs=_remove_outputs,
    )
    remove_selected_rule_btn.click(
        fn=_remove_selected_special_rule_wrapper,
        inputs=[rules_list, special_rules_state],
        outputs=_remove_outputs,
    )
    special_rules_toggle.change(
        fn=_toggle_special_rules_section,
        inputs=[special_rules_toggle],
        outputs=[rules_group],
    )
