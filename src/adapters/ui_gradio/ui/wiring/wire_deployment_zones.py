"""Deployment-zones section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.state_helpers import (
    add_deployment_zone,
    get_deployment_zones_choices,
    remove_last_deployment_zone,
    remove_selected_deployment_zone,
    validate_separation_coords,
)
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
)


def wire_deployment_zones(  # noqa: C901
    *,
    deployment_zones_toggle: gr.Checkbox,
    zones_group: gr.Group,
    deployment_zones_state: gr.State,
    zone_table_width_state: gr.State,
    zone_table_height_state: gr.State,
    zone_unit_state: gr.State,
    zone_border_select: gr.Radio,
    zone_fill_side_checkbox: gr.Checkbox,
    zone_unit: gr.Radio,
    zone_description: gr.Textbox,
    zone_width: gr.Number,
    zone_height: gr.Number,
    zone_sep_x: gr.Number,
    zone_sep_y: gr.Number,
    add_zone_btn: gr.Button,
    remove_last_zone_btn: gr.Button,
    deployment_zones_list: gr.Dropdown,
    remove_selected_zone_btn: gr.Button,
    table_preset: gr.Radio,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    output: gr.JSON,
) -> None:
    """Wire deployment-zone add/remove/border-fill events."""

    # -- closures ----------------------------------------------------------

    def _add_deployment_zone_wrapper(
        border: str,
        fill_side: bool,
        desc: str,
        w: float,
        h: float,
        sx: float,
        sy: float,
        current_state: list[dict[str, Any]],
        tw: float,
        th: float,
        tu: str,
        zone_unit_val: str,
    ) -> dict[Any, Any]:
        description_stripped = (desc or "").strip()
        if not description_stripped:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Description to be filled.",
                },
            }
        if not border or not border.strip():
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Border to be selected.",
                },
            }
        if not w or w <= 0:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Width > 0.",
                },
            }
        if not h or h <= 0:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {
                    "status": "error",
                    "message": "Deployment Zone requires Height > 0.",
                },
            }
        table_w_mm = int(convert_to_cm(tw, tu) * 10)
        table_h_mm = int(convert_to_cm(th, tu) * 10)

        # Convert zone dimensions from user unit to mm
        w_mm = int(convert_to_cm(w, zone_unit_val) * 10)
        h_mm = int(convert_to_cm(h, zone_unit_val) * 10)
        sx_mm = int(convert_to_cm(sx, zone_unit_val) * 10)
        sy_mm = int(convert_to_cm(sy, zone_unit_val) * 10)

        if fill_side:
            if border in ("north", "south"):
                w_mm = table_w_mm
                sx_mm = 0
            else:
                h_mm = table_h_mm
                sy_mm = 0
        sx_mm, sy_mm = validate_separation_coords(
            border, w_mm, h_mm, sx_mm, sy_mm, table_w_mm, table_h_mm
        )
        zone_data = {
            "type": "rect",
            "description": description_stripped,
            "x": int(sx_mm),
            "y": int(sy_mm),
            "width": int(w_mm),
            "height": int(h_mm),
            "border": border,
        }
        new_state, error_msg = add_deployment_zone(
            current_state, zone_data, table_w_mm, table_h_mm
        )
        if error_msg:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
                output: {"status": "error", "message": error_msg},
            }
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices),
            output: {"status": "success"},
        }

    def _remove_last_deployment_zone_wrapper(
        current_state: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        new_state = remove_last_deployment_zone(current_state)
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices),
        }

    def _remove_selected_deployment_zone_wrapper(
        selected_id: str | None, current_state: list[dict[str, Any]]
    ) -> dict[Any, Any]:
        if not selected_id:
            return {
                deployment_zones_state: current_state,
                deployment_zones_list: gr.update(),
            }
        new_state = remove_selected_deployment_zone(current_state, selected_id)
        choices = get_deployment_zones_choices(new_state)
        return {
            deployment_zones_state: new_state,
            deployment_zones_list: gr.update(choices=choices),
        }

    def _on_zone_border_or_fill_change(
        border_val: str,
        fill_side: bool,
        tw: float,
        th: float,
        tu: str,
        zone_unit_val: str,
    ) -> dict[str, Any]:
        """Update zone dimensions when border or fill_side changes.

        Converts table dimensions to the current zone unit.
        """
        # Convert table dimensions to cm, then to the current zone unit
        table_w_cm = convert_to_cm(tw, tu)
        table_h_cm = convert_to_cm(th, tu)

        width_in_zone_unit = convert_from_cm(table_w_cm, zone_unit_val)
        height_in_zone_unit = convert_from_cm(table_h_cm, zone_unit_val)

        updates: dict[Any, Any] = {}
        if fill_side:
            if border_val in ("north", "south"):
                updates[zone_width] = gr.update(
                    value=round(width_in_zone_unit, 2),
                    interactive=False,
                    label=f"Width ({zone_unit_val}) [LOCKED]",
                )
                updates[zone_height] = gr.update(
                    interactive=True, label=f"Height ({zone_unit_val})"
                )
                updates[zone_sep_x] = gr.update(
                    value=0,
                    interactive=False,
                    label=f"Separation X ({zone_unit_val}) [LOCKED]",
                )
                updates[zone_sep_y] = gr.update(
                    interactive=True, label=f"Separation Y ({zone_unit_val})"
                )
            else:
                updates[zone_width] = gr.update(
                    interactive=True, label=f"Width ({zone_unit_val})"
                )
                updates[zone_height] = gr.update(
                    value=round(height_in_zone_unit, 2),
                    interactive=False,
                    label=f"Height ({zone_unit_val}) [LOCKED]",
                )
                updates[zone_sep_x] = gr.update(
                    interactive=True, label=f"Separation X ({zone_unit_val})"
                )
                updates[zone_sep_y] = gr.update(
                    value=0,
                    interactive=False,
                    label=f"Separation Y ({zone_unit_val}) [LOCKED]",
                )
        else:
            updates[zone_width] = gr.update(
                interactive=True, label=f"Width ({zone_unit_val})"
            )
            updates[zone_height] = gr.update(
                interactive=True, label=f"Height ({zone_unit_val})"
            )
            updates[zone_sep_x] = gr.update(
                interactive=True, label=f"Separation X ({zone_unit_val})"
            )
            updates[zone_sep_y] = gr.update(
                interactive=True, label=f"Separation Y ({zone_unit_val})"
            )
        return updates

    # -- bindings ----------------------------------------------------------

    _zone_inputs = [
        zone_border_select,
        zone_fill_side_checkbox,
        table_width,
        table_height,
        table_unit,
        zone_unit,
    ]
    _zone_outputs = [zone_width, zone_height, zone_sep_x, zone_sep_y]
    for component in (
        zone_border_select,
        zone_fill_side_checkbox,
        table_preset,
        table_width,
        table_height,
        table_unit,
    ):
        component.change(
            fn=_on_zone_border_or_fill_change,
            inputs=_zone_inputs,
            outputs=_zone_outputs,
        )

    add_zone_btn.click(
        fn=_add_deployment_zone_wrapper,
        inputs=[
            zone_border_select,
            zone_fill_side_checkbox,
            zone_description,
            zone_width,
            zone_height,
            zone_sep_x,
            zone_sep_y,
            deployment_zones_state,
            table_width,
            table_height,
            table_unit,
            zone_unit,
        ],
        outputs=[deployment_zones_state, deployment_zones_list, output],
    )
    remove_last_zone_btn.click(
        fn=_remove_last_deployment_zone_wrapper,
        inputs=[deployment_zones_state],
        outputs=[deployment_zones_state, deployment_zones_list],
    )
    remove_selected_zone_btn.click(
        fn=_remove_selected_deployment_zone_wrapper,
        inputs=[deployment_zones_list, deployment_zones_state],
        outputs=[deployment_zones_state, deployment_zones_list],
    )

    # Wire toggle for Deployment Zones section
    def _toggle_deployment_zones(enabled: bool) -> Any:
        return handlers.toggle_deployment_zones_section(enabled)

    deployment_zones_toggle.change(
        fn=_toggle_deployment_zones,
        inputs=[deployment_zones_toggle],
        outputs=[zones_group],
    )

    # Wire unit change for Deployment Zones
    def _on_zone_unit_change(
        new_unit: str, w: float, h: float, sx: float, sy: float, prev_unit: str
    ) -> tuple[float, float, float, float, str]:
        """Convert zone dimensions when unit changes."""
        if prev_unit == new_unit:
            return w, h, sx, sy, new_unit
        w_converted = convert_unit_to_unit(w, prev_unit, new_unit)
        h_converted = convert_unit_to_unit(h, prev_unit, new_unit)
        sx_converted = convert_unit_to_unit(sx, prev_unit, new_unit) if sx else 0
        sy_converted = convert_unit_to_unit(sy, prev_unit, new_unit) if sy else 0
        return w_converted, h_converted, sx_converted, sy_converted, new_unit

    zone_unit.change(
        fn=_on_zone_unit_change,
        inputs=[
            zone_unit,
            zone_width,
            zone_height,
            zone_sep_x,
            zone_sep_y,
            zone_unit_state,
        ],
        outputs=[zone_width, zone_height, zone_sep_x, zone_sep_y, zone_unit_state],
    )
