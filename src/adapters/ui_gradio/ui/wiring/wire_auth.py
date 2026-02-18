"""Auth event wiring — logout, profile, and auth-check on load.

Extracted from ``app.py`` to reduce its size.
"""

from __future__ import annotations

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


def wire_auth_events(
    *,
    app: gr.Blocks,
    # Auth gate
    auth_gate: gr.Column,
    auth_message: gr.Markdown,
    # Top bar
    top_bar_row: gr.Row,
    user_label: gr.Markdown,
    logout_btn: gr.Button,
    profile_btn: gr.Button,
    # Profile panel
    profile_panel: gr.Column,
    profile_username_display: gr.Textbox,
    profile_name_input: gr.Textbox,
    profile_email_input: gr.Textbox,
    profile_save_btn: gr.Button,
    profile_close_btn: gr.Button,
    profile_message: gr.Textbox,
    # Global states
    page_state: gr.State,
    detail_card_id_state: gr.State,
    detail_reload_trigger: gr.State,
    editing_card_id: gr.State,
    editing_reload_trigger: gr.State,
    actor_id_state: gr.State,
    session_id_state: gr.State,
    actor_id_component: gr.Textbox,
    page_containers: list[gr.Column],
    # Home page inputs/outputs needed for the post-auth load
    load_recent_cards_fn: Any,
    home_mode_filter: gr.Radio,
    home_preset_filter: gr.Radio,
    home_unit_selector: gr.Radio,
    home_page_state: gr.State,
    home_search_box: gr.Textbox,
    home_per_page_dropdown: gr.Dropdown,
    home_recent_html: gr.HTML,
    home_page_info: gr.HTML,
    home_cards_cache_state: gr.State,
    home_fav_ids_cache_state: gr.State,
) -> None:
    """Wire logout, profile open/save/close, and auth check on page load."""

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
    _event(logout_btn, "click")(fn=None, js=_LOGOUT_JS)

    # ── Profile open ──────────────────────────────────────────────
    def _open_profile(current_actor: str, sid: str):
        """Open profile panel and load data, with session guard."""
        if not is_session_valid(sid):
            return (
                gr.update(visible=False),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(value="", visible=False),
                "",
                "",
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(
                    value='Session expired \u2014 please <a href="/login">log in</a> again.',
                ),
                *(gr.update(visible=False) for _ in page_containers),
            )
        result = get_profile(current_actor)
        no_change = (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            *(gr.update() for _ in page_containers),
        )
        if result["ok"]:
            profile = result["profile"]
            return (
                gr.update(visible=True),
                gr.update(value=profile["username"]),
                gr.update(value=profile["name"]),
                gr.update(value=profile["email"]),
                gr.update(value="", visible=False),
                *no_change,
            )
        return (
            gr.update(visible=True),
            gr.update(value=current_actor),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value="User not found.", visible=True),
            *no_change,
        )

    _event(profile_btn, "click")(
        fn=_open_profile,
        inputs=[actor_id_state, session_id_state],
        outputs=[
            profile_panel,
            profile_username_display,
            profile_name_input,
            profile_email_input,
            profile_message,
            session_id_state,
            actor_id_state,
            auth_gate,
            top_bar_row,
            auth_message,
            *page_containers,
        ],
    )

    # ── Profile save ──────────────────────────────────────────────
    def _save_profile(current_actor: str, name: str, email: str, sid: str):
        """Save profile changes, with session guard."""
        if not is_session_valid(sid):
            return (
                gr.update(
                    value='Session expired \u2014 please <a href="/login">log in</a> again.',
                    visible=True,
                ),
                "",
                "",
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                *(gr.update(visible=False) for _ in page_containers),
            )
        result = update_profile(current_actor, name, email)
        no_change = (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            *(gr.update() for _ in page_containers),
        )
        return (
            gr.update(value=str(result["message"]), visible=True),
            *no_change,
        )

    _event(profile_save_btn, "click")(
        fn=_save_profile,
        inputs=[
            actor_id_state,
            profile_name_input,
            profile_email_input,
            session_id_state,
        ],
        outputs=[
            profile_message,
            session_id_state,
            actor_id_state,
            profile_panel,
            auth_gate,
            top_bar_row,
            *page_containers,
        ],
    )

    # ── Profile close ─────────────────────────────────────────────
    _event(profile_close_btn, "click")(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[profile_panel],
    )

    # ── Auth check on page load (F5 / refresh) ───────────────────
    auth_load_event = _event(app, "load")(
        fn=check_auth,
        inputs=[],
        outputs=[
            page_state,
            detail_card_id_state,
            detail_reload_trigger,
            editing_card_id,
            editing_reload_trigger,
            actor_id_state,
            session_id_state,
            actor_id_component,
            user_label,
            auth_gate,
            top_bar_row,
            *page_containers,
        ],
    )
    # After successful auth check, load home page content
    auth_load_event.then(
        fn=load_recent_cards_fn,
        inputs=[
            home_mode_filter,
            home_preset_filter,
            home_unit_selector,
            home_page_state,
            home_search_box,
            home_per_page_dropdown,
            actor_id_state,
        ],
        outputs=[
            home_recent_html,
            home_page_info,
            home_page_state,
            home_cards_cache_state,
            home_fav_ids_cache_state,
        ],
    )
