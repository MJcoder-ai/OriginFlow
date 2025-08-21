# Developer Onboarding Guide

This guide introduces new contributors to the OriginFlow codebase and
outlines the workflow for extending the platform with new components or
agents.

## 1. Environment Setup

1. Install Python 3.10+ and Node.js 18+
2. Install backend dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   or using Poetry:
   ```sh
   poetry install
   ```
3. Install frontend dependencies if working on the UI:
   ```sh
   cd frontend
   npm install
   ```

## 2. Add Placeholder Component Types

1. Extend `backend/services/placeholder_components.py` with the new type
   and default attributes.
2. Update the catalog in `docs/placeholder_catalog.md`.
3. Reference the placeholder in any new agents or planners.

## 3. Create a New Agent

1. Implement the agent in `backend/agents/` and inherit from
   `AgentBase`.
2. Register the agent in `backend/agents/registry.py` using the
   `@register` decorator.
3. Document the agent's behaviour and inputs/outputs in an appropriate
   doc file.

### Validation Agents

In addition to design agents that modify the ODL graph, you can create
validation agents that inspect the current design and report issues
without making changes.  For example:

- **CrossLayerValidationAgent** – Ensures that all components are
  properly connected.  It identifies isolated nodes, verifies that
  battery modules are connected to inverters or the system root,
  checks that monitoring devices are attached via communication
  links, and compares the number of batteries and inverters to
  recommend a balanced one‑to‑one ratio.  Any issues are
  aggregated into an ``issues`` list in the returned card.
- **NetworkValidationAgent** – Verifies that all inverters and
  monitoring devices are connected to network devices.  It recognises
  both domain‑specific types (`network`, `monitoring`) and their
  generic placeholders (`generic_network`, `generic_monitoring`),
  constructs a connectivity graph of communication links and reports
  missing network paths or absent network devices.

Validation agents typically return a design card with an ``issues`` list
and ``status='complete'``.  When registering a validation agent,
assign a low risk class and a capability of ``report`` via
`register_spec`.

## 4. Enforce Contracts and Calibration

1. Wrap agent execution with `safe_execute` so envelopes are validated
   by the schema enforcer.
2. Use `ConfidenceCalibrator` when assigning confidence scores and
   adjust thresholds based on feedback.
3. After any post‑processing such as confidence calibration, re‑validate
   the envelope using `validate_envelope`. If validation fails, return a
   blocked response. Always include the required keys (`thought`,
   `output`, `status`) when designing new agents and test against the
   schema.

## 5. Orchestrator & Planning

* **Recovery & retry** – Because agents are invoked through
  `safe_execute`, blocked tasks are registered with the global
  `RetryManager`.  The `PlannerOrchestrator` automatically invokes the
  retry manager at the start and end of each `run_workflow` call, so
  blocked tasks are re‑executed whenever new context (such as user input
  or another agent’s output) becomes available. If needed, you can still
  call `resolve_blocked_tasks(session_id)` manually for ad‑hoc retries.

* **Confidence calibration** – Each agent response receives a base
  confidence according to its risk class. The orchestrator uses the
  `ConfidenceCalibrator` to adjust this value based on historical user
  feedback, then writes the calibrated confidence and a dynamic
  auto‑approval threshold into the card. The `ConsensusAgent` ranks
  proposals by calibrated confidence. Call `record_feedback` on the
  orchestrator whenever users approve or reject an action to improve
  calibration.

* **Dynamic planning** – The orchestrator integrates the `DynamicPlanner`
  to automatically generate a task list when none is supplied. The
  planner examines the current design graph to determine which domain
  tasks (network, site, battery, monitoring and validation) are
  required. You can extend the planner by adding new heuristic rules in
  `backend/services/planner.py`, such as checking user requirements or
  balancing risk classes. When adding new tasks, remember to register
  them in `backend/agents/registry.py` and provide the corresponding
  agent implementation.

## 6. Write Tests

1. Add unit or scenario tests under `tests/`.
2. Use `pytest -q` to run the suite.
3. For end‑to‑end flows, leverage asynchronous tests and the
   `safe_execute` wrapper as shown in `docs/end_to_end_tests.md`.

## 7. Submit Your Change

Run the test suite before opening a pull request and ensure all
documentation is up to date. For coding conventions, see `docs/legacy/AGENTS.md`
and `CONTRIBUTING.md`.

