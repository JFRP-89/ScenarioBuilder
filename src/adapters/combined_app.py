"""Combined application — Flask (auth/API) + Gradio (UI) on same origin.

Mounts Flask (WSGI) and Gradio under a single FastAPI/ASGI container so
that HttpOnly cookies set by Flask on ``/auth/login`` travel automatically
to Gradio at ``/sb/``.

Routing priority:
1. ``GET /``  → redirect to ``/sb/``
2. ``/sb/**`` → Gradio Blocks application (with sub-route redirects)
3. Everything else (``/auth/*``, ``/cards/*``, ``/health``, ``/login``, …) → Flask
"""

from __future__ import annotations

import gradio as gr
from a2wsgi import WSGIMiddleware
from adapters.http_flask.app import create_app as create_flask_app
from adapters.ui_gradio.app import build_app as build_gradio_app
from adapters.ui_gradio.ui.router import PAGE_TO_URL
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse


def create_combined_app() -> FastAPI:
    """Build the unified ASGI application.

    ``create_flask_app()`` is called first so that ``build_services()``
    initialises the PostgreSQL session store, user seeding, and all
    repository backends **before** Gradio tries to use them.
    """
    # 1. Flask — auth authority + REST API (also triggers build_services())
    flask_app = create_flask_app()

    # 2. Gradio — UI only (no login form, reads cookie on load)
    gradio_blocks = build_gradio_app()

    # 3. FastAPI shell
    main_app = FastAPI(
        title="ScenarioBuilder",
        docs_url=None,
        redoc_url=None,
    )

    # Root redirect → UI
    @main_app.get("/")
    async def _root():
        return RedirectResponse("/sb/")

    # Backwards-compat: old /ui/ path redirects to /sb/
    @main_app.get("/ui")
    @main_app.get("/ui/")
    async def _legacy_ui():
        return RedirectResponse("/sb/", status_code=301)

    # ── Sub-route redirects for SPA URL navigation ───────────────
    # When a user directly enters /sb/create/ etc., the request must
    # reach the Gradio SPA. Gradio is mounted at /sb and serves its
    # HTML from /sb/. The sub-paths carry a ``?page=<name>`` query
    # param that client-side JS reads to show the correct page.
    for page_name, url_path in PAGE_TO_URL.items():
        if url_path == "/sb/":
            continue  # Gradio already serves its root

        # Strip trailing slash for the redirect path
        clean = url_path.rstrip("/")

        # Create closure that captures page_name
        def _make_redirect(pn: str):
            async def _redirect(request: Request):
                target = f"/sb/?page={pn}"
                # Forward extra query params (e.g. ?id=abc for detail page)
                for key, val in request.query_params.items():
                    target += f"&{key}={val}"
                return RedirectResponse(target)

            return _redirect

        # Register both /sb/create and /sb/create/
        main_app.add_api_route(clean, _make_redirect(page_name), methods=["GET"])
        main_app.add_api_route(clean + "/", _make_redirect(page_name), methods=["GET"])

    # Mount Gradio at /sb (ASGI sub-app handled by gradio)
    main_app = gr.mount_gradio_app(main_app, gradio_blocks, path="/sb")

    # Mount Flask as WSGI catch-all (auth, API, /login, /health, etc.)
    main_app.mount("/", WSGIMiddleware(flask_app))  # type: ignore[arg-type]

    return main_app


# ---------------------------------------------------------------------------
# CLI entry-point — ``python -m adapters.combined_app``
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os

    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        create_combined_app(),
        host=host,
        port=port,
    )  # nosec B104 — container / local dev
