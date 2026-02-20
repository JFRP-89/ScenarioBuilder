"""Pure helpers for cookie-based session / routing logic.

Extracted from ``_check_auth.check_auth`` to reduce cyclomatic complexity.
All helpers are pure (no Gradio imports) and independently testable.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def validate_session_cookie(
    session_id: str,
) -> dict[str, str] | None:
    """Validate a session cookie and return session data or *None*.

    Returns ``{"actor_id": ..., "session_id": ...}`` on success.
    """
    if not session_id:
        return None

    from infrastructure.auth.session_store import get_session

    session = get_session(session_id)
    if session is None:
        return None

    return {"actor_id": session["actor_id"], "session_id": session_id}


def parse_referer_routing(
    referer: str,
    all_pages: list[str],
    url_to_page: dict[str, str],
    page_home: str,
    page_detail: str,
    page_edit: str,
) -> tuple[str, str, str]:
    """Parse referer URL to determine target page and card IDs.

    Returns ``(initial_page, card_id_from_url, editing_id_from_url)``.
    """
    initial_page = page_home
    card_id_from_url = ""
    editing_id_from_url = ""

    if not referer:
        return initial_page, card_id_from_url, editing_id_from_url

    parsed = urlparse(referer)
    qs = parse_qs(parsed.query)

    # 1) Check ?page= query param (redirect from /sb/create/)
    qp = qs.get("page", [None])[0]
    if qp and qp in all_pages:
        initial_page = qp
    # 2) Check path directly (e.g. /sb/myfavorites/)
    elif parsed.path:
        path_norm = parsed.path.rstrip("/") + "/"
        matched = url_to_page.get(path_norm)
        if matched and matched in all_pages:
            initial_page = matched

    # 3) Extract card_id for detail page
    if initial_page == page_detail:
        cid = qs.get("id", [None])[0]
        if cid and cid.strip():
            card_id_from_url = cid.strip()

    # 4) Extract card_id for edit page
    if initial_page == page_edit:
        cid = qs.get("id", [None])[0]
        if cid and cid.strip():
            editing_id_from_url = cid.strip()

    return initial_page, card_id_from_url, editing_id_from_url
