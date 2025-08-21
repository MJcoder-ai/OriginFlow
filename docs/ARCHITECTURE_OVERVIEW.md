# Architecture Overview (vNext)

This document summarizes the **clean, modern agentic architecture** shipped in Phases 1–9. The codebase favors **one LLM-backed orchestrator**, a **typed tool catalog**, and a **state-aware ODL model** as the single source of truth.

## Big picture
```text
        ┌───────────────────────┐
        │       Frontend        │
        │  (Canvas & Console)   │
        └──────────┬────────────┘
                   │          REST APIs
                   ▼
  ┌───────────────────────────────────┐
  │           Orchestrator            │
  │  /ai/act                          │
  │  - context minimizer              │
  │  - task → tool routing            │
  │  - risk policy                    │
  │  - CAS apply ODL patch            │
  └───────┬───────────────────────────┘
          │  typed tool I/O (pure; no DB)
          ▼
┌────────────────────┐ ┌─────────────────────┐
│ Tools (pure)       │ │ Services (DB)       │
│ wiring, structural │ │ component_library   │
│ placeholders, etc. │ │ approvals/audit     │
└──────────┬─────────┘ └──────────┬──────────┘
           │                      │
           ▼                      ▼
┌────────────────┐    ┌────────────────────┐
│ ODL Store      │    │ SQL persistence    │
│ /odl/*, views  │    │ (components, logs) │
└────────────────┘    └────────────────────┘
```

## Key principles
- **Single envelope** responses (`thought`, `output.card`, `output.patch`, `status`, `warnings?`).
- **ODL is truth**: all canvases/layers are derived projections from ODL.
- **Typed tools**: deterministic, pure, easy to test, no DB access.
- **One orchestrator**: minimizes context, routes tasks, enforces policy, applies patches via CAS.
- **Governance & audit**: review-required actions go through approvals; every action is logged.
- **Domains**: declarative config drives placeholder→category mapping and risk overrides.
- **Performance & evals**: budgeter enforces guardrails; scenarios catch regressions.

## Primary modules
- `backend/odl/*` — schemas, patches, store, views (Phase 2)
- `backend/tools/*` — typed tools (Phase 3)
- `backend/orchestrator/*` — orchestrator/core (Phase 4–6)
- `backend/governance/*`, `backend/audit/*`, `backend/memory/*` (Phase 6)
- `backend/domains/*` — domain registry and YAML config (Phase 7)
- `backend/perf/budgeter.py` — request budget guard (Phase 9)
- `backend/evals/*` — eval scenarios & runner (Phase 9)

## Public APIs (summary)
- **ODL**
  - `POST /odl/sessions?session_id=...` → create/return session graph (v=1)
  - `GET  /odl/{session_id}` → full ODL
  - `POST /odl/{session_id}/patch` (requires `If-Match`) → apply ODLPatch
  - `GET  /odl/{session_id}/view?layer=...` → derived projection
  - `GET  /odl/{session_id}/head` → `{session_id, version}`
  - `GET  /odl/{session_id}/view_delta?since=...&layer=...` → `{changed, version, view?}`
- **AI**
  - `POST /ai/act` → orchestrator run; returns ADPF envelope
- **Approvals**
  - `POST /approvals/propose` → store a proposed patch
  - `POST /approvals/{id}/decision` → approve/reject; on approve, patch applied via CAS
  - `GET  /approvals?session_id=...` → list proposals
- **Naming policy**
  - `GET /naming-policy` / `PUT /naming-policy` (Option B with retro-apply)

See the individual docs for details.

## Implementation Status Notes
Several services contain placeholder implementations marked with TODO comments:
- `backend/services/compatibility.py` - Rule validation stubs for electrical, mechanical, thermal, and communication compatibility
- `backend/services/calculation_engines.py` - HVAC and water pump sizing engines
- `backend/services/learning_agent_service.py` - ML model integration for action scoring
- `backend/services/vector_store.py` - Vector database protocol implementations