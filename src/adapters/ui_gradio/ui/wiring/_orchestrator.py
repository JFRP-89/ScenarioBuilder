"""Internal wiring orchestrator — dispatches to per-section wirers.

This module is **private**.  The public API is ``wire_events()`` in
``__init__.py``, which delegates here after accepting all typed
keyword arguments.

Rationale
---------
``wire_events()`` intentionally has many parameters so that ``app.py``
(and the contract tests) can verify exhaustive component coverage via
introspection.  Moving the *body* here keeps the facade thin while
concentrating orchestration complexity in a single private place.
"""

from __future__ import annotations

from dataclasses import dataclass

import gradio as gr
from adapters.ui_gradio.ui.wiring._deployment._context import DeploymentZonesCtx
from adapters.ui_gradio.ui.wiring._scenography._context import ScenographyCtx
from adapters.ui_gradio.ui.wiring.wire_deployment_zones import wire_deployment_zones
from adapters.ui_gradio.ui.wiring.wire_generate import GenerateCtx, wire_generate
from adapters.ui_gradio.ui.wiring.wire_objectives import ObjectivesCtx, wire_objectives
from adapters.ui_gradio.ui.wiring.wire_scenography import wire_scenography
from adapters.ui_gradio.ui.wiring.wire_special_rules import wire_special_rules
from adapters.ui_gradio.ui.wiring.wire_table import wire_table
from adapters.ui_gradio.ui.wiring.wire_victory_points import wire_victory_points
from adapters.ui_gradio.ui.wiring.wire_visibility import wire_visibility

# ── DTO for seed-based field updates ────────────────────────────────


@dataclass(frozen=True)
class _SeedFieldsBundle:
    """Immutable bundle of Gradio components for seed-based scenario filling.

    Consolidates the ~20 state/table fields used by _wire_apply_seed and
    _wire_refill_scenario, reducing function signature complexity.
    """

    armies: gr.Textbox
    deployment: gr.Textbox
    layout: gr.Textbox
    objectives: gr.Textbox
    initial_priority: gr.Textbox
    scenario_name: gr.Textbox
    deployment_zones_state: gr.State
    deployment_zones_list: gr.Dropdown
    objective_points_state: gr.State
    objective_points_list: gr.Dropdown
    scenography_state: gr.State
    scenography_list: gr.Dropdown
    mode: gr.Radio
    table_preset: gr.Radio
    custom_table_row: gr.Row
    table_width: gr.Number
    table_height: gr.Number
    special_rules_state: gr.State

    @property
    def outputs_for_click(self) -> list:
        """Ordered list of components for Gradio click outputs."""
        return [
            self.armies,
            self.deployment,
            self.layout,
            self.objectives,
            self.initial_priority,
            self.scenario_name,
            self.deployment_zones_state,
            self.deployment_zones_list,
            self.objective_points_state,
            self.objective_points_list,
            self.scenography_state,
            self.scenography_list,
            self.mode,
            self.table_preset,
            self.custom_table_row,
            self.table_width,
            self.table_height,
            self.special_rules_state,
        ]


@dataclass(frozen=True)
class _MetaBundle:
    """Scenario meta fields: actor, name, mode, seed controls, text fields."""

    actor_id: gr.Textbox
    scenario_name: gr.Textbox
    mode: gr.Radio
    is_replicable: gr.Checkbox
    generate_from_seed: gr.Number
    apply_seed_btn: gr.Button
    refill_scenario_btn: gr.Button
    armies: gr.Textbox
    deployment: gr.Textbox
    layout: gr.Textbox
    objectives: gr.Textbox
    initial_priority: gr.Textbox


@dataclass(frozen=True)
class _TableBundle:
    """Table dimension / preset controls."""

    table_preset: gr.Radio
    prev_unit_state: gr.State
    custom_table_row: gr.Row
    table_width: gr.Number
    table_height: gr.Number
    table_unit: gr.Radio


@dataclass(frozen=True)
class _VPBundle:
    """Victory-points section controls."""

    objectives_with_vp_toggle: gr.Checkbox
    vp_group: gr.Group
    vp_state: gr.State
    vp_input: gr.Textbox
    add_vp_btn: gr.Button
    remove_vp_btn: gr.Button
    vp_list: gr.Dropdown
    remove_selected_vp_btn: gr.Button
    vp_editing_state: gr.State
    cancel_edit_vp_btn: gr.Button


