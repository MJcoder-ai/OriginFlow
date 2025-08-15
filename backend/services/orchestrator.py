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


class PlannerOrchestrator:
    """Coordinate planning and execution of design tasks."""

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        planner: Optional[PlannerAgent] = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.planner = planner or PlannerAgent()

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

            env = await agent.safe_execute(session_id, tid, **task)
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


__all__ = ["PlannerOrchestrator"]

