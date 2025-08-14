"""Dynamic prompt orchestrator for ADPF 2.1.

The orchestrator executes a deterministic sequence of layers:

    1. Governance enforcement.
    2. Meta‑cognition planning.
    3. Domain knowledge injection.
    4. Context contract initialization.
    5. Reasoning scaffold (placeholder).
    6. Agent template execution (e.g. planning, design, component selection).
    7. Validation and recovery (ensure schema compliance).
    8. Inter‑agent notifications and consensus.
    9. Learning, calibration and telemetry.

During Sprints 1–2 only the first six steps were implemented in a
skeletal manner.  Subsequent Sprint 3–4 introduced domain packs
and agent templates for planning, PV design and component
selection.  In Sprint 5–6 the orchestrator integrates
**consensus**, **learning** and **observability**: proposals are
aggregated via a ``ConsensusEngine``, outcomes are recorded by a
``LearningAgent`` and execution is instrumented with a ``Tracer``
and ``MetricsCollector``.  The orchestrator now returns rich
observability data alongside results.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from backend.governance.governance import Governance
from backend.models.context_contract import ContextContract
from backend.templates import (
    PlannerTemplate,
    PVDesignTemplate,
    ComponentSelectorTemplate,
)
from backend.domain import load_domain_pack
from backend.bus.inter_agent_bus import InterAgentBus
from backend.consensus.consensus_engine import ConsensusEngine
from backend.learning.learning_agent import LearningAgent
from backend.observability import Tracer, MetricsCollector

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - environment without pyyaml
    yaml = None


class DynamicPromptOrchestratorV2:
    """Skeleton orchestrator following ADPF 2.1."""

    def __init__(self, adpf_config: Optional[Dict[str, Any]] = None) -> None:
        self.governance = Governance()

        # Load configuration settings either from the supplied dictionary
        # or from the project YAML file.  Configuration values may
        # include consensus weights, budgets and policy thresholds.
        if adpf_config is not None:
            self.config = adpf_config
        else:
            # Load configuration from YAML if present.  The dynamic
            # orchestrator lives in backend/orchestrator, so go two
            # levels up to reach the project root and then into
            # config/adpf.yaml.
            project_root = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(project_root, "config", "adpf.yaml")
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    if yaml is not None:
                        self.config = yaml.safe_load(f) or {}
                    else:
                        self.config = {}
            except FileNotFoundError:
                self.config = {}

        # Initialise auxiliary components for inter‑agent events,
        # consensus decisions, learning and observability.  These are
        # available regardless of configuration; consensus weights may
        # be overridden via the config.
        consensus_weights = None
        if isinstance(self.config.get("consensus"), dict):
            consensus_weights = self.config["consensus"].get("weights")
        self.bus = InterAgentBus()
        self.consensus = ConsensusEngine(weights=consensus_weights)
        self.learning = LearningAgent()
        self.tracer = Tracer()
        self.metrics = MetricsCollector()

    async def run(self, command: str, session_id: str) -> Dict[str, Any]:
        """Execute the layered workflow for a user command."""
        # Start a root span and timer for observability.  We record
        # attributes such as the command and session for later analysis.
        root_span = self.tracer.start_span("orchestrator.run", command=command, session=session_id)
        timer_start = self.metrics.start_timer("orchestrator.run_ms")

        # Step 1: Governance & safety enforcement.  In future sprints the
        # ``task`` argument may be a richer object describing the command.
        policy = Governance.enforce(task={"requires_citations": False}, session=session_id)

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

        # Step 7: Validation and recovery is handled within each template via
        # the validator and recovery utilities.  Results returned here
        # should already conform to the standard envelope.

        # Step 8: Inter‑agent notifications and consensus.  Publish the
        # completion event to the bus and compute consensus over
        # proposals if needed.  Currently only one proposal is
        # generated, so consensus simply returns the same output.
        self.bus.publish("TaskCompleted", template_output)
        consensus_choice = self.consensus.decide([template_output])

        # Step 9: Learning, calibration and telemetry.  Record the
        # envelope with the learning agent.  Update metrics to reflect
        # counts of tasks, errors and validations.
        await self.learning.update(session_id, consensus_choice)
        # Record counts for metrics
        result_data = consensus_choice.get("result") or {}
        if isinstance(result_data, dict) and "tasks" in result_data:
            task_count = len(result_data.get("tasks", []))
            self.metrics.record("task_count", float(task_count))
        self.metrics.record("validation_count", float(len(consensus_choice.get("validations", []))))
        self.metrics.record("error_count", float(len(consensus_choice.get("errors", []))))

        # Stop timer and span for observability
        self.metrics.stop_timer("orchestrator.run_ms", timer_start)
        span_status = "ok" if consensus_choice.get("status") == "complete" else "error"
        self.tracer.end_span(root_span, status=span_status)

        spans = [
            {
                "name": s.name,
                "duration_ms": s.duration_ms,
                "status": s.status,
                "attributes": s.attributes,
            }
            for s in self.tracer.collect_finished()
        ]
        metrics_summary = self.metrics.summary()

        # Merge template metrics with orchestrator metrics
        final_metrics: Dict[str, Any] = template_output.get("metrics", {}).copy()
        final_metrics.update(metrics_summary)
        final_metrics["spans"] = spans

        envelope: Dict[str, Any] = {
            "status": consensus_choice.get("status", "unknown"),
            "policy": policy,
            "meta_plan": meta_plan,
            "domain": domain_data,
            "contract": contract.model_dump(),
            "result": consensus_choice.get("result"),
            "card": consensus_choice.get("card"),
            "metrics": final_metrics,
            "errors": consensus_choice.get("errors"),
            "validations": consensus_choice.get("validations"),
        }
        return envelope
