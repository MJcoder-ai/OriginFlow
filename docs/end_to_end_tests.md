# End‑to‑End Scenario Tests (Phase 17)

To ensure that OriginFlow operates correctly across its various agents
and calibration components, a set of end‑to‑end scenario tests has been
added. These tests exercise the meta‑cognition and consensus agents,
validate the orchestrator’s saga‑based workflow and recovery logic, and serve as a
foundation for future integration tests covering full design flows.

## Test Overview

The test suite resides under the `tests/` directory and can be executed
using `pytest`. It covers the following scenarios:

- **Meta‑Cognition questions**: When provided with a list of missing
  fields (e.g. `panel orientation`, `datasheet`), the
  `MetaCognitionAgent` produces a blocked response with one question per
  missing item.
- **Meta‑Cognition reason**: When given a reason string (e.g.
  `missing PV layout`), the agent formulates a single clarifying
  question containing that reason.
- **Consensus selection**: The `ConsensusAgent` receives multiple
  candidate outputs containing confidence values and selects the design
  with the highest confidence, returning the chosen card and patch.
- **Orchestrator workflow**: The `PlannerOrchestrator` executes a multi‑step saga
  workflow (for example, `generate_network`, `generate_site`,
  `generate_battery`, `generate_monitoring`) and produces calibrated
  design cards with confidence and dynamic thresholds.  The test
  verifies that the design graph contains the expected placeholder nodes
  and edges.
- **Recovery & retry**: A blocked task is manually registered with the
  retry manager.  When the orchestrator runs a workflow containing that
  task, it automatically resolves and clears the blocked task queue.
  The test ensures the blocked queue is empty after the workflow
  completes.

## Running the Tests

From the repository root, install `pytest` if necessary and run:

```sh
pip install pytest
pytest -q
```

These tests rely on the presence of `backend.utils.adpf.wrap_response`
for the meta‑cognition and consensus agents. If the module is missing,
those tests will be skipped automatically.  The orchestrator tests
assume that the saga engine, confidence calibrator and recovery
manager are integrated as in the current codebase.

## Extending Scenario Tests

In future phases, additional tests should be added to cover:

- Full plan–act design flows involving multiple domain agents and the
  saga workflow engine.
- User interactions through the UI and API endpoints, using test
  clients to simulate HTTP requests.
- Error handling and recovery scenarios, including compensation of
  failed saga steps and idempotent patch application.

These tests form an essential part of the quality assurance process and
help prevent regressions as OriginFlow continues to evolve.

## Developer Guidance

When writing new tests, consult the [developer onboarding guide](developer_guide.md)
for best practices. The guide provides templates for writing asynchronous tests,
explains how to use the `safe_execute` wrapper in test contexts and highlights
how to extend scenario coverage as new agents and workflows are added.

