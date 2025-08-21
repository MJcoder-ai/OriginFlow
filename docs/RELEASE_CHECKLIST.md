Release Checklist
Use this checklist to validate a release candidate.

Functional
- All public routes documented in docs/API_CONTRACTS.md respond with the single envelope.
- ODL patch CAS works: concurrent write returns 409; idempotent re-apply is a no-op.
- Orchestrator budgeter warns/blocks oversized requests (Phase 9).
- Approvals flow applies patch on approve and logs audit events.

Evals & QA
- `python -m backend.scripts.run_evals` → all scenarios pass.
- Unit tests pass (tools, budgeter, orchestrator happy-paths).

Docs
- docs/ARCHITECTURE_OVERVIEW.md is current.
- API changes reflected in docs/API_CONTRACTS.md.

Deployment
- DB migrations applied (if any new tables).
- Previous release tagged; changelog updated.
- Observability dashboards receiving traces/metrics.
