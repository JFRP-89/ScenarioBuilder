"""Auth-related UI components: gate, top bar, profile panel.

Extracted from ``app.py`` so the main module stays lean.
"""

from __future__ import annotations

import gradio as gr


def build_auth_gate() -> tuple[gr.Column, gr.Markdown]:
    """Build the authentication-required gate shown for unauthenticated users.

    Returns
    -------
    tuple
        (auth_gate, auth_message)
    """
    with gr.Column(visible=False, elem_id="auth-gate") as auth_gate:
        gr.Markdown("## Scenario Card Generator — Authentication Required")
        auth_message = gr.Markdown(
            'You are not logged in. Please <a href="/login">log in</a> ' "to continue.",
            elem_id="auth-message",
        )
    return auth_gate, auth_message


def build_top_bar() -> tuple[gr.Row, gr.Markdown, gr.Button, gr.Button]:
    """Build the top bar with user label, profile and logout buttons.

    Returns
    -------
    tuple
        (top_bar_row, user_label, profile_btn, logout_btn)
    """
    with gr.Row(visible=False, elem_id="top-bar") as top_bar_row:
        user_label = gr.Markdown(
            value="",
            elem_id="user-label",
        )
        profile_btn = gr.Button(
            "👤 Profile",
            variant="secondary",
            size="sm",
            elem_id="profile-btn",
        )
        logout_btn = gr.Button(
            "🚪 Logout",
            variant="secondary",
            size="sm",
            elem_id="logout-btn",
        )
    return top_bar_row, user_label, profile_btn, logout_btn


def build_profile_panel() -> tuple[
    gr.Column,
    gr.Textbox,
    gr.Textbox,
    gr.Textbox,
    gr.Button,
    gr.Button,
    gr.Textbox,
]:
    """Build the profile editing panel (hidden by default).

    Returns
    -------
    tuple
        (profile_panel, profile_username_display, profile_name_input,
         profile_email_input, profile_save_btn, profile_close_btn,
         profile_message)
    """
    with gr.Column(visible=False, elem_id="profile-panel") as profile_panel:
        gr.Markdown("### Profile")
        profile_username_display = gr.Textbox(
            label="Username",
            interactive=False,
            elem_id="profile-username",
        )
        profile_name_input = gr.Textbox(
            label="Display Name",
            elem_id="profile-name",
        )
        profile_email_input = gr.Textbox(
            label="Email",
            elem_id="profile-email",
        )
        with gr.Row():
            profile_save_btn = gr.Button(
                "Save",
                variant="primary",
                size="sm",
                elem_id="profile-save-btn",
            )
            profile_close_btn = gr.Button(
                "Close",
                variant="secondary",
                size="sm",
                elem_id="profile-close-btn",
            )
        profile_message = gr.Textbox(
            label="",
            interactive=False,
            visible=False,
            elem_id="profile-message",
        )
    return (
        profile_panel,
        profile_username_display,
        profile_name_input,
        profile_email_input,
        profile_save_btn,
        profile_close_btn,
        profile_message,
    )
