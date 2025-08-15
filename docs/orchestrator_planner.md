# Planner Orchestrator

The `PlannerOrchestrator` combines the dynamic task planner with
registered domain agents.  It executes *every* task through the
`WorkflowEngine`, which applies each agent's graph patch atomically as
part of a saga transaction.  Beginning in Phase 13 there is no fallback
to plain sequential execution: if any step fails, previously applied
patches are rolled back automatically.  The orchestrator still returns a
list of ADPF envelopes representing the outputs from each agent.

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

### Developer Guidance

If you plan to customise the orchestrator or develop new planning
strategies, consult the developer onboarding guide
(`docs/developer_guide.md`).  The guide explains how tasks are mapped to
agents, how to register new tasks in `TaskAgentMapping`, and how the
orchestrator invokes agents via `safe_execute`.  It also provides tips
on composing custom saga compensation behaviour and recovery mechanisms
for more advanced planning logic.

