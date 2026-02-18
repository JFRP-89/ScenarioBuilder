"""Preview-and-render helper for the generate button."""

from __future__ import annotations

from typing import Any

import gradio as gr
from adapters.ui_gradio._state._deployment_zones import get_deployment_zones_choices
from adapters.ui_gradio._state._objective_points import get_objective_points_choices
from adapters.ui_gradio._state._scenography import get_scenography_choices
from adapters.ui_gradio._state._seed_sync import (
    api_deployment_to_ui_state,
    api_objectives_to_ui_state,
    api_scenography_to_ui_state,
)
from adapters.ui_gradio.services._generate._form_state import FormState
from adapters.ui_gradio.services.generate import handle_preview
from adapters.ui_gradio.ui.components.svg_preview import render_svg_from_card


def _filter_internal_fields(preview_data: dict[str, Any]) -> dict[str, Any]:
    """Filter internal fields from preview data for display.

    Internal fields are:
    - Fields prefixed with _ (_payload, _actor_id) - needed for submission only
    - is_replicable - configuration flag, not part of scenario data visible to user
    - generate_from_seed - transient input, not stored in card

    These fields are kept in full preview data for submission but hidden from JSON display.
    """
    return {
        k: v
        for k, v in preview_data.items()
        if not k.startswith("_") and k not in ("is_replicable", "generate_from_seed")
    }


def _extract_shape_states(
    preview_data: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],  # deployment_zones_state
    list[dict[str, Any]],  # objective_points_state
    list[dict[str, Any]],  # scenography_state
]:
    """Convert API-format shapes in preview_data to UI state format.

    Returns (dep_state, obj_state, scen_state) ready for ``gr.State`` injection.
    """
    shapes = preview_data.get("shapes", {})
    dep_state = api_deployment_to_ui_state(shapes.get("deployment_shapes", []))
    obj_state = api_objectives_to_ui_state(shapes.get("objective_shapes", []))
    scen_state = api_scenography_to_ui_state(shapes.get("scenography_specs", []))
    return dep_state, obj_state, scen_state


# Return type: 9-tuple
_PreviewResult = tuple[
    dict[str, Any],  # display_data   (JSON)
    str,  # svg_html       (HTML)
    dict[str, Any],  # full_preview   (State)
    list[dict[str, Any]],  # dep_state      (State)
    dict,  # dep_choices    (gr.update for Dropdown)
    list[dict[str, Any]],  # obj_state      (State)
    dict,  # obj_choices    (gr.update for Dropdown)
    list[dict[str, Any]],  # scen_state     (State)
    dict,  # scen_choices   (gr.update for Dropdown)
]


def preview_and_render(*args: Any) -> _PreviewResult:
    """Validate form, build preview card, and render SVG locally.

    Pure delegation — no Gradio wiring, easy to unit-test.

    Returns a 9-tuple:
        0. filtered_preview_for_display  (JSON display)
        1. svg_html                      (SVG preview)
        2. full_preview_data             (State — for submission)
        3. deployment_zones_state        (State — editable zones)
        4. deployment_zones_choices      (gr.update — dropdown)
        5. objective_points_state        (State — editable points)
        6. objective_points_choices      (gr.update — dropdown)
        7. scenography_state             (State — editable scenography)
        8. scenography_choices           (gr.update — dropdown)
    """
    preview_data = handle_preview(FormState(*args))

    # On error, return empty shapes + no-op dropdowns
    if preview_data.get("status") == "error":
        svg_html = ""
        display_data = preview_data
        empty: list[dict[str, Any]] = []
        return (
            display_data,
            svg_html,
            preview_data,
            empty,
            gr.update(),
            empty,
            gr.update(),
            empty,
            gr.update(),
        )

    svg_html = render_svg_from_card(preview_data)
    display_data = _filter_internal_fields(preview_data)

    # Convert API shapes → UI state format
    dep_state, obj_state, scen_state = _extract_shape_states(preview_data)

    return (
        display_data,
        svg_html,
        preview_data,
        dep_state,
        gr.update(choices=get_deployment_zones_choices(dep_state), value=None),
        obj_state,
        gr.update(choices=get_objective_points_choices(obj_state), value=None),
        scen_state,
        gr.update(choices=get_scenography_choices(scen_state), value=None),
    )
