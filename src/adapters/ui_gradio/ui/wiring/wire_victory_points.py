"""Victory-points section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.state_helpers import (
    add_victory_point,
    get_victory_points_choices,
    remove_last_victory_point,
    remove_selected_victory_point,
)


def wire_victory_points(
    *,
    objectives_with_vp_toggle: gr.Checkbox,
    vp_group: gr.Group,
    vp_state: gr.State,
    vp_input: gr.Textbox,
    add_vp_btn: gr.Button,
    remove_vp_btn: gr.Button,
    vp_list: gr.Dropdown,
    remove_selected_vp_btn: gr.Button,
) -> None:
    """Wire victory-point toggle/add/remove events."""

    # -- closures ----------------------------------------------------------

    def _toggle_vp_section(enabled: bool) -> Any:
        return handlers.toggle_vp_section(enabled)

    def _add_vp_wrapper(
        current_state: list[dict[str, Any]], description: str
    ) -> dict[Any, Any]:
        desc = description.strip()
        if not desc:
            return {
                vp_state: current_state,
                vp_list: gr.update(),
                vp_input: gr.update(value=""),
            }
        new_state = add_victory_point(current_state)
        new_state[-1]["description"] = desc
        choices = get_victory_points_choices(new_state)
        return {
            vp_state: new_state,
            vp_list: gr.update(choices=choices),
            vp_input: gr.update(value=""),
        }

    def _remove_last_vp_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_victory_point(current_state)
        choices = get_victory_points_choices(new_state)
        return {
            vp_state: new_state,
            vp_list: gr.update(choices=choices),
        }

    def _remove_selected_vp_wrapper(
        selected_id: str, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {vp_state: current_state, vp_list: gr.update()}
        new_state = remove_selected_victory_point(current_state, selected_id)
        choices = get_victory_points_choices(new_state)
        return {
            vp_state: new_state,
            vp_list: gr.update(choices=choices),
        }

    # -- bindings ----------------------------------------------------------

    objectives_with_vp_toggle.change(
        fn=_toggle_vp_section,
        inputs=[objectives_with_vp_toggle],
        outputs=[vp_group],
    )
    add_vp_btn.click(
        fn=_add_vp_wrapper,
        inputs=[vp_state, vp_input],
        outputs=[vp_state, vp_list, vp_input],
    )
    remove_vp_btn.click(
        fn=_remove_last_vp_wrapper,
        inputs=[vp_state],
        outputs=[vp_state, vp_list],
    )
    remove_selected_vp_btn.click(
        fn=_remove_selected_vp_wrapper,
        inputs=[vp_list, vp_state],
        outputs=[vp_state, vp_list],
    )
