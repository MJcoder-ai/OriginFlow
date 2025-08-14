"""Governance policy enforcement for ADPF 2.1."""
from __future__ import annotations

from typing import Any, Dict


class Governance:
    """Stub governance handler used by the orchestrator."""

    @staticmethod
    def enforce(task: Any, session: Any) -> Dict[str, Any]:
        """Return a governance policy dict given a task and session.

        Args:
            task: The current task or command being processed.  This may
                contain fields such as ``requires_citations`` to influence
                policy.  ``task`` may be a dictionary or an object with
                attributes.
            session: The current session identifier or object (unused).

        Returns:
            A mapping of policy keys and values.  See ADPF 2.1 for details.
        """
        # Determine whether citations are required.  If the task is a
        # dictionary use the ``get`` method, otherwise fall back to
        # attribute access via ``getattr``.  Defaults to False.
        citations_required: bool
        if isinstance(task, dict):
            citations_required = bool(task.get("requires_citations", False))
        else:
            citations_required = bool(getattr(task, "requires_citations", False))

        return {
            "pii_policy": "strip-or-mask",
            "citations_required": citations_required,
            "restricted_topics": [],
            "uncertainty_threshold": 0.35,
            "allowed_tools": ["retrieval", "calculator"],
        }
