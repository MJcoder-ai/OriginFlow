"""
ADPF (Agentic Design Protocol Format) helpers.

This module defines a **single** response envelope for all AI actions and
tool invocations.  It intentionally **does not** mirror fields for legacy
clients.  The goal is a clean, unambiguous contract:

{
  "thought": "short rationale for auditability",
  "output": {
    "card":  { ... optional UI guidance ... },
    "patch": { ... optional ODL patch ... }
  },
  "status":   "pending|blocked|complete",
  "warnings": [ ... optional list ... ]
}

Notes:
- `thought` is a short rationale string suitable for audit logs. It should
  be compact (one or two sentences).
- `output.card` is optional; use for UI surfacing.
- `output.patch` is optional; contains an ODL patch to apply.
- `status` must be one of: "pending" | "blocked" | "complete".
- `warnings` is optional.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

VALID_STATUSES = {"pending", "blocked", "complete"}


def wrap_response(
    *,
    thought: str,
    card: Optional[Dict[str, Any]] = None,
    patch: Optional[Dict[str, Any]] = None,
    status: str = "pending",
    warnings: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Build a response envelope (no legacy duplication).

    Args:
        thought: Short rationale for auditability. Keep it concise.
        card: Optional UI guidance payload (rendered by the client).
        patch: Optional ODL patch to apply to the current design graph.
        status: "pending" | "blocked" | "complete".
        warnings: Optional list of human-readable warning strings.

    Returns:
        A dict matching the ADPF envelope contract.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}.")

    output: Dict[str, Any] = {}
    if card is not None:
        output["card"] = card
    if patch is not None:
        output["patch"] = patch

    env: Dict[str, Any] = {
        "thought": thought,
        "output": output,
        "status": status,
    }
    if warnings:
        env["warnings"] = warnings
    return env

