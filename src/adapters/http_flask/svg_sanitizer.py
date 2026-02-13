"""SVG sanitization and validation (XSS / XXE prevention).

Extracted from cards route to follow SRP — route handlers only translate
HTTP ↔ use-case DTOs; sanitization lives here.
"""

from __future__ import annotations

import re
from typing import cast

from defusedxml import ElementTree as DET
from defusedxml.ElementTree import fromstring as defused_fromstring
from domain.errors import ValidationError

# ── XXE prevention ──────────────────────────────────────────────────


def _validate_no_dangerous_xml_entities(svg: str) -> None:
    """Validate SVG does not contain dangerous XML entities (XXE prevention).

    Args:
        svg: SVG string to validate.

    Raises:
        ValidationError: If DOCTYPE or ENTITY declarations are found.
    """
    if re.search(r"<!DOCTYPE", svg, re.IGNORECASE):
        raise ValidationError("SVG must not contain DOCTYPE declarations")

    if re.search(r"<!ENTITY", svg, re.IGNORECASE):
        raise ValidationError("SVG must not contain ENTITY declarations")


# ── Namespace stripping ─────────────────────────────────────────────


def _strip_svg_namespaces_inplace(element: DET.Element) -> None:
    """Strip namespaces from SVG element tree (in-place modification).

    Converts tags like ``{http://www.w3.org/2000/svg}rect`` to ``rect``.
    This ensures deterministic serialization without ns0: prefixes.
    """
    if "}" in element.tag:
        element.tag = element.tag.split("}", 1)[1]

    for attr_name in list(element.attrib.keys()):
        if "}" in attr_name:
            clean_name = attr_name.split("}", 1)[1]
            element.attrib[clean_name] = element.attrib.pop(attr_name)

    for child in element:
        _strip_svg_namespaces_inplace(child)


def _local_svg_name(name: str) -> str:
    """Strip SVG namespace from tag/attribute name."""
    return name.split("}")[-1] if "}" in name else name


# ── Allowlist validation ────────────────────────────────────────────


def _allowed_svg_attrs() -> dict[str, set[str]]:
    """Return allowed attributes per tag (safe presentation subset)."""
    _common_paint = {"fill", "stroke", "stroke-width"}
    return {
        "svg": {"xmlns", "width", "height", "viewBox"},
        "rect": {"x", "y", "width", "height"} | _common_paint,
        "circle": {"cx", "cy", "r"} | _common_paint,
        "polygon": {"points"} | _common_paint,
        "text": {
            "x",
            "y",
            "fill",
            "font-size",
            "font-family",
            "text-anchor",
            "dominant-baseline",
            "font-weight",
        },
        "g": {"transform"},
    }


def _enforce_svg_tag_allowed(tag: str) -> None:
    """Enforce allowlist for SVG tags."""
    allowed_tags = {"svg", "rect", "circle", "polygon", "text", "g"}
    if tag not in allowed_tags:
        raise ValidationError(f"SVG contains forbidden tag: <{tag}>")


def _validate_svg_numeric_attr(tag: str, attr_name: str, attr_value: str) -> None:
    """Validate numeric SVG attribute values for specific tags."""
    _NUMERIC_ATTRS = {"x", "y", "width", "height", "cx", "cy", "r"}
    if attr_name not in _NUMERIC_ATTRS:
        return

    if attr_name == "viewBox":
        parts = attr_value.strip().split()
        if len(parts) != 4 or any(not p.lstrip("-").isdigit() for p in parts):
            raise ValidationError("SVG viewBox must be 4 integers")
        return

    if not attr_value.strip().lstrip("-").isdigit():
        raise ValidationError(f"SVG attribute '{attr_name}' must be an integer")


def _validate_svg_polygon_points(attr_value: str) -> None:
    """Validate polygon points characters (digits, spaces, commas, minus only)."""
    for ch in attr_value:
        if ch.isdigit() or ch in {" ", ",", "-"}:
            continue
        raise ValidationError("SVG polygon points contain invalid characters")


def _validate_paint_value(attr_name: str, attr_value: str) -> None:
    """Validate fill/stroke values don't contain dangerous references."""
    lower = attr_value.lower()
    if "url(" in lower or "javascript:" in lower or "expression(" in lower:
        raise ValidationError(
            f"SVG attribute '{attr_name}' contains forbidden reference"
        )


def _validate_svg_attribute(
    tag: str,
    attr_name: str,
    attr_value: str,
    allowed_for_tag: set[str],
) -> None:
    """Validate a single SVG attribute against allowlist rules."""
    clean_attr = _local_svg_name(attr_name)
    lower_attr = clean_attr.lower()

    if lower_attr.startswith("on"):
        raise ValidationError(
            f"SVG contains forbidden event handler attribute: {clean_attr}"
        )

    if lower_attr in {"href", "xlink:href", "src"}:
        raise ValidationError(
            f"SVG must not contain external reference attribute: {clean_attr}"
        )

    if lower_attr in {"style", "class"}:
        raise ValidationError(f"SVG must not contain styling attribute: {clean_attr}")

    if clean_attr not in allowed_for_tag:
        raise ValidationError(
            f"SVG contains forbidden attribute '{clean_attr}' on <{tag}>"
        )

    if lower_attr in {"fill", "stroke"}:
        _validate_paint_value(clean_attr, attr_value)

    _validate_svg_numeric_attr(tag, clean_attr, attr_value)

    if tag == "polygon" and clean_attr == "points":
        _validate_svg_polygon_points(attr_value)


def _validate_svg_allowlist(element: DET.Element) -> None:
    """Strict SVG allowlist validation (XSS prevention).

    Allows only the minimal SVG subset we generate (svg/rect/circle/polygon)
    and only safe attributes. Everything else is rejected.
    """
    tag = _local_svg_name(element.tag)
    _enforce_svg_tag_allowed(tag)

    allowed_for_tag = _allowed_svg_attrs().get(tag, set())
    for attr_name, attr_value in element.attrib.items():
        _validate_svg_attribute(tag, attr_name, attr_value, allowed_for_tag)

    for child in list(element):
        _validate_svg_allowlist(child)


# ── Public API ──────────────────────────────────────────────────────


def normalize_svg_xml(svg: str) -> str:
    """Normalize SVG via XML parsing and re-serialization.

    This ensures the SVG is well-formed XML and removes potential XSS vectors.

    Uses defusedxml to prevent XXE attacks (safer than stdlib ET.fromstring).
    Validates SVG content against allowlist to block XSS vectors.
    Strips namespaces to ensure deterministic output without ns0: prefixes.

    Args:
        svg: SVG string from renderer.

    Returns:
        Normalized SVG string (always contains literal ``<svg>``, not ``<ns0:svg>``).

    Raises:
        ValidationError: If SVG is not well-formed XML or contains dangerous content.
    """
    try:
        _validate_no_dangerous_xml_entities(svg)
        root = defused_fromstring(svg)
        _validate_svg_allowlist(root)
        _strip_svg_namespaces_inplace(root)
        return cast(str, DET.tostring(root, encoding="unicode", method="xml"))

    except DET.ParseError as e:
        raise ValidationError(f"Invalid SVG XML: {e}") from e
    except ValidationError:
        raise
    except Exception as e:
        if "defusedxml" in type(e).__module__ or "Forbidden" in type(e).__name__:
            raise ValidationError(f"SVG contains forbidden XML features: {e}") from e
        raise ValidationError(f"SVG parsing failed: {e}") from e
