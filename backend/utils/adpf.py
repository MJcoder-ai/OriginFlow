"""
Helper functions and schema definitions for integrating the Advanced Dynamic Prompting Framework (ADPF).

This module defines a simple wrapper to produce a standard JSON envelope
around agent responses.  The envelope captures the agent's internal thought,
the structured output (e.g. design card and patch), and the overall status.

Integrating with the ADPF requires that every agent return a well‑formed JSON
object.  See `wrap_response` for usage.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List


def wrap_response(
    *,
    thought: str,
    card: Optional[Dict[str, Any]],
    patch: Optional[Dict[str, Any]],
    status: str,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Wrap an agent response into the ADPF JSON envelope.

    The returned dictionary has the following keys:

    - ``thought``: a short string summarising the agent's internal reasoning.
    - ``output``: a dictionary containing the ``card`` and ``patch``.
    - ``card``/``patch``: duplicated at the top level for backward
      compatibility with pre‑ADPF responses.
    - ``status``: one of ``pending``, ``blocked`` or ``complete``.
    - ``warnings``: an optional list of cautionary messages.

    Args:
        thought: A plain‑English description of what the agent did or why it failed.
        card: The rich design card returned by the agent (may be ``None``).
        patch: The ODL patch to apply (may be ``None``).
        status: The outcome status of the task.
        warnings: Optional list of warning strings.

    Returns:
        A dictionary conforming to the ADPF standard envelope.
    """
    envelope: Dict[str, Any] = {
        "thought": thought,
        "output": {
            "card": card,
            "patch": patch,
        },
        "status": status,
    }

    # Expose card and patch at the top level for backward compatibility
    envelope["card"] = card
    envelope["patch"] = patch

    if warnings:
        envelope["warnings"] = warnings

    return envelope

