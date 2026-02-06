"""Backward-compatible re-exports for tests.

This module exists solely so that existing test imports of underscore-prefixed
helpers (e.g. ``_convert_to_cm``, ``_on_table_preset_change``) keep working
after those symbols were removed from ``app.py``.

No logic lives here - only aliases.
"""

from adapters.ui_gradio.api_client import build_headers as _build_headers
from adapters.ui_gradio.api_client import get_api_base_url as _get_api_base_url
from adapters.ui_gradio.state_helpers import (
    get_default_actor_id as _get_default_actor_id,
)
from adapters.ui_gradio.ui.wiring import (
    _on_table_preset_change as _on_table_preset_change,
)
from adapters.ui_gradio.ui.wiring import (
    _on_table_unit_change as _on_table_unit_change,
)
from adapters.ui_gradio.units import (
    build_custom_table_payload as _build_custom_table_payload,
)
from adapters.ui_gradio.units import convert_from_cm as _convert_from_cm
from adapters.ui_gradio.units import convert_to_cm as _convert_to_cm
from adapters.ui_gradio.units import (
    convert_unit_to_unit as _convert_unit_to_unit,
)

__all__ = [
    "_build_custom_table_payload",
    "_build_headers",
    "_convert_from_cm",
    "_convert_to_cm",
    "_convert_unit_to_unit",
    "_get_api_base_url",
    "_get_default_actor_id",
    "_on_table_preset_change",
    "_on_table_unit_change",
]
