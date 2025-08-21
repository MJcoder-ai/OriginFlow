# Evals, QA & Performance (Phase 9)

This directory provides a simple eval harness to exercise critical
agentic flows and detect regressions or performance issues.

## What it covers
- **PV wiring**: small end-to-end run of `generate_wiring`
- **Placeholder replacement**: orchestrator returns a `pending` proposal and on
  approval the ODL version advances
- **Budgeter**: the orchestrator warns or blocks oversized requests

## Running locally
```bash
python -m backend.scripts.run_evals
```
Produces a JSON report with `passed/failed` and brief step traces.

## CI integration
- Run the eval script on PRs and fail if any scenario fails.
- Optionally store the report artifact to track trends.

## Extending scenarios
Add a new file in `backend/evals/scenarios/`, export a `run() -> dict`, and
append to `backend/evals/runner.py`.

## Performance notes
- The **budgeter** (`backend/perf/budgeter.py`) estimates request size and
  enforces soft/hard limits before expensive work. Replace the estimator with
  a real tokenizer/cost table when needed.
