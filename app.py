import os
import sys

from adapters.http_flask.app import create_app

# app.py (repo root)

ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

app = create_app()
