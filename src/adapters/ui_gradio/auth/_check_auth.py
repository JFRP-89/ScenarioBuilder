"""Cookie-based session check for Gradio page loads.

Validates the ``sb_session`` HttpOnly cookie on page load so
the correct page and auth state are shown immediately.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.auth._check_logic import (
    parse_referer_routing,
    validate_session_cookie,
)
from adapters.ui_gradio.auth._service import get_logged_in_label


def check_auth(request: gr.Request):
    """Validate the ``sb_session`` HttpOnly cookie on page load.

    If the cookie carries a valid session, populate actor/session state
    and show the main UI.  Also reads the ``?page=`` query parameter from
    the browser ``Referer`` header so that the correct page container is
    shown immediately (e.g. after F5 on ``/sb/myscenarios/``).

    For the detail page (``scenario_detail``) the ``?id=`` query param
    is also extracted so the card content reloads on F5.

    Otherwise show the authentication-required gate with a login link.

    Returns a tuple of N outputs:
        page_state, detail_card_id_state, detail_reload_trigger,
        editing_card_id, editing_reload_trigger,
        actor_id_state, session_id_state, actor_id textbox,
        user_label, auth_gate, top_bar_row, *page_containers (one per page).
    """
    from adapters.ui_gradio.ui.router import (
        ALL_PAGES,
        PAGE_CREATE,
        PAGE_DETAIL,
        PAGE_EDIT,
        PAGE_HOME,
        URL_TO_PAGE,
    )

    def _page_visibility(target: str) -> list:
        """Return visibility updates for all page containers."""
        effective = PAGE_CREATE if target == PAGE_EDIT else target
        return [gr.update(visible=(p == effective)) for p in ALL_PAGES]

    session_id = request.cookies.get("sb_session", "")
    session_data = validate_session_cookie(session_id)

    if session_data is not None:
        actor_id = session_data["actor_id"]
        referer = request.headers.get("referer", "")

        initial_page, card_id_from_url, editing_id_from_url = parse_referer_routing(
            referer,
            ALL_PAGES,
            URL_TO_PAGE,
            PAGE_HOME,
            PAGE_DETAIL,
            PAGE_EDIT,
        )

        reload_trigger = 1 if card_id_from_url else gr.update()
        edit_reload = 1 if editing_id_from_url else gr.update()

        return (
            initial_page,
            card_id_from_url or gr.update(),
            reload_trigger,
            editing_id_from_url or gr.update(),
            edit_reload,
            actor_id,
            session_id,
            gr.update(value=actor_id),
            gr.update(value=get_logged_in_label(actor_id)),
            gr.update(visible=False),
            gr.update(visible=True),
            *_page_visibility(initial_page),
        )

    # Not authenticated — show the auth gate, hide everything else
    return (
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        "",
        "",
        gr.update(),
        gr.update(),
        gr.update(visible=True),
        gr.update(visible=False),
        *_page_visibility("__none__"),
    )
