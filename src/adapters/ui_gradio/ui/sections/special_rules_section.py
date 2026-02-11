"""Special rules section."""

from typing import Any

import gradio as gr


def build_special_rules_section() -> (
    tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]
):
    """Build special rules builder UI components.

    Returns:
        Tuple of (special_rules_state, special_rules_toggle, rules_group,
                 rule_type_radio, rule_name_input, rule_value_input,
                 add_rule_btn, remove_rule_btn, rules_list, remove_selected_rule_btn,
                 rule_name_state, rule_value_state)
    """
    # Toggle for Special Rules section
    with gr.Row():
        special_rules_toggle = gr.Checkbox(
            label="Add Special Rules",
            value=False,
            elem_id="special-rules-toggle",
        )

    # Special Rules section (collapsible)
    with gr.Group(visible=False) as rules_group:
        gr.Markdown("### Special Rules")
        gr.Markdown(
            "_Each rule has a **name** and either a **description** OR a **source**._"
        )

        special_rules_state = gr.State([])
        rule_name_state = gr.State("")
        rule_value_state = gr.State("")

        with gr.Row():
            rule_type_radio = gr.Radio(
                choices=["description", "source"],
                value="description",
                label="Rule Type",
                elem_id="rule-type-radio",
            )

        with gr.Row():
            rule_name_input = gr.Textbox(
                label="Rule Name",
                placeholder="Enter rule name",
                elem_id="rule-name-input",
                interactive=True,
            )

        with gr.Row():
            rule_value_input = gr.Textbox(
                label="Rule Value",
                placeholder="Enter description or source",
                lines=2,
                elem_id="rule-value-input",
                interactive=True,
            )

        rule_editing_state = gr.State(None)

        with gr.Row():
            add_rule_btn = gr.Button("+ Add Rule", size="sm", elem_id="add-rule-btn")
            cancel_edit_rule_btn = gr.Button(
                "Cancel Edit", size="sm", visible=False, elem_id="cancel-edit-rule-btn"
            )
            remove_rule_btn = gr.Button(
                "- Remove Last", size="sm", elem_id="remove-rule-btn"
            )

        # Rule list display
        gr.Markdown("_Current Rules:_")
        rules_list = gr.Dropdown(
            choices=[],
            value=None,
            label="Rules",
            elem_id="rules-list",
            interactive=True,
            allow_custom_value=False,
        )
        remove_selected_rule_btn = gr.Button(
            "Remove Selected", size="sm", elem_id="remove-selected-rule-btn"
        )

    return (
        special_rules_state,
        special_rules_toggle,
        rules_group,
        rule_type_radio,
        rule_name_input,
        rule_value_input,
        add_rule_btn,
        remove_rule_btn,
        rules_list,
        remove_selected_rule_btn,
        rule_name_state,
        rule_value_state,
        rule_editing_state,
        cancel_edit_rule_btn,
    )
