"""Implementation of the planning template for ADPF 2.1.

The ``PlannerTemplate`` is responsible for producing a list of tasks
that should be executed for a given design session.  In the original
OriginFlow architecture this responsibility was carried out by the
``PlannerAgent``.  To ease migration during Sprint 1–2, this
template provides a compatibility layer: it can optionally invoke the
legacy ``PlannerAgent`` (if available in the environment) or fall
back to a simple static plan.  Future sprints will replace this
implementation with a full reasoning scaffold that incorporates
domain packs, context contracts and consensus.

Outputs from the template conform to the **standard output envelope**
proposed by ADPF.  This includes a ``status`` field, a ``result``
mapping containing the tasks, a ``card`` describing the template
execution and ``metrics`` capturing timing or token usage (left
blank for now).  Errors are reported in the ``errors`` field.
"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    # Import the legacy PlannerAgent if it exists.  In development
    # environments where the old codebase is not present this import
    # will fail gracefully and the template will use a fallback plan.
    from backend.agents.planner_agent import PlannerAgent  # type: ignore
except Exception:
    PlannerAgent = None  # type: ignore

from backend.models.context_contract import ContextContract
from .agent_template import AgentTemplate


class PlannerTemplate(AgentTemplate):
    """Concrete template for planning tasks.

    This template constructs a sequence of high‑level tasks based on
    the current context contract and governance policy.  When the
    legacy ``PlannerAgent`` is available it delegates the task
    construction to that implementation, providing continuity with
    existing behavior.  Otherwise it returns a minimal static plan
    suitable for development and testing.
    """

    name: str = "Planner"
    cognitive_mode: str = "plan"
    protocol_steps: List[str] = [
        "situation_analysis",
        "hypothesis_generation",
        "synthesis",
        "verification",
        "reflection",
    ]
    # Output schema describing the result shape.  This is a loose
    # specification; full JSON schemas will be introduced in later sprints.
    output_schema: Dict[str, Any] = {
        "tasks": {
            "type": "array",
            "items": {"type": "object"},
        }
    }

    async def run(self, contract: ContextContract, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Produce a task plan for the session.

        The contract must contain a ``session_id`` (in ``inputs``) and
        optionally a ``command`` describing the user's intent.  The
        governance policy may influence budget or safety decisions but
        is not used in this initial implementation.

        Returns:
            A dictionary with fields:
                - ``status`` (str): "complete" on success.
                - ``result`` (dict): mapping containing a ``tasks`` list.
                - ``card`` (dict): summary of the template run.
                - ``metrics`` (dict): placeholder for telemetry metrics.
                - ``errors`` (list): empty on success, populated on failure.
        """
        session_id = contract.inputs.get("session_id")
        command: str = str(contract.inputs.get("command", "")).lower().strip()

        tasks: List[Dict[str, Any]] = []
        errors: List[str] = []

        # If the legacy planner exists and we have a session ID, delegate to it.
        if PlannerAgent is not None and session_id:
            try:
                planner = PlannerAgent()
                # The legacy planner API returns a list of tasks.  We ignore
                # any additional metadata for now.
                tasks = await planner.plan(session_id, command)
            except Exception as exc:  # pragma: no cover - graceful degradation
                errors.append(f"Legacy planner error: {exc}")

        # Fallback static plan when legacy planner is unavailable or failed.
        if not tasks:
            # Minimal dynamic plan derived from common solar workflows.
            tasks = [
                {
                    "id": "gather_requirements",
                    "status": "pending",
                    "reason": "Collect missing inputs before design."
                },
                {
                    "id": "generate_design",
                    "status": "pending",
                    "reason": "Create a preliminary PV system design."
                },
                {
                    "id": "refine_validate",
                    "status": "pending",
                    "reason": "Refine design and validate compliance."
                },
            ]

        # Construct the output envelope.
        result: Dict[str, Any] = {
            "tasks": tasks,
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if t.get("status") == "pending"]),
        }
        card = {
            "template": self.name,
            "cognitive_mode": self.cognitive_mode,
            "confidence": 1.0 if not errors else 0.5,
        }

        return {
            "status": "complete" if not errors else "error",
            "result": result,
            "card": card,
            "metrics": {},
            "errors": errors,
        }