@dataclass(frozen=True)
class _SpecialRulesBundle:
    """Special-rules section controls."""

    special_rules_state: gr.State
    special_rules_toggle: gr.Checkbox
    rules_group: gr.Group
    rule_type_radio: gr.Radio
    rule_name_input: gr.Textbox
    rule_value_input: gr.Textbox
    add_rule_btn: gr.Button
    remove_rule_btn: gr.Button
    rules_list: gr.Dropdown
    remove_selected_rule_btn: gr.Button
    rule_editing_state: gr.State
    cancel_edit_rule_btn: gr.Button


@dataclass(frozen=True)
class _VisibilityBundle:
    """Visibility section controls."""

    visibility: gr.Radio
    shared_with_row: gr.Row
    shared_with: gr.Textbox


@dataclass(frozen=True)
class _ObjectivesBundle:
    """Objective-points section controls."""

    objective_points_toggle: gr.Checkbox
    objective_points_group: gr.Group
    objective_points_state: gr.State
    objective_unit_state: gr.State
    objective_description: gr.Textbox
    objective_cx_input: gr.Number
    objective_cy_input: gr.Number
    objective_unit: gr.Radio
    add_objective_btn: gr.Button
    objective_points_list: gr.Dropdown
    remove_last_objective_btn: gr.Button
    remove_selected_objective_btn: gr.Button
    objective_editing_state: gr.State
    cancel_edit_objective_btn: gr.Button


@dataclass(frozen=True)
class _GenerateBundle:
    """Generate/output section controls + optional navigation/create/edit."""

    generate_btn: gr.Button
    svg_preview: gr.HTML
    output: gr.JSON
    preview_full_state: gr.State
    create_scenario_btn: gr.Button | None = None
    create_scenario_status: gr.Textbox | None = None
    page_state: gr.State | None = None
    page_containers: list[gr.Column] | None = None
    home_recent_html: gr.HTML | None = None
    home_page_info: gr.HTML | None = None
    home_page_state: gr.State | None = None
    home_cards_cache_state: gr.State | None = None
    home_fav_ids_cache_state: gr.State | None = None
    editing_card_id: gr.Textbox | None = None
    create_heading_md: gr.Markdown | None = None


# ── Helper functions for seed-based scenarios ──────────────────────


def _normalize_seed_value(seed_value: float | None) -> int:
    """Normalize and validate a seed value from Gradio."""
    if seed_value and seed_value > 0:
        return int(seed_value)
    return 0


def _normalize_objectives_text(obj: str | dict | None) -> str:
    """Extract readable objectives text from various formats."""
    if isinstance(obj, dict):
        return str(obj.get("objective", str(obj)))
    return str(obj) if obj else ""


def _build_seed_outputs(
    card,
    api_deployment_to_ui_state,
    api_objectives_to_ui_state,
    api_scenography_to_ui_state,
    get_deployment_zones_choices,
    get_objective_points_choices,
    get_scenography_choices,
) -> tuple:
    """Build output updates for a successfully loaded seed card."""
    obj_text = _normalize_objectives_text(card.objectives)
    dep_state = api_deployment_to_ui_state(card.map_spec.deployment_shapes or [])
    obj_state = api_objectives_to_ui_state(card.map_spec.objective_shapes or [])
    scen_state = api_scenography_to_ui_state(card.map_spec.shapes or [])
    preset = card.table.preset_name
    tw_cm = card.table.width_mm / 10
    th_cm = card.table.height_mm / 10
    return (
        gr.update(value=card.armies or ""),
        gr.update(value=card.deployment or ""),
        gr.update(value=card.layout or ""),
        gr.update(value=obj_text),
        gr.update(value=card.initial_priority or ""),
        gr.update(),  # scenario_name — NOT overwritten
        dep_state,
        gr.update(choices=get_deployment_zones_choices(dep_state), value=None),
        obj_state,
        gr.update(choices=get_objective_points_choices(obj_state), value=None),
        scen_state,
        gr.update(choices=get_scenography_choices(scen_state), value=None),
        gr.update(value=card.mode.value),
        gr.update(value=preset),
        gr.update(visible=(preset == "custom")),
        gr.update(value=tw_cm),
        gr.update(value=th_cm),
        card.special_rules or [],
    )


