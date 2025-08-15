"""Planner orchestrator service.

This module ties together the :class:`PlannerAgent` and the dynamic
task registry to execute design tasks.  The orchestrator first generates
a plan based on the current session state and then dispatches the tasks
to the appropriate agents using :class:`AgentRegistry`.

The orchestrator returns a list of ADPF envelopes representing the
outputs from each agent.  Blocked tasks trigger the
``MetaCognitionAgent`` so users receive clarifying questions.  When
``use_consensus`` is enabled, the final step aggregates the candidate
envelopes using the ``ConsensusAgent``.
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

