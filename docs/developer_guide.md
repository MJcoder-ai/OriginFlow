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

## 4. Enforce Contracts and Calibration

1. Wrap agent execution with `safe_execute` so envelopes are validated
   by the schema enforcer.
2. Use `ConfidenceCalibrator` when assigning confidence scores and
   adjust thresholds based on feedback.

## 5. Recovery and Retry

Use the `RetryManager` to re‑execute blocked tasks. Agents should return
`status="blocked"` with a helpful message when required context is
missing.

## 6. Write Tests

1. Add unit or scenario tests under `tests/`.
2. Use `pytest -q` to run the suite.
3. For end‑to‑end flows, leverage asynchronous tests and the
   `safe_execute` wrapper as shown in `docs/end_to_end_tests.md`.

## 7. Submit Your Change

Run the test suite before opening a pull request and ensure all
documentation is up to date. For coding conventions, see `AGENTS.md`
and `CONTRIBUTING.md`.

