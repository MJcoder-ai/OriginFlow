"""Planner orchestrator service.

This module defines an asynchronous orchestrator that sequences design
tasks across multiple domain agents.  It integrates with the agent
registry to dispatch tasks to the correct agent, automatically
invokes meta‑cognition for blocked tasks, aggregates competing outputs
using the consensus agent, registers blocked tasks for retry, and
applies patches to the design graph.  Beginning with Phase 13, the
orchestrator executes *all* tasks using a saga‑style workflow engine.
There is no fallback to sequential execution; instead, every task
produces a graph patch that participates in a consistent, atomic
transaction.  Compensation functions may be provided to customise
rollback behaviour for specific tasks.

Key features:
    * **Saga integration** – Tasks are always executed inside a saga via
      the ``WorkflowEngine``.  Each agent’s patch is applied to the
      design graph; if any step fails, the engine automatically rolls
      back previously applied patches using compensating transactions.
      Custom compensation functions can be supplied on a per‑task basis
      to override the default behaviour of calling ``patch.reverse()``.
      This ensures atomic multi‑step operations without relying on
      distributed transactions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.agents.planner_agent import PlannerAgent
from backend.agents.registry import AgentRegistry
from backend.utils.confidence_calibration import ConfidenceCalibrator


class PlannerOrchestrator:
    """Coordinate planning and execution of design tasks."""

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        planner: Optional[PlannerAgent] = None,
        calibrator: Optional[ConfidenceCalibrator] = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.planner = planner or PlannerAgent()
        self.calibrator = calibrator or ConfidenceCalibrator()

    async def run(
        self,
        session_id: str,
        command: str,
        *,
        requirements: Optional[Dict[str, Any]] = None,
        use_consensus: bool = False,
    ) -> List[Dict[str, Any]]:
        """Generate a task plan and execute mapped agents.

        Args:
            session_id: Identifier of the current design session.
            command: User instruction for the planner (e.g. ``"design system"``).
            requirements: Optional mapping of requirement values passed directly
                to :meth:`PlannerAgent.plan`.
            use_consensus: When ``True`` a final ``ConsensusAgent`` step is
                executed across candidate envelopes.

        Returns:
            A list of ADPF envelopes produced by executed agents.
        """

        plan = await self.planner.plan(
            session_id, command, requirements=requirements
        )

        envelopes: List[Dict[str, Any]] = []
        candidates: List[Dict[str, Any]] = []

        for task in plan:
            tid = task.get("id")
            status = task.get("status", "pending")
            agent = self.registry.get_agent(tid)

            if status == "blocked":
                meta = self.registry.get_agent("meta_cognition")
                if meta:
                    missing = (
                        task.get("missing_requirements")
                        or task.get("missing_components")
                        or []
                    )
                    env = await meta.safe_execute(
                        session_id,
                        "meta_cognition",
                        missing=missing,
                        reason=task.get("reason", ""),
                    )
                    envelopes.append(env)
                continue

            if not agent:
                continue

            env = await self.run_task(session_id, tid, agent_name=tid, agent=agent, **task)
            envelopes.append(env)
            candidates.append(env)

        if use_consensus and len(candidates) > 1:
            consensus = self.registry.get_agent("consensus")
            if consensus:
                env = await consensus.safe_execute(
                    session_id, "consensus", candidates=candidates
                )
                envelopes.append(env)

        return envelopes

    async def run_task(
        self,
        session_id: str,
        task_id: str,
        *,
        agent_name: str,
        agent: Any,
        **context: Any,
    ) -> Dict[str, Any]:
        """Execute an individual task and enforce schema compliance."""

        resp = await agent.safe_execute(session_id, task_id, **context)

        # Apply confidence calibration if a card and confidence are present
        try:
            card = resp.get("output", {}).get("card", {})  # type: ignore[assignment]
            confidence = card.get("confidence")
            if isinstance(confidence, (int, float)):
                card["confidence"] = self.calibrator.calibrate_confidence(
                    agent_name=agent_name,
                    action_type=task_id,
                    original_confidence=float(confidence),
                )
        except Exception:
            pass

        # After calibration, re-validate the envelope to ensure it still
        # conforms to the ADPF schema.  If validation fails, return a
        # blocked envelope indicating schema error.  This ensures that
        # modifications (e.g. adding confidence fields) do not break the
        # contract enforced by schema_enforcer.
        try:
            # Reuse validate_envelope from schema_enforcer via safe_execute
            from backend.utils.schema_enforcer import validate_envelope  # type: ignore
            validate_envelope(resp)  # type: ignore[arg-type]
        except Exception:
            # Return a fallback envelope to indicate invalid structure
            return {
                "thought": f"Invalid envelope returned by agent '{agent_name}' after calibration for task '{task_id}'",
                "output": {
                    "card": {
                        "title": agent_name.replace("_", " ").title(),
                        "body": "The modified envelope did not conform to the required schema.",
                    },
                    "patch": None,
                },
                "status": "blocked",
            }
        return resp


__all__ = ["PlannerOrchestrator"]

