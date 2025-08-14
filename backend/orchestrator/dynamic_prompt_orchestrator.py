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

    Earlier sprints implemented a skeletal orchestrator with static
    routing and partial support for domain packs, agent templates,
    consensus, learning and observability.  This version extends the
    workflow with simple **meta‑cognition planning**, dynamic
    **domain selection** using ``available_packs()``, configurable
    **budgets** from the ADPF configuration, **rule‑based**
    verification via domain constraints, multi‑agent **consensus**
    across PV design and component selection, basic **learning
    calibration** of confidence scores, concurrency for combined
    operations, PII masking for user inputs, persistent **context
    contract** storage and simple **budget enforcement**.  The
    orchestrator supports commands like "design 5 kW system",
    "select components" or combined operations such as "design and
    select" or "complete system", automatically selects the
    appropriate templates and merges their results while respecting
    governance policies, budgets and domain constraints.
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
from backend.domain import load_domain_pack, available_packs
from backend.bus.inter_agent_bus import InterAgentBus
from backend.consensus.consensus_engine import ConsensusEngine
from backend.learning.learning_agent import LearningAgent
from backend.observability import Tracer, MetricsCollector
from backend.utils.security import mask_pii
import asyncio

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

        cmd_lower = command.lower().strip()

        # Step 3: Domain injection. Choose a domain pack based on the
        # command.  We default to "solar" unless the command names another
        # available domain.  The newest version of the chosen pack is used.
        domain_name = "solar"
        version = "v1"
        try:
            packs = available_packs()
            for dom, versions in packs.items():
                if dom in cmd_lower:
                    domain_name = dom
                    if versions:
                        version = sorted(versions)[-1]
                    break
            domain_data: Dict[str, Any] = load_domain_pack(domain_name, version)
        except Exception:
            domain_data = {"formulas": None, "constraints": None, "components": None}

        # Step 4: Load or create a context contract for the session.
        try:
            contract = ContextContract.load(session_id)
        except Exception:
            contract = ContextContract(inputs={})
        contract.inputs.update({"command": command, "session_id": session_id})
        contract.inputs = mask_pii(contract.inputs)

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

        # Step 6: Agent template execution.  Determine which templates are
        # required based on the command.  If both design and component
        # selection are requested, run them concurrently and feed their
        # outputs into the consensus engine.  Otherwise run the single
        # appropriate template or fall back to the planner.
        try:
            design_needed = cmd_lower.startswith("design") or "design" in cmd_lower
            component_needed = "component" in cmd_lower or "select" in cmd_lower
            combined = design_needed and component_needed
            if combined:
                design_template = PVDesignTemplate(domain=domain_name, version=version)
                selector_template = ComponentSelectorTemplate(domain=domain_name, version=version)
                design_output, selector_output = await asyncio.gather(
                    design_template.run(contract, policy),
                    selector_template.run(contract, policy),
                )
                design_output.setdefault("expertise", 0.6)
                design_output.setdefault("preference", 1.0)
                design_output.setdefault("risk", 0.2)
                selector_output.setdefault("expertise", 0.4)
                selector_output.setdefault("preference", 1.0)
                selector_output.setdefault("risk", 0.1)
                proposals = [design_output, selector_output]
            elif design_needed:
                template = PVDesignTemplate(domain=domain_name, version=version)
                proposals = [await template.run(contract, policy)]
            elif component_needed:
                template = ComponentSelectorTemplate(domain=domain_name, version=version)
                proposals = [await template.run(contract, policy)]
            else:
                template = PlannerTemplate()
                proposals = [await template.run(contract, policy)]
        except Exception as exc:  # pragma: no cover - catch unexpected errors
            proposals = [
                {
                    "status": "error",
                    "result": None,
                    "card": {"template": "unknown", "confidence": 0.0},
                    "metrics": {},
                    "errors": [f"Template execution error: {exc}"],
                    "validations": [],
                }
            ]

        # Step 7: Validation and recovery is handled within each template via
        # the validator and recovery utilities.  Results returned here
        # should already conform to the standard envelope.

        # For consensus, enrich each proposal with numeric fields if they
        # are absent.  Confidence is derived from the card and used to
        # populate expertise and confidence weights.
        for proposal in proposals:
            conf = 0.5
            if isinstance(proposal.get("card"), dict):
                conf = float(proposal["card"].get("confidence", 0.5))
            proposal.setdefault("expertise", conf)
            proposal.setdefault("confidence", conf)
            proposal.setdefault("preference", 1.0)
            proposal.setdefault("risk", 0.0)

        # Step 8: Inter‑agent notifications and consensus. Publish all
        # completion events to the bus and compute consensus over the
        # proposals.
        for proposal in proposals:
            self.bus.publish("TaskCompleted", proposal)
        consensus_choice = self.consensus.decide(proposals)

        # Step 9: Learning, calibration and telemetry.  Record the
        # envelope with the learning agent.  Update metrics to reflect
        # counts of tasks, errors and validations.
        await self.learning.update(session_id, consensus_choice)
        # Record counts for metrics
        result_data = consensus_choice.get("result") or {}
        if isinstance(result_data, dict) and "tasks" in result_data:
            task_count = len(result_data.get("tasks", []))
            self.metrics.record("task_count", float(task_count))
        self.metrics.record(
            "validation_count", float(len(consensus_choice.get("validations", [])))
        )
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
        base_metrics: Dict[str, Any] = {}
        for prop in proposals:
            base_metrics.update(prop.get("metrics", {}))
        final_metrics: Dict[str, Any] = base_metrics.copy()
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
            "next_actions": consensus_choice.get("next_actions", []),
        }

        # Apply budget enforcement based on governance policy.  We
        # approximate token usage as the number of tasks plus one
        # retrieval for the domain pack.
        try:
            budget_info = policy.get("budget") or {}
            token_limit = budget_info.get("token_limit")
            retrieval_limit = budget_info.get("retrieval_limit")
            estimated_tokens = 0
            res = envelope.get("result") or {}
            if isinstance(res, dict) and "tasks" in res and isinstance(res["tasks"], list):
                estimated_tokens += len(res["tasks"])
            if domain_data.get("components"):
                estimated_tokens += 1
            if token_limit is not None and estimated_tokens > token_limit:
                envelope["status"] = "error"
                envelope.setdefault("validations", []).append(
                    f"Estimated token usage {estimated_tokens} exceeds limit {token_limit}"
                )
            if retrieval_limit is not None and 1 > retrieval_limit:
                envelope["status"] = "error"
                envelope.setdefault("validations", []).append(
                    f"Retrieval count 1 exceeds limit {retrieval_limit}"
                )
        except Exception:
            pass

        # Persist context contract for session continuity
        try:
            contract.save(session_id)
        except Exception:
            pass

        # Reset metrics collector for subsequent runs to avoid
        # accumulating cross-session data.  Observability spans are
        # similarly cleared when collected.
        self.metrics = MetricsCollector()
        return envelope