def _build_refill_outputs(
    new_seed: int,
    resolve_full_seed_defaults,
    get_services,
    api_deployment_to_ui_state,
    api_objectives_to_ui_state,
    api_scenography_to_ui_state,
    get_deployment_zones_choices,
    get_objective_points_choices,
    get_scenography_choices,
) -> tuple:
    """Build output updates for a newly generated random seed."""
    expected = resolve_full_seed_defaults(new_seed)
    svc = get_services()
    content = svc.generate_scenario_card.resolve_seed_preview(new_seed)
    full = svc.generate_scenario_card.resolve_full_seed_scenario(
        new_seed,
        expected["table_width_mm"],
        expected["table_height_mm"],
    )
    dep_state = api_deployment_to_ui_state(full.get("deployment_shapes", []))
    obj_state = api_objectives_to_ui_state(full.get("objective_shapes", []))
    scen_state = api_scenography_to_ui_state(full.get("scenography_specs", []))
    return (
        gr.update(value=new_seed),
        gr.update(value=content["armies"]),
        gr.update(value=content["deployment"]),
        gr.update(value=content["layout"]),
        gr.update(value=content["objectives"]),
        gr.update(value=content["initial_priority"]),
        gr.update(value=content.get("name", "")),
        dep_state,
        gr.update(choices=get_deployment_zones_choices(dep_state), value=None),
        obj_state,
        gr.update(choices=get_objective_points_choices(obj_state), value=None),
        scen_state,
        gr.update(choices=get_scenography_choices(scen_state), value=None),
        gr.update(value=expected["mode"]),
        gr.update(value=expected["table_preset"]),
        gr.update(visible=False),
        gr.update(value=expected["table_width_mm"] / 10),
        gr.update(value=expected["table_height_mm"] / 10),
        [],  # special_rules_state cleared
    )


# ── Seed-field wiring ────────────────────────────────────────────────


def _wire_replicable_toggle(
    is_replicable: gr.Checkbox,
    generate_from_seed: gr.Number,
    apply_seed_btn: gr.Button,
    refill_scenario_btn: gr.Button,
) -> None:
    """Wire the is_replicable toggle to enable/disable seed controls."""
    _saved_seed: list[float | None] = [None]

    def _toggle_seed_field(
        replicable: bool,
        current_seed: float | None,
    ) -> tuple[dict, dict, dict]:
        if replicable:
            return (
                gr.update(value=_saved_seed[0], interactive=True),
                gr.update(interactive=True),
                gr.update(interactive=True),
            )
        _saved_seed[0] = current_seed
        return (
            gr.update(value=None, interactive=False),
            gr.update(interactive=False),
            gr.update(interactive=False),
        )

    is_replicable.change(
        fn=_toggle_seed_field,
        inputs=[is_replicable, generate_from_seed],
        outputs=[generate_from_seed, apply_seed_btn, refill_scenario_btn],
    )


def _wire_apply_seed(
    *,
    apply_seed_btn: gr.Button,
    generate_from_seed: gr.Number,
    fields: _SeedFieldsBundle,
) -> None:
    """Wire the Apply Seed button to look up a card by seed and fill the form."""

    def _apply_seed(seed_value: float | None) -> tuple:
        from adapters.ui_gradio._state._deployment_zones import (
            get_deployment_zones_choices,
        )
        from adapters.ui_gradio._state._objective_points import (
            get_objective_points_choices,
        )
        from adapters.ui_gradio._state._scenography import get_scenography_choices
        from adapters.ui_gradio._state._seed_sync import (
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
        )
        from infrastructure.bootstrap import get_services

        _NO_CHANGE: tuple = tuple(gr.update() for _ in range(18))
        seed_int = _normalize_seed_value(seed_value)
        if seed_int <= 0:
            return _NO_CHANGE

        svc = get_services()
        card = svc.generate_scenario_card.find_card_by_seed(seed_int)
        if card is None:
            return _NO_CHANGE

        return _build_seed_outputs(
            card,
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
            get_deployment_zones_choices,
            get_objective_points_choices,
            get_scenography_choices,
        )

    apply_seed_btn.click(
        fn=_apply_seed,
        inputs=[generate_from_seed],
        outputs=fields.outputs_for_click,
    )


