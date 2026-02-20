"""Auth event wiring — logout, profile, and auth-check on load.

Extracted from ``app.py`` to reduce its size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr
from adapters.ui_gradio.auth import (
    check_auth,
    get_profile,
    is_session_valid,
    update_profile,
)


def _event(component: Any, name: str) -> Any:
    """Access a dynamically-generated Gradio event trigger by name."""
    return getattr(component, name)


@dataclass(frozen=True)
class AuthEventsCtx:
    """Widget references for auth-events wiring."""

    app: gr.Blocks
    auth_gate: gr.Column
    auth_message: gr.Markdown
    top_bar_row: gr.Row
    user_label: gr.Markdown
    logout_btn: gr.Button
    profile_btn: gr.Button
    profile_panel: gr.Column
    profile_username_display: gr.Textbox
    profile_name_input: gr.Textbox
    profile_email_input: gr.Textbox
    profile_pw_input: gr.Textbox
    profile_pw_confirm_input: gr.Textbox
    profile_save_btn: gr.Button
    profile_close_btn: gr.Button
    profile_message: gr.Textbox
    page_state: gr.State
    detail_card_id_state: gr.Textbox
    detail_reload_trigger: gr.State
    editing_card_id: gr.Textbox
    editing_reload_trigger: gr.State
    actor_id_state: gr.State
    session_id_state: gr.State
    actor_id_component: gr.Textbox
    page_containers: list[gr.Column]
    load_recent_cards_fn: Any
    home_mode_filter: gr.Radio
    home_preset_filter: gr.Radio
    home_unit_selector: gr.Radio
    home_page_state: gr.State
    home_search_box: gr.Textbox
    home_per_page_dropdown: gr.Dropdown
    home_recent_html: gr.HTML
    home_page_info: gr.HTML
    home_cards_cache_state: gr.State
    home_fav_ids_cache_state: gr.State


def wire_auth_events(*, ctx: AuthEventsCtx) -> None:
    """Wire logout, profile open/save/close, and auth check on page load."""
    c = ctx

    # ── Logout via JavaScript ─────────────────────────────────────
    _LOGOUT_JS = """
    () => {
        const m = document.cookie.match(/sb_csrf=([^;]+)/);
        const csrf = m ? m[1] : "";
        fetch("/auth/logout", {
            method: "POST",
            headers: {"X-CSRF-Token": csrf},
            credentials: "same-origin"
        }).finally(() => { window.location.href = "/login"; });
    }
    """
    _event(c.logout_btn, "click")(fn=None, js=_LOGOUT_JS)

    # ── Profile open ──────────────────────────────────────────────
    def _open_profile(current_actor: str, sid: str):
        """Open profile panel and load data, with session guard."""
        if not is_session_valid(sid):
            return (
                gr.update(visible=False),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value="", visible=False),
                "",
                "",
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(
                    value='Session expired \u2014 please <a href="/login">log in</a> again.',
                ),
                *(gr.update(visible=False) for _ in c.page_containers),
            )
        result = get_profile(current_actor)
        no_change = (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            *(gr.update() for _ in c.page_containers),
        )
        if result["ok"]:
            profile = result["profile"]
            return (
                gr.update(visible=True),
                gr.update(value=profile["username"]),
                gr.update(value=profile["name"]),
                gr.update(value=profile["email"]),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value="", visible=False),
                *no_change,
            )
        return (
            gr.update(visible=True),
            gr.update(value=current_actor),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value="User not found.", visible=True),
            *no_change,
        )

    _event(c.profile_btn, "click")(
        fn=_open_profile,
        inputs=[c.actor_id_state, c.session_id_state],
        outputs=[
            c.profile_panel,
            c.profile_username_display,
            c.profile_name_input,
            c.profile_email_input,
            c.profile_pw_input,
            c.profile_pw_confirm_input,
            c.profile_message,
            c.session_id_state,
            c.actor_id_state,
            c.auth_gate,
            c.top_bar_row,
            c.auth_message,
            *c.page_containers,
        ],
    )

    # ── Profile save ──────────────────────────────────────────────
    def _save_profile(
        current_actor: str,
        name: str,
        email: str,
        new_pw: str,
        confirm_pw: str,
        sid: str,
    ):
        """Save profile changes, with session guard."""
        if not is_session_valid(sid):
            return (
                gr.update(
                    value='Session expired \u2014 please <a href="/login">log in</a> again.',
                    visible=True,
                ),
                gr.update(value=""),
                gr.update(value=""),
                "",
                "",
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                *(gr.update(visible=False) for _ in c.page_containers),
            )
        result = update_profile(current_actor, name, email, new_pw, confirm_pw)
        no_change = (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            *(gr.update() for _ in c.page_containers),
        )
        # Clear password fields on success
        if result["ok"]:
            return (
                gr.update(value=str(result["message"]), visible=True),
                gr.update(value=""),
                gr.update(value=""),
                *no_change,
            )
        return (
            gr.update(value=str(result["message"]), visible=True),
            gr.update(),
            gr.update(),
            *no_change,
        )

    _event(c.profile_save_btn, "click")(
        fn=_save_profile,
        inputs=[
            c.actor_id_state,
            c.profile_name_input,
            c.profile_email_input,
            c.profile_pw_input,
            c.profile_pw_confirm_input,
            c.session_id_state,
        ],
        outputs=[
            c.profile_message,
            c.profile_pw_input,
            c.profile_pw_confirm_input,
            c.session_id_state,
            c.actor_id_state,
            c.profile_panel,
            c.auth_gate,
            c.top_bar_row,
            *c.page_containers,
        ],
    )

    # ── Profile close ─────────────────────────────────────────────
    _event(c.profile_close_btn, "click")(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[c.profile_panel],
    )

    # ── Auth check on page load (F5 / refresh) ───────────────────
    auth_load_event = _event(c.app, "load")(
        fn=check_auth,
        inputs=[],
        outputs=[
            c.page_state,
            c.detail_card_id_state,
            c.detail_reload_trigger,
            c.editing_card_id,
            c.editing_reload_trigger,
            c.actor_id_state,
            c.session_id_state,
            c.actor_id_component,
            c.user_label,
            c.auth_gate,
            c.top_bar_row,
            *c.page_containers,
        ],
    )
    # After successful auth check, load home page content
    auth_load_event.then(
        fn=c.load_recent_cards_fn,
        inputs=[
            c.home_mode_filter,
            c.home_preset_filter,
            c.home_unit_selector,
            c.home_page_state,
            c.home_search_box,
            c.home_per_page_dropdown,
            c.actor_id_state,
        ],
        outputs=[
            c.home_recent_html,
            c.home_page_info,
            c.home_page_state,
            c.home_cards_cache_state,
            c.home_fav_ids_cache_state,
        ],
    )
