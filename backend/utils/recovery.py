"""Recovery and graceful degradation utilities.

When an agent or orchestrator cannot produce a valid output, a
recovery mechanism should return a simplified envelope indicating
failure and suggesting remedial actions.  This module defines a
helper function for generating such degraded envelopes.  It will be
extended in later sprints to handle partial results and context-aware
fallback strategies.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def recover(out: Optional[Dict[str, Any]], valid: bool, agent: str) -> Dict[str, Any]:
    """Return a degraded envelope when validation fails.

    Args:
        out: The original output from the agent (may be None).
        valid: Whether the original output was considered valid.
        agent: The name of the agent or template that produced the output.

    Returns:
        A simplified envelope containing an error status, an empty result
        and a message indicating that recovery was invoked.
    """
    if valid:
        return out or {}
    # When validation fails, construct a minimal envelope preserving any
    # available validations from the original output.  Metrics are
    # omitted since the result is degraded.  Include a next_actions
    # list to guide the caller.
    return {
        "status": "error",
        "result": None,
        "card": {"template": agent, "confidence": 0.0},
        "metrics": {},
        "validations": (out.get("validations", []) if out else []),
        "errors": [
            f"Output from {agent} failed validation, returned degraded response."
        ],
        "next_actions": ["Review input requirements", "Retry operation"],
    }
