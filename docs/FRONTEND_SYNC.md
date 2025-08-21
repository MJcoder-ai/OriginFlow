# Frontend Canvas Sync (Phase 8)

The canvas is a **projection** over ODL. Keep it in sync using the following
endpoints:

1. `GET /odl/{session_id}/head` → `{session_id, version}`  
   Poll this lightweight endpoint to detect changes without pulling the view.

2. `GET /odl/{session_id}/view_delta?since=<version>&layer=<name>`  
   Returns `{changed, version, view?}`. If `changed=false`, skip re-render.
   If `changed=true`, use the returned `view` to render.

3. Apply changes via `POST /odl/{session_id}/patch` using `If-Match` with the
   current version to keep optimistic concurrency guarantees.

## UI Tips
- Use node/edge `id` and `component_master_id` as **stable references**; treat
  `name` as a display label only.
- Defer heavy recomputations until `changed=true`.
- When a patch is applied by the UI, optimistically update the canvas while a
  background poll confirms the version increment.
