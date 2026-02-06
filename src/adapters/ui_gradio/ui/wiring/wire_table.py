"""Table-section event wiring."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio import handlers
from adapters.ui_gradio.constants import (
    TABLE_MASSIVE_CM,
    TABLE_STANDARD_CM,
    UNIT_LIMITS,
)
from adapters.ui_gradio.units import (
    convert_from_cm,
    convert_to_cm,
    convert_unit_to_unit,
)

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
) -> None:
    """Wire table preset/unit changes and objective-default updates."""

    table_preset.change(
        fn=_on_table_preset_change,
        inputs=[table_preset, table_unit],
        outputs=[custom_table_row, table_width, table_height],
    )
    table_unit.change(
        fn=_on_table_unit_change,
        inputs=[table_unit, table_width, table_height, prev_unit_state],
        outputs=[table_width, table_height, prev_unit_state],
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
