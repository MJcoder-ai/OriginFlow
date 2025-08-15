# Planner Orchestrator

The `PlannerOrchestrator` combines the dynamic task planner with
registered domain agents.  It executes tasks sequentially and returns a
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
on integrating the saga workflow engine and recovery mechanisms into
more advanced planning logic.