def _wire_refill_scenario(
    *,
    refill_scenario_btn: gr.Button,
    generate_from_seed: gr.Number,
    fields: _SeedFieldsBundle,
) -> None:
    """Wire the Refill Scenario button to generate a random seed + fill form."""

    def _refill_scenario() -> tuple:
        import random as _rng

        from adapters.ui_gradio._state._deployment_zones import (
            get_deployment_zones_choices,
        )
        from adapters.ui_gradio._state._objective_points import (
            get_objective_points_choices,
        )
        from adapters.ui_gradio._state._scenography import get_scenography_choices
        from adapters.ui_gradio._state._seed_sync import (
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
        )
        from application.use_cases._generate._themes import (
            _resolve_full_seed_defaults,
        )
        from domain.seed import MAX_SEED
        from infrastructure.bootstrap import get_services

        new_seed = _rng.randint(1, MAX_SEED)  # nosec B311 — not security-sensitive
        return _build_refill_outputs(
            new_seed,
            _resolve_full_seed_defaults,
            get_services,
            api_deployment_to_ui_state,
            api_objectives_to_ui_state,
            api_scenography_to_ui_state,
            get_deployment_zones_choices,
            get_objective_points_choices,
            get_scenography_choices,
        )

    refill_scenario_btn.click(
        fn=_refill_scenario,
        inputs=[],
        outputs=[generate_from_seed, *fields.outputs_for_click],
    )


# ── Main orchestrator ────────────────────────────────────────────────


