# End‑to‑End Scenario Tests (Phase 17)

To ensure that OriginFlow operates correctly across its various agents
and calibration components, a set of end‑to‑end scenario tests has been
added. These tests exercise the meta‑cognition and consensus agents,
verify the behaviour of the confidence calibrator, and serve as a
foundation for future integration tests covering full design flows.

## Test Overview

The new tests reside under the `tests/` directory and can be executed
using `pytest`. They cover the following scenarios:

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
- **Confidence calibration**: The `ConfidenceCalibrator` records
  feedback (approval/rejection) for a specific agent and action type,
  computes an acceptance rate, adjusts a new confidence score towards
  neutrality when feedback is mixed, and leaves thresholds unchanged
  when the acceptance rate is neutral (0.5).

## Running the Tests

From the repository root, install `pytest` if necessary and run:

```sh
pip install pytest
pytest -q
```

These tests rely on the presence of `backend.utils.adpf.wrap_response`
for the meta‑cognition and consensus agents. If the module is missing,
those tests will be skipped automatically.

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

