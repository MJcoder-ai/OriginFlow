"""Dynamic prompt orchestrator for ADPF 2.1.

The orchestrator executes a deterministic sequence of layers:

    1. Governance enforcement.
    2. Meta‑cognition planning.
    3. Domain knowledge injection.
    4. Context contract initialization.
    5. Reasoning scaffold (placeholder).
    6. Agent template execution (e.g. planning, design, component selection).
    7. Validation and recovery (ensure schema compliance).
    8. Inter‑agent notifications and consensus (future work).
    9. Learning, calibration and telemetry (future work).

During Sprint 1–2 only the first six steps are partially implemented.
Governance enforcement, meta‑cognition planning, domain injection and
context contract creation are stubbed.  Agent template execution is
supported via the ``PlannerTemplate``, which yields a high‑level task
plan.  Validation, consensus and learning layers will be added in
subsequent sprints.
"""
from __future__ import annotations

from typing import Any, Dict

from backend.governance.governance import Governance
from backend.models.context_contract import ContextContract
from backend.templates import PlannerTemplate


class DynamicPromptOrchestratorV2:
    """Skeleton orchestrator following ADPF 2.1."""

    def __init__(self) -> None:
        self.governance = Governance()

    async def run(self, command: str, session_id: str) -> Dict[str, Any]:
        """Execute the layered workflow for a user command."""
        # Step 1: Governance enforcement.
        policy = self.governance.enforce(command, session_id)

        # Step 2: Meta‑cognition planning (stub).
        meta_plan: Dict[str, Any] = {"strategy": "naive"}

        # Step 3: Domain knowledge injection (stub).
        domain_data: Dict[str, Any] = {"domain_pack": None}

        # Step 4: Initialize a context contract for the session.  We
        # capture both the raw command and the session identifier in the
        # inputs so downstream templates have access to this metadata.  The
        # contract will be enriched as the workflow progresses.
        contract = ContextContract(inputs={"command": command, "session_id": session_id})

        # Step 5: (Placeholder) Reasoning scaffold would go here.

        # Step 6: Agent template execution.  For Sprint 1–2 we only
        # support the planning template, which returns a high‑level task
        # list.  Future sprints will select templates based on the
        # meta‑cognition strategy and domain injection.
        planner = PlannerTemplate()
        plan_output = await planner.run(contract, policy)

        # TODO: Steps 7–9 (validation, inter‑agent events, learning) will be
        # implemented in later sprints.

        # Construct the orchestrator envelope.  This includes the
        # intermediate artefacts from earlier steps plus the result from
        # the template.  The final status propagates the planner status.
        return {
            "status": plan_output.get("status", "unknown"),
            "policy": policy,
            "meta_plan": meta_plan,
            "domain": domain_data,
            "contract": contract.model_dump(),
            "result": plan_output.get("result"),
            "card": plan_output.get("card"),
            "metrics": plan_output.get("metrics"),
            "errors": plan_output.get("errors"),
        }
