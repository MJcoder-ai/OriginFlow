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
supported via templates such as ``PlannerTemplate`` for task planning,
``PVDesignTemplate`` for basic system sizing and ``ComponentSelectorTemplate``
for component recommendations.  Validation, consensus and learning layers will
be added in subsequent sprints.
"""
from __future__ import annotations

from typing import Any, Dict

from backend.governance.governance import Governance
from backend.models.context_contract import ContextContract
from backend.templates import (
    PlannerTemplate,
    PVDesignTemplate,
    ComponentSelectorTemplate,
)
from backend.domain import load_domain_pack


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

        # Step 3: Domain injection.  Load the requested domain pack.  For
        # now we assume the solar domain; later meta‑cognition may select
        # different domains or versions.
        try:
            domain_data: Dict[str, Any] = load_domain_pack("solar", "v1")
        except Exception:
            # Fallback to empty domain data on failure.
            domain_data = {"formulas": None, "constraints": None, "components": None}

        # Step 4: Initialize a context contract for the session.  Capture
        # the raw command and session ID.  Additional inputs (e.g. target
        # power or budget) may be extracted from the command below.
        contract = ContextContract(inputs={"command": command, "session_id": session_id})

        # Extract numeric values from the command for common parameters.
        # For example "design 5 kW system" sets target_power=5000.
        cmd_lower = command.lower().strip()
        import re

        m = re.search(r"(\d+(?:\.\d+)?)\s*kw", cmd_lower)
        if m:
            try:
                kw_value = float(m.group(1))
                contract.inputs["target_power"] = kw_value * 1000
            except Exception:
                pass
        bm = re.search(r"[\$\u00a3](\d+(?:\.\d+)?)", cmd_lower)
        if bm:
            try:
                budget_val = float(bm.group(1))
                contract.inputs["budget"] = budget_val
            except Exception:
                pass

        # Step 5: (Placeholder) Reasoning scaffold would go here.

        # Step 6: Agent template execution.  Dispatch based on the
        # command.  If the user requests a design, invoke the
        # PVDesignTemplate.  If the user requests component selection,
        # invoke the ComponentSelectorTemplate.  Otherwise invoke
        # PlannerTemplate to produce a task plan.
        if cmd_lower.startswith("design"):
            template = PVDesignTemplate(domain="solar", version="v1")
            template_output = await template.run(contract, policy)
        elif "component" in cmd_lower or "select" in cmd_lower:
            template = ComponentSelectorTemplate(domain="solar", version="v1")
            template_output = await template.run(contract, policy)
        else:
            template = PlannerTemplate()
            template_output = await template.run(contract, policy)

        # TODO: Steps 7–9 (validation, inter‑agent events, learning) will be
        # implemented in later sprints.

        # Construct the orchestrator envelope.
        return {
            "status": template_output.get("status", "unknown"),
            "policy": policy,
            "meta_plan": meta_plan,
            "domain": domain_data,
            "contract": contract.model_dump(),
            "result": template_output.get("result"),
            "card": template_output.get("card"),
            "metrics": template_output.get("metrics"),
            "errors": template_output.get("errors"),
            "validations": template_output.get("validations"),
        }
