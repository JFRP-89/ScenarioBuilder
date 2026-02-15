"""WSGI entrypoint for production servers (Gunicorn / Waitress).

Usage
-----
**Linux / macOS (Gunicorn)**::

    PYTHONPATH=src gunicorn -w 2 -b 0.0.0.0:8000 adapters.http_flask.wsgi:app

**Windows (Waitress)**::

    $env:PYTHONPATH="src"
    waitress-serve --listen=0.0.0.0:8000 adapters.http_flask.wsgi:app

The module simply instantiates the Flask application via ``create_app()``
and exposes it as ``app`` — the standard WSGI callable that any
PEP-3333 server expects.
"""

from __future__ import annotations

from adapters.http_flask.app import create_app

app = create_app()
