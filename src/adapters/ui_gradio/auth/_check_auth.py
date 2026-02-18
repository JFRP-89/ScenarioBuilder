"""Cookie-based session check for Gradio page loads.

Validates the ``sb_session`` HttpOnly cookie on page load so
the correct page and auth state are shown immediately.
"""

from __future__ import annotations

import gradio as gr
from adapters.ui_gradio.auth._service import get_logged_in_label


def check_auth(request: gr.Request):  # noqa: C901
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
        # Edit mode reuses the create form container
        effective = PAGE_CREATE if target == PAGE_EDIT else target
        return [gr.update(visible=(p == effective)) for p in ALL_PAGES]

    session_id = request.cookies.get("sb_session", "")
    if session_id:
        from infrastructure.auth.session_store import get_session

        session = get_session(session_id)
        if session is not None:
            actor_id = session["actor_id"]

            # ── Determine initial page + card_id from Referer URL ─
            initial_page = PAGE_HOME
            card_id_from_url = ""
            editing_id_from_url = ""
            referer = request.headers.get("referer", "")
            if referer:
                from urllib.parse import parse_qs, urlparse

                parsed = urlparse(referer)
                qs = parse_qs(parsed.query)

                # 1) Check ?page= query param  (redirect from /sb/create/)
                qp = qs.get("page", [None])[0]
                if qp and qp in ALL_PAGES:
                    initial_page = qp
                # 2) Check path directly  (e.g. /sb/myfavorites/)
                elif parsed.path:
                    path_norm = parsed.path.rstrip("/") + "/"
                    matched = URL_TO_PAGE.get(path_norm)
                    if matched and matched in ALL_PAGES:
                        initial_page = matched

                # 3) Extract card_id for detail page
                if initial_page == PAGE_DETAIL:
                    cid = qs.get("id", [None])[0]
                    if cid and cid.strip():
                        card_id_from_url = cid.strip()

                # 4) Extract card_id for edit page
                if initial_page == PAGE_EDIT:
                    cid = qs.get("id", [None])[0]
                    if cid and cid.strip():
                        editing_id_from_url = cid.strip()

            # detail_reload_trigger: bump to 1 so the .change handler fires
            reload_trigger = 1 if card_id_from_url else gr.update()

            # editing_reload_trigger: bump to 1 so the edit form repopulates
            edit_reload = 1 if editing_id_from_url else gr.update()

            return (
                initial_page,  # page_state
                card_id_from_url or gr.update(),  # detail_card_id_state
                reload_trigger,  # detail_reload_trigger
                editing_id_from_url or gr.update(),  # editing_card_id
                edit_reload,  # editing_reload_trigger
                actor_id,  # actor_id_state
                session_id,  # session_id_state
                gr.update(value=actor_id),  # actor_id textbox
                gr.update(value=get_logged_in_label(actor_id)),  # user_label
                gr.update(visible=False),  # auth_gate → hide
                gr.update(visible=True),  # top_bar_row → show
                *_page_visibility(initial_page),  # page containers
            )

    # Not authenticated — show the auth gate, hide everything else
    return (
        gr.update(),  # page_state (unchanged)
        gr.update(),  # detail_card_id_state (unchanged)
        gr.update(),  # detail_reload_trigger (unchanged)
        gr.update(),  # editing_card_id (unchanged)
        gr.update(),  # editing_reload_trigger (unchanged)
        "",  # actor_id_state
        "",  # session_id_state
        gr.update(),  # actor_id textbox
        gr.update(),  # user_label
        gr.update(visible=True),  # auth_gate → show
        gr.update(visible=False),  # top_bar_row → hide
        *_page_visibility("__none__"),  # hide all page containers
    )
