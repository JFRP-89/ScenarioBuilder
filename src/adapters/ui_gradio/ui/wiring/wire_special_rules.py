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


def _short_id() -> str:
    """Return a short random identifier."""
    return str(uuid.uuid4())[:8]


_BTN_ADD_RULE = "+ Add Rule"


def _validate_rule_inputs(name_raw: str, value_raw: str) -> str | None:
    """Return an error message when either input is empty, else ``None``."""
    name_ok = bool(name_raw and name_raw.strip())
    value_ok = bool(value_raw and value_raw.strip())
    if name_ok and value_ok:
        return None
    if not name_ok and not value_ok:
        return "Special Rule requires both Name and Value to be filled."
    if not name_ok:
        return "Special Rule requires Name to be filled."
    return "Special Rule requires Value to be filled."


def _make_rule_reset(
    rule_widgets: dict[str, Any],
    *,
    choices: list[tuple[str, str]] | None = None,
) -> dict[Any, Any]:
    """Build the 'reset form' widget dict used after add/remove/cancel."""
    result: dict[Any, Any] = {
        rule_widgets["editing_state"]: None,
        rule_widgets["add_btn"]: gr.update(value=_BTN_ADD_RULE),
        rule_widgets["cancel_btn"]: gr.update(visible=False),
        rule_widgets["name_input"]: gr.update(value=""),
        rule_widgets["value_input"]: gr.update(value=""),
    }
    if choices is not None:
        result[rule_widgets["rules_list"]] = gr.update(choices=choices, value=None)
    return result


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

    # Widget-ref map used by module-level helpers
    _rw: dict[str, Any] = {
        "editing_state": rule_editing_state,
        "add_btn": add_rule_btn,
        "cancel_btn": cancel_edit_rule_btn,
        "name_input": rule_name_input,
        "value_input": rule_value_input,
        "rules_list": rules_list,
    }

    # -- closures ----------------------------------------------------------

    def _on_rule_selected(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        """Populate form when a rule is selected from dropdown."""
        if not selected_id:
            reset = _make_rule_reset(_rw)
            reset[rule_type_radio] = gr.update(value="description")
            return reset
        rule = next((r for r in current_state if r["id"] == selected_id), None)
        if not rule:
            return {
                rule_editing_state: None,
                rule_name_input: gr.update(),
                rule_value_input: gr.update(),
                rule_type_radio: gr.update(),
                add_rule_btn: gr.update(value=_BTN_ADD_RULE),
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
        reset = _make_rule_reset(_rw)
        reset[rule_type_radio] = gr.update(value="description")
        reset[rules_list] = gr.update(value=None)
        return reset

    def _add_or_update_special_rule_wrapper(
        current_state: list[dict[str, Any]],
        rule_type: str,
        name_input_val: str,
        value_input_val: str,
        editing_id: str | None,
    ) -> dict[Any, Any]:
        error_msg = _validate_rule_inputs(name_input_val, value_input_val)
        if error_msg:
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

        name_stripped = (name_input_val or "").strip()
        value_stripped = (value_input_val or "").strip()

        if editing_id:
            new_state = update_special_rule(
                current_state, editing_id, name_stripped, rule_type, value_stripped
            )
        else:
            new_rule = {
                "id": _short_id(),
                "name": name_stripped,
                "rule_type": rule_type,
                "value": value_stripped,
            }
            new_state = [*current_state, new_rule]

        choices = get_special_rules_choices(new_state)
        reset = _make_rule_reset(_rw, choices=choices)
        reset[special_rules_state] = new_state
        reset[output] = {"status": "success"}
        return reset

    def _remove_last_special_rule_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_special_rule(current_state)
        choices = get_special_rules_choices(new_state)
        reset = _make_rule_reset(_rw, choices=choices)
        reset[special_rules_state] = new_state
        return reset

    def _remove_selected_special_rule_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            reset = _make_rule_reset(_rw)
            reset[special_rules_state] = current_state
            reset[rules_list] = gr.update()
            return reset
        new_state = remove_selected_special_rule(current_state, selected_id)
        choices = get_special_rules_choices(new_state)
        reset = _make_rule_reset(_rw, choices=choices)
        reset[special_rules_state] = new_state
        return reset

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
