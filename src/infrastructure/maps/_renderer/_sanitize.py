"""SVG attribute sanitisation helpers (stateless, no I/O)."""

from __future__ import annotations

import html
import re

# Regex that validates CSS paint / numeric values safe for SVG attributes.
# Allows: color names, hex (#abc, #aabbcc), rgb/rgba(…), named colours,
# and simple numerics.  Rejects javascript:, expression(, url( etc.
_SAFE_SVG_PAINT_RE = re.compile(
    r"^(?:"
    r"#[0-9a-fA-F]{3,8}"
    r"|rgba?\(\s*[\d.,/%\s]+\)"
    r"|[a-zA-Z]+"
    r"|none"
    r"|transparent"
    r")$"
)
_SAFE_SVG_NUMERIC_RE = re.compile(r"^[\d.]+$")


def escape_text(text: str) -> str:
    """Escape text for safe inclusion in SVG text nodes."""
    return html.escape(str(text), quote=True)


def escape_attr(value: str) -> str:
    """Escape a value for safe inclusion in an SVG attribute."""
    return html.escape(str(value), quote=True)


def safe_paint(value: str, default: str) -> str:
    """Return *value* if it looks like a safe CSS paint; else *default*.

    Blocks ``javascript:``, ``expression(``, ``url(`` and any other
    string that doesn't match normal color/paint syntax.
    """
    if _SAFE_SVG_PAINT_RE.match(value):
        return value
    return default


def safe_numeric(value: str, default: str) -> str:
    """Return *value* if purely numeric; else *default*."""
    if _SAFE_SVG_NUMERIC_RE.match(value):
        return value
    return default
