"""Unit selector component for measurement unit conversion (cm/in/ft)."""

from __future__ import annotations

import gradio as gr


def create_unit_state() -> gr.State:
    """Create a State component to track the previous unit value.

    Returns:
        State component initialized with "cm"

    Example:
        >>> unit_state = create_unit_state()
    """
    return gr.State("cm")


def create_unit_radio(elem_id_prefix: str) -> gr.Radio:
    """Create a Radio component for unit selection (cm/in/ft).

    Args:
        elem_id_prefix: Prefix for the elem_id (e.g., "table", "zone", "objective")

    Returns:
        Radio component with cm/in/ft choices

    Example:
        >>> unit_radio = create_unit_radio("table")
        >>> # unit_radio will have elem_id="table-unit"
    """
    return gr.Radio(
        choices=["cm", "in", "ft"],
        value="cm",
        label="Unit",
        elem_id=f"{elem_id_prefix}-unit",
    )


def build_unit_selector(elem_id_prefix: str) -> tuple[gr.State, gr.Radio]:
    """Build a complete unit selector (State + Radio) for measurement conversion.

    This is a convenience function that creates both the State and Radio
    in the current Gradio context. If you need more control over where
    each component is placed, use create_unit_state() and create_unit_radio()
    separately.

    Args:
        elem_id_prefix: Prefix for the elem_id (e.g., "table", "zone", "objective")

    Returns:
        Tuple of (unit_state, unit_radio)

    Example:
        >>> # Inside a Gradio context:
        >>> with gr.Row():
        ...     unit_state, unit_radio = build_unit_selector("table")
    """
    unit_state = create_unit_state()
    unit_radio = create_unit_radio(elem_id_prefix)
    return unit_state, unit_radio
