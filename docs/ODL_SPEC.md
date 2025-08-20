# ODL – Single Source of Truth

This specification describes the state model, patch protocol, versioning and
derived views for OriginFlow's Open Design Language (ODL).

## State model
The ODL state for a session is a versioned graph:
- **nodes** – typed entities (e.g., panel, inverter, battery) with
  `component_master_id` (stable part link) and an `attrs` dict for structured
  metadata.
- **edges** – typed relations (electrical, mechanical, data) with optional attrs.
- **meta** – session-level metadata (requirements, domain).

## Versioning and concurrency
- Each session has an integer `version` starting at 1.
- Applying a patch requires an **optimistic concurrency** header:
  `If-Match: <current_version>`.
- On success, version increments by 1.

## Patches and idempotency
Patches contain a `patch_id` and a list of operations. Each operation must have
an `op_id` that is tracked to ensure **idempotency**: re-sending the same
operation is safe.

Supported operations:
- `add_node`, `update_node`, `remove_node`
- `add_edge`, `update_edge`, `remove_edge`
- `set_meta`

## Derived views (canvas layers)
Canvas and other visualizations must call `GET /odl/{session_id}/view?layer=...`
to retrieve the correct projection. Views are **pure functions** over ODL state.

## API routes
- `POST /odl/sessions` – create or return an existing session graph (version=1)
- `GET /odl/{session_id}` – full ODL state for a session
- `POST /odl/{session_id}/patch` – apply a patch with `If-Match`
- `GET /odl/{session_id}/view?layer=...` – derived projection

## Rationale
- A single, versioned source of truth prevents drift between canvases.
- Pure patch & view functions keep logic deterministic and testable.
- Idempotency and CAS ensure robust retries and safe concurrency.
