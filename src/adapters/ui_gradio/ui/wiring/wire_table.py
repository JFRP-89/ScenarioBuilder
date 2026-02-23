"""Table-section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr

from adapters.ui_gradio import handlers
from adapters.ui_gradio._state._table_validation import check_all_shapes_fit_table
from adapters.ui_gradio.constants import (
    TABLE_MASSIVE_CM,
    TABLE_STANDARD_CM,
    UNIT_LIMITS,
)
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
    to_mm,
)

# Standard / massive dimensions in mm for preset detection
_STANDARD_MM = (int(TABLE_STANDARD_CM[0] * 10), int(TABLE_STANDARD_CM[1] * 10))
_MASSIVE_MM = (int(TABLE_MASSIVE_CM[0] * 10), int(TABLE_MASSIVE_CM[1] * 10))


def _detect_preset(width_mm: int, height_mm: int) -> str:
    """Infer the preset name from mm dimensions."""
    if (width_mm, height_mm) == _STANDARD_MM:
        return "standard"
    if (width_mm, height_mm) == _MASSIVE_MM:
        return "massive"
    return "custom"


# -- thin adapters (tests import these via app.py compat shims) -----------


def _on_table_preset_change(
    preset: str, current_unit: str
) -> tuple[dict[str, Any], float, float]:
    result: tuple[dict[str, Any], float, float] = handlers.on_table_preset_change(
        preset, current_unit, TABLE_STANDARD_CM, TABLE_MASSIVE_CM, convert_from_cm
    )
    return result


def _on_table_unit_change(
    new_unit: str, width: float, height: float, prev_unit: str
) -> tuple[float, float, str]:
    result: tuple[float, float, str] = handlers.on_table_unit_change(
        new_unit, width, height, prev_unit, UNIT_LIMITS, convert_unit_to_unit
    )
    return result


# -- wiring ---------------------------------------------------------------


def wire_table(
    *,
    table_preset: gr.Radio,
    prev_unit_state: gr.State,
    custom_table_row: gr.Row,
    table_width: gr.Number,
    table_height: gr.Number,
    table_unit: gr.Radio,
    objective_cx_input: gr.Number,
    objective_cy_input: gr.Number,
    # Shape states for bounds validation on resize
    deployment_zones_state: gr.State,
    objective_points_state: gr.State,
    scenography_state: gr.State,
    output: gr.JSON,
) -> None:
    """Wire table preset/unit changes and objective-default updates.

    When the table dimensions shrink (preset change or manual edit),
    existing deployment zones, objective points and scenography elements
    are validated against the new bounds.  If any shape overflows the
    table, the change is **rejected** and an error is shown in *output*.
    """

    def _on_preset_with_validation(
        preset: str,
        current_unit: str,
        old_width: float,
        old_height: float,
        dep_zones: list[dict[str, Any]],
        obj_points: list[dict[str, Any]],
        scen_items: list[dict[str, Any]],
    ) -> dict[Any, Any]:
        """Change table preset, but reject if shapes overflow."""
        # Compute what the new dimensions would be
        vis_update, new_w, new_h = _on_table_preset_change(preset, current_unit)
        new_w_mm = to_mm(new_w, current_unit)
        new_h_mm = to_mm(new_h, current_unit)

        err = check_all_shapes_fit_table(
            deployment_zones=dep_zones,
            objective_points=obj_points,
            scenography=scen_items,
            table_width_mm=new_w_mm,
            table_height_mm=new_h_mm,
        )
        if err:
            # Reject: keep old dimensions, revert preset display
            old_w_mm = to_mm(old_width, current_unit)
            old_h_mm = to_mm(old_height, current_unit)
            old_preset = _detect_preset(old_w_mm, old_h_mm)
            return {
                table_preset: gr.update(value=old_preset),
                custom_table_row: gr.update(visible=(old_preset == "custom")),
                table_width: old_width,
                table_height: old_height,
                output: {"status": "error", "message": err},
            }

        return {
            table_preset: gr.update(),
            custom_table_row: vis_update,
            table_width: new_w,
            table_height: new_h,
            output: gr.update(),
        }

    table_preset.change(
        fn=_on_preset_with_validation,
        inputs=[
            table_preset,
            table_unit,
            table_width,
            table_height,
            deployment_zones_state,
            objective_points_state,
            scenography_state,
        ],
        outputs=[table_preset, custom_table_row, table_width, table_height, output],
    )

    table_unit.change(
        fn=_on_table_unit_change,
        inputs=[table_unit, table_width, table_height, prev_unit_state],
        outputs=[table_width, table_height, prev_unit_state],
    )

    # Validate shapes when width/height are manually changed
    def _on_dimension_change(
        new_w: float,
        new_h: float,
        unit: str,
        dep_zones: list[dict[str, Any]],
        obj_points: list[dict[str, Any]],
        scen_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Reject manual dimension changes that would clip existing shapes."""
        new_w_mm = to_mm(new_w, unit)
        new_h_mm = to_mm(new_h, unit)

        err = check_all_shapes_fit_table(
            deployment_zones=dep_zones,
            objective_points=obj_points,
            scenography=scen_items,
            table_width_mm=new_w_mm,
            table_height_mm=new_h_mm,
        )
        if err:
            return {output: {"status": "error", "message": err}}
        return {output: gr.update()}

    for component in (table_width, table_height):
        component.change(
            fn=_on_dimension_change,
            inputs=[
                table_width,
                table_height,
                table_unit,
                deployment_zones_state,
                objective_points_state,
                scenography_state,
            ],
            outputs=[output],
        )

    # Objective defaults on table resize
    def _update_objective_defaults(
        tw: float, th: float, tu: str
    ) -> tuple[float, float]:
        result: tuple[float, float] = handlers.update_objective_defaults(
            tw, th, tu, convert_to_cm
        )
        return result

    for component in (table_width, table_height, table_unit):
        component.change(
            fn=_update_objective_defaults,
            inputs=[table_width, table_height, table_unit],
            outputs=[objective_cx_input, objective_cy_input],
        )