def _wire_all(
    *,
    meta: _MetaBundle,
    table: _TableBundle,
    vp: _VPBundle,
    rules: _SpecialRulesBundle,
    vis: _VisibilityBundle,
    deployment_ctx: DeploymentZonesCtx,
    obj: _ObjectivesBundle,
    scenography_ctx: ScenographyCtx,
    gen: _GenerateBundle,
) -> None:
    """Dispatch all UI events to per-section wirers.

    This is the internal implementation behind ``wire_events()``.
    Each parameter is a frozen dataclass bundling a logical UI section,
    which keeps the orchestrator signature manageable while still
    wiring ~100 Gradio components together.
    """

    wire_table(
        table_preset=table.table_preset,
        prev_unit_state=table.prev_unit_state,
        custom_table_row=table.custom_table_row,
        table_width=table.table_width,
        table_height=table.table_height,
        table_unit=table.table_unit,
        objective_cx_input=obj.objective_cx_input,
        objective_cy_input=obj.objective_cy_input,
    )

    _wire_replicable_toggle(
        meta.is_replicable,
        meta.generate_from_seed,
        meta.apply_seed_btn,
        meta.refill_scenario_btn,
    )

    seed_fields_bundle = _SeedFieldsBundle(
        armies=meta.armies,
        deployment=meta.deployment,
        layout=meta.layout,
        objectives=meta.objectives,
        initial_priority=meta.initial_priority,
        scenario_name=meta.scenario_name,
        deployment_zones_state=deployment_ctx.deployment_zones_state,
        deployment_zones_list=deployment_ctx.deployment_zones_list,
        objective_points_state=obj.objective_points_state,
        objective_points_list=obj.objective_points_list,
        scenography_state=scenography_ctx.scenography_state,
        scenography_list=scenography_ctx.scenography_list,
        mode=meta.mode,
        table_preset=table.table_preset,
        custom_table_row=table.custom_table_row,
        table_width=table.table_width,
        table_height=table.table_height,
        special_rules_state=rules.special_rules_state,
    )

    _wire_apply_seed(
        apply_seed_btn=meta.apply_seed_btn,
        generate_from_seed=meta.generate_from_seed,
        fields=seed_fields_bundle,
    )

    _wire_refill_scenario(
        refill_scenario_btn=meta.refill_scenario_btn,
        generate_from_seed=meta.generate_from_seed,
        fields=seed_fields_bundle,
    )

    wire_special_rules(
        special_rules_state=rules.special_rules_state,
        special_rules_toggle=rules.special_rules_toggle,
        rules_group=rules.rules_group,
        rule_type_radio=rules.rule_type_radio,
        rule_name_input=rules.rule_name_input,
        rule_value_input=rules.rule_value_input,
        add_rule_btn=rules.add_rule_btn,
        remove_rule_btn=rules.remove_rule_btn,
        rules_list=rules.rules_list,
        remove_selected_rule_btn=rules.remove_selected_rule_btn,
        rule_editing_state=rules.rule_editing_state,
        cancel_edit_rule_btn=rules.cancel_edit_rule_btn,
        output=gen.output,
    )

    wire_victory_points(
        objectives_with_vp_toggle=vp.objectives_with_vp_toggle,
        vp_group=vp.vp_group,
        vp_state=vp.vp_state,
        vp_input=vp.vp_input,
        add_vp_btn=vp.add_vp_btn,
        remove_vp_btn=vp.remove_vp_btn,
        vp_list=vp.vp_list,
        remove_selected_vp_btn=vp.remove_selected_vp_btn,
        vp_editing_state=vp.vp_editing_state,
        cancel_edit_vp_btn=vp.cancel_edit_vp_btn,
    )

    wire_scenography(scenography_ctx)

    wire_deployment_zones(deployment_ctx)

    wire_objectives(
        ctx=ObjectivesCtx(
            objective_points_toggle=obj.objective_points_toggle,
            objective_points_group=obj.objective_points_group,
            objective_points_state=obj.objective_points_state,
            objective_unit_state=obj.objective_unit_state,
            objective_description=obj.objective_description,
            objective_cx_input=obj.objective_cx_input,
            objective_cy_input=obj.objective_cy_input,
            objective_unit=obj.objective_unit,
            add_objective_btn=obj.add_objective_btn,
            objective_points_list=obj.objective_points_list,
            remove_last_objective_btn=obj.remove_last_objective_btn,
            remove_selected_objective_btn=obj.remove_selected_objective_btn,
            table_width=table.table_width,
            table_height=table.table_height,
            table_unit=table.table_unit,
            objective_editing_state=obj.objective_editing_state,
            cancel_edit_objective_btn=obj.cancel_edit_objective_btn,
            output=gen.output,
        )
    )

    wire_visibility(
        visibility=vis.visibility,
        shared_with_row=vis.shared_with_row,
    )

    wire_generate(
        ctx=GenerateCtx(
            actor_id=meta.actor_id,
            scenario_name=meta.scenario_name,
            mode=meta.mode,
            is_replicable=meta.is_replicable,
            generate_from_seed=meta.generate_from_seed,
            armies=meta.armies,
            table_preset=table.table_preset,
            table_width=table.table_width,
            table_height=table.table_height,
            table_unit=table.table_unit,
            deployment=meta.deployment,
            layout=meta.layout,
            objectives=meta.objectives,
            initial_priority=meta.initial_priority,
            special_rules_state=rules.special_rules_state,
            visibility=vis.visibility,
            shared_with=vis.shared_with,
            scenography_state=scenography_ctx.scenography_state,
            deployment_zones_state=deployment_ctx.deployment_zones_state,
            objective_points_state=obj.objective_points_state,
            objectives_with_vp_toggle=vp.objectives_with_vp_toggle,
            vp_state=vp.vp_state,
            generate_btn=gen.generate_btn,
            svg_preview=gen.svg_preview,
            output=gen.output,
            preview_full_state=gen.preview_full_state,
            create_scenario_btn=gen.create_scenario_btn,
            create_scenario_status=gen.create_scenario_status,
            page_state=gen.page_state,
            page_containers=gen.page_containers,
            home_recent_html=gen.home_recent_html,
            home_page_info=gen.home_page_info,
            home_page_state=gen.home_page_state,
            home_cards_cache_state=gen.home_cards_cache_state,
            home_fav_ids_cache_state=gen.home_fav_ids_cache_state,
            vp_input=vp.vp_input,
            vp_list=vp.vp_list,
            rules_list=rules.rules_list,
            scenography_list=scenography_ctx.scenography_list,
            deployment_zones_list=deployment_ctx.deployment_zones_list,
            objective_points_list=obj.objective_points_list,
            editing_card_id=gen.editing_card_id,
            create_heading_md=gen.create_heading_md,
        )
    )
