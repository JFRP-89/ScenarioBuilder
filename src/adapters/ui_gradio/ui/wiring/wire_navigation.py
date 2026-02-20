"""Navigation wiring — hooks up all inter-page navigation buttons.

Handles Home, Browse, Create, Favorites, Back buttons across every page.
Each navigation action first checks that the server-side session is still
valid (idle timeout, max lifetime). If expired, the user is returned to
the login screen.

When navigating to the Create page via ``home_create_btn``, the entire
form is reset so that stale data from a previous edit session is cleared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import is_session_valid
from adapters.ui_gradio.ui.router import (
    PAGE_CREATE,
    PAGE_FAVORITES,
    PAGE_HOME,
    PAGE_LIST,
    navigate_to,
)
from adapters.ui_gradio.ui.wiring._generate._resets import (
    build_dropdown_resets,
    build_extra_resets,
    build_form_resets,
)


def _expired_result(
    n_page_containers: int,
) -> tuple[Any, ...]:
    """Return outputs that hide everything and show the login panel.

    Output order matches ``nav_outputs_with_session``:
    ``[page_state, *page_containers, session_id_state, actor_id_state,
       login_panel, top_bar_row, login_message]``
    """
    return (
        PAGE_HOME,  # page_state → reset
        # hide every page container
        *(gr.update(visible=False) for _ in range(n_page_containers)),
        "",  # session_id_state → cleared
        "",  # actor_id_state → cleared
        gr.update(visible=True),  # login_panel / auth_gate → show
        gr.update(visible=False),  # top_bar_row → hide
        gr.update(
            value='Session expired \u2014 please <a href="/login">log in</a> again.',
        ),  # login_message / auth_message
    )


def _wire_create_button(
    *,
    home_create_btn: gr.Button,
    session_id_state: gr.State,
    nav_outputs_with_session: list[gr.components.Component],
    guarded_nav_fn: Any,
    n_page_containers: int,
    create_form_components: list[gr.components.Component] | None,
    create_dropdown_lists: list[gr.components.Component] | None,
    editing_card_id: gr.Textbox | None,
    create_heading_md: gr.Markdown | None,
    create_scenario_btn: gr.Button | None = None,
) -> None:
    """Wire the Home → Create button, optionally resetting form state."""
    _form = create_form_components or []
    _dropdowns = create_dropdown_lists or []
    _extra: list[gr.components.Component] = []
    if editing_card_id is not None:
        _extra.append(editing_card_id)
    if create_heading_md is not None:
        _extra.append(create_heading_md)
    if create_scenario_btn is not None:
        _extra.append(create_scenario_btn)

    if not _form:
        home_create_btn.click(
            fn=lambda sid: guarded_nav_fn(PAGE_CREATE, sid),
            inputs=[session_id_state],
            outputs=nav_outputs_with_session,
        )
        return

    create_outputs = [*nav_outputs_with_session, *_form, *_dropdowns, *_extra]

    def _guarded_create(sid: str) -> tuple[Any, ...]:
        n_reset = len(_form) + len(_dropdowns) + len(_extra)
        if not is_session_valid(sid):
            return (
                *_expired_result(n_page_containers),
                *(gr.update() for _ in range(n_reset)),
            )
        page_val, *vis = navigate_to(PAGE_CREATE)
        nav = (
            page_val,
            *vis,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )
        return (
            *nav,
            *build_form_resets(),
            *build_dropdown_resets(_dropdowns),
            *build_extra_resets(
                has_editing_card_id=editing_card_id is not None,
                has_create_heading_md=create_heading_md is not None,
                has_create_scenario_btn=create_scenario_btn is not None,
            ),
        )

    home_create_btn.click(
        fn=_guarded_create,
        inputs=[session_id_state],
        outputs=create_outputs,
    )


@dataclass(frozen=True)
class NavigationCtx:
    """Widget references for navigation wiring."""

    page_state: gr.State
    previous_page_state: gr.State
    page_containers: list[gr.Column]
    home_create_btn: gr.Button
    list_back_btn: gr.Button
    detail_back_btn: gr.Button
    create_back_btn: gr.Button
    edit_back_btn: gr.Button
    favorites_back_btn: gr.Button
    session_id_state: gr.State
    actor_id_state: gr.State
    login_panel: gr.Column
    top_bar_row: gr.Row
    login_message: gr.Textbox
    create_form_components: list[gr.components.Component] | None = None
    create_dropdown_lists: list[gr.components.Component] | None = None
    editing_card_id: gr.Textbox | None = None
    create_heading_md: gr.Markdown | None = None
    create_scenario_btn: gr.Button | None = None
    home_reload_fn: Any | None = None
    home_reload_inputs: list[gr.components.Component] | None = field(default=None)
    home_reload_outputs: list[gr.components.Component] | None = field(default=None)


def wire_navigation(*, ctx: NavigationCtx) -> None:
    """Wire all navigation buttons with session-expiry guard.

    If the session has expired (idle > 15 min or max lifetime > 12 h),
    the user is returned to the login screen instead of navigating.

    When *create_form_components* is supplied, the "Create" button also
    resets all form fields, dropdowns, ``editing_card_id``, and the
    heading so that stale edit data is never carried over.

    Note: ``home_browse_btn`` and ``home_favorites_btn`` are **not**
    wired here.  Their click handlers live in ``wire_list_page`` and
    ``wire_favorites_page`` respectively, which combine navigation with
    data loading in a single callback to avoid race conditions on
    logout.
    """
    n = len(ctx.page_containers)

    # Outputs that every guarded button writes to
    nav_outputs_with_session = [
        ctx.page_state,
        *ctx.page_containers,
        ctx.session_id_state,
        ctx.actor_id_state,
        ctx.login_panel,
        ctx.top_bar_row,
        ctx.login_message,
    ]

    def _guarded_nav(target_page: str, sid: str) -> tuple[Any, ...]:
        """Navigate to *target_page* if session is valid, else expire."""
        if not is_session_valid(sid):
            return _expired_result(n)
        page_val, *vis = navigate_to(target_page)
        return (
            page_val,
            *vis,
            gr.update(),  # session_id_state unchanged
            gr.update(),  # actor_id_state unchanged
            gr.update(),  # login_panel unchanged
            gr.update(),  # top_bar_row unchanged
            gr.update(),  # login_message unchanged
        )

    # Home → Create (Browse and Favorites are handled by their
    # respective wire_*_page functions to avoid dual-handler races.)
    _wire_create_button(
        home_create_btn=ctx.home_create_btn,
        session_id_state=ctx.session_id_state,
        nav_outputs_with_session=nav_outputs_with_session,
        guarded_nav_fn=_guarded_nav,
        n_page_containers=n,
        create_form_components=ctx.create_form_components,
        create_dropdown_lists=ctx.create_dropdown_lists,
        editing_card_id=ctx.editing_card_id,
        create_heading_md=ctx.create_heading_md,
        create_scenario_btn=ctx.create_scenario_btn,
    )

    # Back → Home (with optional data reload)
    _home_back_kwargs: dict[str, Any] = {
        "fn": lambda sid: _guarded_nav(PAGE_HOME, sid),
        "inputs": [ctx.session_id_state],
        "outputs": nav_outputs_with_session,
    }

    for btn in (ctx.list_back_btn, ctx.create_back_btn, ctx.favorites_back_btn):
        event = btn.click(**_home_back_kwargs)
        if ctx.home_reload_fn is not None:
            event.then(
                fn=ctx.home_reload_fn,
                inputs=ctx.home_reload_inputs or [],
                outputs=ctx.home_reload_outputs or [],
            )

    # Back from detail/edit → previous page
    def _guarded_detail_back(from_page: str, sid: str) -> tuple[Any, ...]:
        if not is_session_valid(sid):
            return _expired_result(n)
        target = (
            from_page
            if from_page in (PAGE_HOME, PAGE_LIST, PAGE_FAVORITES)
            else PAGE_LIST
        )
        page_val, *vis = navigate_to(target)
        return (
            page_val,
            *vis,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    ctx.detail_back_btn.click(
        fn=_guarded_detail_back,
        inputs=[ctx.previous_page_state, ctx.session_id_state],
        outputs=nav_outputs_with_session,
    )
    ctx.edit_back_btn.click(
        fn=_guarded_detail_back,
        inputs=[ctx.previous_page_state, ctx.session_id_state],
        outputs=nav_outputs_with_session,
    )
