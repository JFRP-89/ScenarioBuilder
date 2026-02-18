"""Safe keyword-argument filtering for dynamic ``**`` unpacking.

Prevents the two most common ``wire_events(**ns, ...)`` foot-guns:

* ``TypeError: got an unexpected keyword argument``
* ``TypeError: got multiple values for keyword argument``

And catches missing-required early with a clear message.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable


class KwargsContractError(RuntimeError):
    """Raised when *kwargs_for_call* detects a contract violation."""


def kwargs_for_call(
    payload: dict[str, Any],
    fn: Callable[..., Any],
    *,
    explicit_overrides: set[str] | frozenset[str] = frozenset(),
    strict_extras: bool = False,
) -> dict[str, Any]:
    """Build a safe ``**kwargs`` dict from *payload* for *fn*.

    Parameters
    ----------
    payload:
        Raw key→value mapping (typically ``vars(namespace)``).
    fn:
        The target callable whose signature is inspected.
    explicit_overrides:
        Keys that the caller passes **separately** in the call site
        (e.g. ``page_state``, ``editing_card_id``).  If any of these
        appear in *payload* the call would blow up with *"multiple
        values"*; we raise ``KwargsContractError`` instead.
    strict_extras:
        When *True* **and** *fn* does NOT accept ``**kwargs``, raise
        ``KwargsContractError`` if *payload* contains keys that are not
        in *fn*'s signature.  When *False* (the default) those extras
        are silently dropped.

    Returns
    -------
    dict[str, Any]
        Filtered dictionary ready for ``fn(**result, ...)``.

    Raises
    ------
    KwargsContractError
        On override conflicts, unexpected extras (strict mode) or
        missing required parameters.
    """
    # ── 1. Detect override conflicts ────────────────────────────────
    conflicts = set(payload) & set(explicit_overrides)
    if conflicts:
        raise KwargsContractError(
            f"payload contains keys that are also passed as explicit "
            f"overrides — this would cause 'multiple values' for: "
            f"{sorted(conflicts)}"
        )

    sig = inspect.signature(fn)
    params = sig.parameters

    # Does fn accept **kwargs?
    has_var_keyword = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
    )

    # ── 2. Filter / validate extras ─────────────────────────────────
    accepted_names = set(params) - {
        p.name
        for p in params.values()
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    }

    if has_var_keyword:
        # fn accepts **kwargs → pass everything except overrides
        result = {k: v for k, v in payload.items() if k not in explicit_overrides}
    else:
        extras = set(payload) - accepted_names
        if strict_extras and extras:
            raise KwargsContractError(
                f"{fn.__qualname__}() does not accept **kwargs and "
                f"payload contains unexpected keys: {sorted(extras)}"
            )
        result = {k: v for k, v in payload.items() if k in accepted_names}

    # ── 3. Validate missing required ────────────────────────────────
    required = {
        name
        for name, p in params.items()
        if p.default is inspect.Parameter.empty
        and p.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and name not in explicit_overrides
    }
    missing = required - set(result)
    if missing:
        raise KwargsContractError(
            f"{fn.__qualname__}() is missing required parameters "
            f"(not in payload and not in explicit_overrides): "
            f"{sorted(missing)}"
        )

    return result
