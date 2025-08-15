# Planner Orchestrator

The `PlannerOrchestrator` combines the dynamic task planner with
registered domain agents.  It executes *every* task through the
`WorkflowEngine`, which applies each agent's graph patch atomically as
part of a saga transaction.  Beginning in Phase 13 there is no fallback
to plain sequential execution: if any step fails, previously applied
patches are rolled back automatically.  The orchestrator still returns a
list of ADPF envelopes representing the outputs from each agent.

* **Recovery & retry** – Because agents are invoked through
  `safe_execute`, any blocked tasks are stored in the global
  `RetryManager`.  The orchestrator automatically calls
  `retry_manager.resolve_blocked_tasks(session_id)` at the beginning and
  end of every workflow run, so previously blocked tasks are
  re‑executed as soon as the user provides missing information or
  another agent completes its work.  You can still call
  `resolve_blocked_tasks` manually, but in most cases the orchestrator
  handles retries on your behalf.

## Usage

```python
from backend.services import PlannerOrchestrator

orchestrator = PlannerOrchestrator()
envelopes = await orchestrator.run("session-1", "design network and site")
```

This will invoke the appropriate agents (`NetworkAgent` and
`SitePlanningAgent`), handle blocked tasks via meta‑cognition, and
return a list of ADPF envelopes.  To aggregate competing outputs using
consensus, set `use_consensus=True`.

### Features

* **Confidence calibration** – Each agent response is assigned a base
  confidence according to its risk class (e.g. low, medium or high).
  This base value is then passed through the `ConfidenceCalibrator` to
  incorporate historical user feedback.  The orchestrator stores both
  the calibrated confidence and a **dynamic threshold** in the design
  card; downstream UIs or policy engines can use these values to decide
  whether to auto‑approve actions.  The consensus agent extracts and
  calibrates each candidate’s confidence when ranking competing
  proposals, so designs that have historically been approved are more
  likely to be selected.
* **Schema enforcement** – Every agent response is validated against
  the ADPF envelope schema.  `safe_execute` performs initial
  validation, and after calibration or other modifications, the
  orchestrator re‑validates the envelope to ensure it still conforms to
  the contract.  If validation fails at any stage, a blocked response is
  returned, preventing malformed data from entering the workflow.

### Developer Guidance

If you plan to customise the orchestrator or develop new planning
strategies, consult the developer onboarding guide
(`docs/developer_guide.md`).  The guide explains how tasks are mapped to
agents, how to register new tasks in `TaskAgentMapping`, and how the
orchestrator invokes agents via `safe_execute`.  It also provides tips
on composing custom saga compensation behaviour and recovery mechanisms
for more advanced planning logic.

