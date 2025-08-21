Contributing Guide
Thanks for helping build OriginFlow! This guide explains how to add tools, extend the orchestrator, and work with the ODL single source of truth.

Quick start
```bash
# run evals (E2E sanity)
python -m backend.scripts.run_evals
```

### Adding a new tool
- Create a typed input/output in `backend/tools/schemas.py`.
- Implement the pure function in `backend/tools/<your_tool>.py`:
  - No DB access.
  - Accepts typed input.
  - Returns ODLPatch with idempotent op_ids.
- Add a small unit test or extend an eval scenario.

### Wiring a tool into the orchestrator
- Extend `backend/orchestrator/router.py` to build the tool’s input from ActArgs and return its ODLPatch.
- Optionally map the task in `backend/orchestrator/policy.py` for risk class.
- Update docs if it is a public task.

### Working with ODL
- Use `/odl/sessions`, `/odl/{sid}`, `/odl/{sid}/patch` (with If-Match) and `/odl/{sid}/view?layer=...` in dev tools or tests.
- Patches must be idempotent; repeated application must be safe.

### Governance, Audit, Memory
- `review_required` actions should return a `propose_patch` action for the UI.
- The Approvals API applies the patch on approve and logs audit events.
- Store only structured, compact memory (no raw transcripts).

### Style & quality
- Follow `docs/CODING_STANDARDS.md`.
- Keep functions small and deterministic.
- Prefer Pydantic v2 models over loose dicts at module boundaries.
