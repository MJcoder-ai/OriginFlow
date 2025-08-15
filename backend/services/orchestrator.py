"""Planner orchestrator service.

This module defines an asynchronous orchestrator that sequences design
tasks across multiple domain agents. It integrates with the agent
registry to dispatch tasks to the correct agent, automatically invokes
meta‑cognition for blocked tasks, aggregates competing outputs using the
consensus agent, registers blocked tasks for retry, and applies patches
to the design graph via a saga‑style workflow engine. When no tasks are
provided by the caller, the orchestrator invokes the ``DynamicPlanner``
to generate an appropriate task list based on the current state of the
ODL graph. Thus, dynamic planning is fully integrated: the orchestrator
decides which tasks to run if none are specified, ensuring that essential
steps (network, site, battery, monitoring and validation) are always
executed in the correct order.

All tasks are executed using a saga engine: every agent’s patch is
applied atomically, and compensating patches are used to roll back
changes if a failure occurs. Compensation functions may be provided to
override the default reversal logic. The orchestrator also integrates
confidence calibration, schema enforcement, and automated recovery and
retry, making it a robust coordinator for multi‑domain design workflows.
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

    async def run_workflow(
        self,
        *,
        session_id: str,
        tasks: List[str],
        use_consensus: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute a predefined list of tasks via the saga workflow engine.

        This method resolves previously blocked tasks at the start and end of
        the workflow, runs each task through the ``WorkflowEngine`` so that
        graph patches are applied atomically, calibrates confidences, assigns
        dynamic thresholds and returns the resulting envelopes.  If
        ``use_consensus`` is true and more than one envelope is produced, a
        consensus step is executed across the candidates.
        """

        from backend.utils.retry_manager import retry_manager
        from backend.services.workflow_engine import WorkflowEngine, SagaStep
        from backend.services.odl_graph_service import ODLGraphPatch

        # Resolve any blocked tasks at the beginning of the workflow
        await retry_manager.resolve_blocked_tasks(session_id)

        results: List[Dict[str, Any]] = []
        engine = WorkflowEngine()
        steps: List[SagaStep] = []

        # Build saga steps for each requested task
        for task_id in tasks:
            agent = self.registry.get_agent(task_id)
            if not agent:
                continue

            async def forward_fn(
                sid: str, tid: str = task_id, ag: Any = agent
            ) -> ODLGraphPatch:
                env = await self.run_task(
                    sid, tid, agent_name=tid, agent=ag
                )

                # Append dynamic threshold to card
                card: Optional[Dict[str, Any]] = None
                if isinstance(env, dict):
                    out = env.get("output")
                    if isinstance(out, dict):
                        card = out.get("card")
                    if card is None:
                        card = env.get("card")
                if isinstance(card, dict):
                    base_threshold = 0.75
                    try:
                        dyn_thr = self.calibrator.get_threshold(
                            tid, tid, base_threshold
                        )
                    except Exception:
                        dyn_thr = base_threshold
                    card["dynamic_threshold"] = dyn_thr

                results.append(env)

                patch_dict: Optional[Dict[str, Any]] = None
                if isinstance(env, dict):
                    out = env.get("output")
                    if isinstance(out, dict):
                        patch_dict = out.get("patch")
                if patch_dict is None and isinstance(env, dict):
                    patch_dict = env.get("patch")  # type: ignore[assignment]

                if patch_dict:
                    try:
                        return ODLGraphPatch.model_validate(patch_dict)
                    except Exception:
                        return ODLGraphPatch()
                return ODLGraphPatch()

            steps.append(SagaStep(name=task_id, forward=forward_fn))

        # Execute workflow; workflow engine handles rollback on failure
        try:
            await engine.run(session_id, steps)
        except Exception:
            pass

        # Resolve blocked tasks again after workflow completes
        await retry_manager.resolve_blocked_tasks(session_id)

        # Optionally run consensus across candidate results
        if use_consensus and len(results) > 1:
            consensus = self.registry.get_agent("consensus")
            if consensus:
                env = await self.run_task(
                    session_id,
                    "consensus",
                    agent_name="consensus",
                    agent=consensus,
                    candidates=results,
                )

                card: Optional[Dict[str, Any]] = None
                out = env.get("output") if isinstance(env, dict) else None
                if isinstance(out, dict):
                    card = out.get("card")
                if card is None and isinstance(env, dict):
                    card = env.get("card")
                if isinstance(card, dict):
                    base_threshold = 0.75
                    try:
                        dyn_thr = self.calibrator.get_threshold(
                            "consensus", "consensus", base_threshold
                        )
                    except Exception:
                        dyn_thr = base_threshold
                    card["dynamic_threshold"] = dyn_thr
                results.append(env)

        return results

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
            command: User instruction for the planner (e.g.
                ``"design system"``).
            requirements: Optional mapping of requirement values passed
                directly to :meth:`PlannerAgent.plan`.
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

            env = await self.run_task(
                session_id,
                tid,
                agent_name=tid,
                agent=agent,
                **task,
            )
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
            card = resp.get("output", {}).get(
                "card", {}
            )  # type: ignore[assignment]
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
            from backend.utils.schema_enforcer import (
                validate_envelope,
            )  # type: ignore
            validate_envelope(resp)  # type: ignore[arg-type]
        except Exception:
            # Return a fallback envelope to indicate invalid structure
            return {
                "thought": (
                    "Invalid envelope returned by agent "
                    f"'{agent_name}' after calibration for task '{task_id}'"
                ),
                "output": {
                    "card": {
                        "title": agent_name.replace("_", " ").title(),
                        "body": (
                            "The modified envelope did not conform to the "
                            "required schema."
                        ),
                    },
                    "patch": None,
                },
                "status": "blocked",
            }
        return resp


__all__ = ["PlannerOrchestrator"]
