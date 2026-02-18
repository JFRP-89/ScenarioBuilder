"""Parameter Object for generate-service form state.

Groups the 22 discrete Gradio UI fields into a single dataclass
so that ``_prepare_payload``, ``handle_preview``, and ``handle_generate``
each accept **one** ``FormState`` instead of 22 positional parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FormState:
    """Immutable snapshot of every Gradio form field needed to generate a card.

    Field order matches the Gradio ``inputs`` list in ``wire_generate.py``
    so that ``FormState(*args)`` works when ``args`` comes from Gradio.
    """

    actor: str
    name: str
    mode: str
    is_replicable: bool
    generate_from_seed: float | None
    armies_val: str
    preset: str
    width: float
    height: float
    unit: str
    depl: str
    lay: str
    obj: str
    init_priority: str
    rules_state: list[dict[str, Any]]
    vis: str
    shared: str
    scenography_state_val: list[dict[str, Any]]
    deployment_zones_state_val: list[dict[str, Any]]
    objective_points_state_val: list[dict[str, Any]]
    objectives_with_vp_enabled: bool
    vp_state: list[dict[str, Any]]
