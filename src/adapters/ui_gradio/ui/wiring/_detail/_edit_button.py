"""Edit-button wiring — populates the Create form and navigates to edit mode.

Extracted from ``wire_detail.py`` to reduce its size.  The public entry
point is :func:`wire_edit_button`, called by ``wire_detail_page`` when the
edit-mode widgets are available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import gradio as gr
from adapters.ui_gradio.state_helpers import (
    get_deployment_zones_choices,
    get_objective_points_choices,
    get_scenography_choices,
    get_special_rules_choices,
    get_victory_points_choices,
)
from adapters.ui_gradio.ui.components.search_helpers import escape_html
from adapters.ui_gradio.ui.router import PAGE_EDIT, navigate_to
from adapters.ui_gradio.ui.wiring._detail._converters import (
    _api_deployment_to_state,
    _api_objectives_to_state,
    _api_scenography_to_state,
    _api_special_rules_to_state,
    _extract_objectives_text_for_form,
)

# ── Module-level helpers (no nesting penalty for CC) ─────────────────


@dataclass(frozen=True)
class _EditFormData:
    """Extracted form data from API card response."""

    name: str
    heading: str
    svg_wrapped: str
    obj_text: str
    vp_enabled: bool
    vp_items: list
    rules_state_val: list
    scen_state_val: list
    depl_state_val: list
    obj_state_val: list
    shared_val: str
    has_scen: bool
    has_depl: bool
    has_obj: bool
    card_data: dict = field(repr=False)


def _extract_edit_form_data(
    card_data: dict[str, Any],
    svg_wrapped: str,
) -> _EditFormData:
    """Pure extraction of derived form data from API card response."""
    name = card_data.get("name", "")
    heading = f"## Edit: {escape_html(name)}" if name else "## Edit Scenario"

    obj_text, vp_enabled, vp_items = _extract_objectives_text_for_form(
        card_data.get("objectives"),
    )

    rules_raw = card_data.get("special_rules")
    rules_state_val = (
        _api_special_rules_to_state(rules_raw)
        if isinstance(rules_raw, list) and rules_raw
        else []
    )

    shapes = card_data.get("shapes") or {}
    if not isinstance(shapes, dict):
        shapes = {}
    scen_specs = shapes.get("scenography_specs", [])
    depl_shapes = shapes.get("deployment_shapes", [])
    obj_shapes = shapes.get("objective_shapes", [])

    shared_list = card_data.get("shared_with", [])
    shared_val = ", ".join(shared_list) if isinstance(shared_list, list) else ""

    return _EditFormData(
        name=name,
        heading=heading,
        svg_wrapped=svg_wrapped,
        obj_text=obj_text,
        vp_enabled=vp_enabled,
        vp_items=vp_items,
        rules_state_val=rules_state_val,
        scen_state_val=_api_scenography_to_state(scen_specs) if scen_specs else [],
        depl_state_val=_api_deployment_to_state(depl_shapes) if depl_shapes else [],
        obj_state_val=_api_objectives_to_state(obj_shapes) if obj_shapes else [],
        shared_val=shared_val,
        has_scen=bool(scen_specs),
        has_depl=bool(depl_shapes),
        has_obj=bool(obj_shapes),
        card_data=card_data,
    )


def _collect_non_none(
    pairs: list[tuple[Any, Any]],
) -> list[Any]:
    """Collect values from (widget, value) pairs where widget is not None."""
    return [v for w, v in pairs if w is not None]


def _build_empty_edit_result(
    nav: tuple,
    n_opt: int,
    has_btn: bool,
) -> tuple:
    """Build the return tuple for empty / error card editing."""
    btn_reset = (gr.update(value="Create Scenario"),) if has_btn else ()
    return (
        *nav,
        "",  # editing_card_id
        "## Create New Scenario",
        "",  # scenario_name
        "casual",  # mode
        True,  # is_replicable
        "",  # armies
        *btn_reset,
        *([gr.update()] * n_opt),
    )


def _build_opt_pairs(
    fd: _EditFormData,
    opt_widgets: list[Any],
) -> list[tuple[Any, Any]]:
    """Build (widget, value) pairs for all optional outputs.

    *opt_widgets* order must match the ``_opt`` list in ``wire_edit_button``.
    """
    cd = fd.card_data
    depl_choices = get_deployment_zones_choices(fd.depl_state_val)
    obj_choices = get_objective_points_choices(fd.obj_state_val)
    scen_choices = get_scenography_choices(fd.scen_state_val)
    vp_choices = get_victory_points_choices(fd.vp_items)
    rules_choices = get_special_rules_choices(fd.rules_state_val)

    # fmt: off
    values: list[Any] = [
        # simple form fields
        gr.update(value=cd.get("table_preset", "standard")),
        gr.update(value=cd.get("deployment", "") or ""),
        gr.update(value=cd.get("layout", "") or ""),
        gr.update(value=fd.obj_text),
        gr.update(value=cd.get("initial_priority", "") or ""),
        gr.update(value=fd.vp_enabled),
        fd.vp_items,
        gr.update(value=cd.get("visibility", "public")),
        gr.update(value=fd.shared_val),
        fd.rules_state_val,
        # shape states
        fd.scen_state_val,
        fd.depl_state_val,
        fd.obj_state_val,
        gr.update(value=fd.svg_wrapped),
        gr.update(value=None),
        # deployment zones section
        gr.update(choices=depl_choices, value=None),
        gr.update(value=fd.has_depl),
        gr.update(visible=fd.has_depl),
        # objective points section
        gr.update(choices=obj_choices, value=None),
        gr.update(value=fd.has_obj),
        gr.update(visible=fd.has_obj),
        # scenography section
        gr.update(choices=scen_choices, value=None),
        gr.update(value=fd.has_scen),
        gr.update(visible=fd.has_scen),
        # VP section
        gr.update(choices=vp_choices, value=None),
        gr.update(visible=fd.vp_enabled),
        # special rules section
        gr.update(choices=rules_choices, value=None),
        gr.update(value=bool(fd.rules_state_val)),
        gr.update(visible=bool(fd.rules_state_val)),
    ]
    # fmt: on
    return list(zip(opt_widgets, values, strict=False))


@dataclass(frozen=True)
class EditButtonCtx:
    """Widget references for edit-button wiring."""

    fetch_card_and_svg: Any
    detail_edit_btn: gr.Button
    detail_card_id_state: gr.Textbox
    actor_id_state: gr.State | None
    page_state: gr.State
    page_containers: list[gr.Column]
    editing_card_id: gr.Textbox
    editing_reload_trigger: gr.State | None
    create_heading_md: gr.Markdown
    scenario_name: gr.Textbox
    mode: gr.Radio
    is_replicable: gr.Checkbox
    armies: gr.Textbox
    table_preset: gr.Radio | None
    deployment: gr.Textbox
    layout: gr.Textbox
    objectives: gr.Textbox
    initial_priority: gr.Textbox
    objectives_with_vp_toggle: gr.Checkbox | None
    vp_state: gr.State | None
    visibility: gr.Radio | None
    shared_with: gr.Textbox | None
    special_rules_state: gr.State | None
    scenography_state: gr.State | None
    deployment_zones_state: gr.State | None
    objective_points_state: gr.State | None
    svg_preview: gr.HTML | None
    output: gr.JSON | None
    deployment_zones_list: gr.Dropdown | None = None
    deployment_zones_toggle: gr.Checkbox | None = None
    zones_group: gr.Group | None = None
    objective_points_list: gr.Dropdown | None = None
    objective_points_toggle: gr.Checkbox | None = None
    objective_points_group: gr.Group | None = None
    scenography_list: gr.Dropdown | None = None
    scenography_toggle: gr.Checkbox | None = None
    scenography_group: gr.Group | None = None
    vp_list: gr.Dropdown | None = None
    vp_group: gr.Group | None = None
    rules_list: gr.Dropdown | None = None
    special_rules_toggle: gr.Checkbox | None = None
    rules_group: gr.Group | None = None
    create_scenario_btn: gr.Button | None = None


def wire_edit_button(*, ctx: EditButtonCtx) -> None:  # noqa: C901
    """Wire the Edit button to populate Create form and navigate there."""
    c = ctx

    # Collect all outputs that will be populated
    _form_outputs: list[gr.components.Component] = [
        c.page_state,
        *c.page_containers,
        c.editing_card_id,
        c.create_heading_md,
        c.scenario_name,
        c.mode,
        c.is_replicable,
        c.armies,
    ]
    if c.create_scenario_btn is not None:
        _form_outputs.append(c.create_scenario_btn)

    # Optional form fields — order determines output mapping
    _opt: list[gr.components.Component | None] = [
        c.table_preset,
        c.deployment,
        c.layout,
        c.objectives,
        c.initial_priority,
        c.objectives_with_vp_toggle,
        c.vp_state,
        c.visibility,
        c.shared_with,
        c.special_rules_state,
        c.scenography_state,
        c.deployment_zones_state,
        c.objective_points_state,
        c.svg_preview,
        c.output,
        c.deployment_zones_list,
        c.deployment_zones_toggle,
        c.zones_group,
        c.objective_points_list,
        c.objective_points_toggle,
        c.objective_points_group,
        c.scenography_list,
        c.scenography_toggle,
        c.scenography_group,
        c.vp_list,
        c.vp_group,
        c.rules_list,
        c.special_rules_toggle,
        c.rules_group,
    ]
    _opt_present = [w for w in _opt if w is not None]
    _all_outputs = _form_outputs + _opt_present
    _has_btn = c.create_scenario_btn is not None
    _n_opt = len(_opt_present)

    def _go_edit_form(card_id: str, actor_id: str = "") -> tuple:
        """Fetch card data and navigate to Create page in edit mode."""
        nav = navigate_to(PAGE_EDIT)

        if not card_id:
            return _build_empty_edit_result(nav, _n_opt, _has_btn)

        card_data, svg_wrapped = c.fetch_card_and_svg(card_id, actor_id)
        if card_data.get("status") == "error":
            return _build_empty_edit_result(nav, _n_opt, _has_btn)

        fd = _extract_edit_form_data(card_data, svg_wrapped)

        values: list[Any] = [
            *nav,
            card_id,
            fd.heading,
            gr.update(value=fd.name or ""),
            gr.update(value=fd.card_data.get("mode", "casual")),
            gr.update(value=fd.card_data.get("is_replicable", True)),
            gr.update(value=fd.card_data.get("armies", "") or ""),
        ]
        if _has_btn:
            values.append(gr.update(value="Update Scenario"))

        values.extend(_collect_non_none(_build_opt_pairs(fd, _opt)))
        return tuple(values)

    _edit_inputs: list[gr.components.Component] = [c.detail_card_id_state]
    if c.actor_id_state is not None:
        _edit_inputs.append(c.actor_id_state)

    c.detail_edit_btn.click(
        fn=_go_edit_form,
        inputs=_edit_inputs,
        outputs=_all_outputs,
    )

    # ── F5 edit restore: when editing_reload_trigger fires, repopulate
    # the form from editing_card_id (set by _check_auth on page load).
    def _reload_edit_form(_trigger: int, card_id: str, actor_id: str = "") -> tuple:
        """Repopulate edit form from card_id on page reload (F5)."""
        if not card_id:
            return tuple(gr.update() for _ in _all_outputs)
        return _go_edit_form(card_id, actor_id)

    if c.editing_reload_trigger is not None:
        _reload_inputs: list[gr.components.Component] = [
            c.editing_reload_trigger,
            c.editing_card_id,
        ]
        if c.actor_id_state is not None:
            _reload_inputs.append(c.actor_id_state)

        c.editing_reload_trigger.change(
            fn=_reload_edit_form,
            inputs=_reload_inputs,
            outputs=_all_outputs,
        )
