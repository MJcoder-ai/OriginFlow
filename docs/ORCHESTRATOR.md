# Orchestrator (Phase 4)

The orchestrator provides a single AI entrypoint that:
1. Minimizes context by fetching only the required ODL slice (layer view)
2. Routes a high-level task to a typed tool
3. Applies a returned `ODLPatch` via the ODL store with optimistic concurrency
4. Enforces a simple risk policy (`auto`, `review_required`, `blocked`)
5. Returns the **single** ADPF envelope (`thought`, `output.card`, `output.patch`, `status`, `warnings?`)

## API
`POST /ai/act`
```json
{
  "session_id": "sess-123",
  "task": "generate_wiring",
  "request_id": "r-abc-1",
  "args": { "layer": "electrical", "edge_kind": "electrical" }
}
```

## Internals
- **Context** — `backend/orchestrator/context.py` loads the graph and computes a
  minimal layer view (`nodes`), avoiding large unneeded payloads.
- **Router** — `backend/orchestrator/router.py` translates `task`+`args` into a
  typed tool call. Tools are pure and deterministic.
- **Policy** — `backend/orchestrator/policy.py` returns `auto` /
  `review_required` / `blocked`. In Phase 6 this will incorporate calibrated
  model confidence and human approvals.
- **Execution** — `backend/orchestrator/orchestrator.py` composes the above and
  applies patches via the ODL store (`apply_patch_cas`).

## Adding a new task
1. Implement a tool in `backend/tools/` (typed inputs/outputs).
2. Extend the task router to build the tool input.
3. Add a risk class in `policy.py`.
4. Write a small E2E test asserting the envelope and the new ODL version.
