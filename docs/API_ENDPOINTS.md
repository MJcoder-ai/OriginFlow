# OriginFlow API (vNext)

This document summarizes the canonical API surface exposed by the backend.

## ODL – design graph

### Create session
```
POST /api/v1/odl/sessions?session_id={id}
```
- Starts a new graph at `version=1`.
- Uses optimistic concurrency on patch via the `If-Match` header.

### Read head (current version)
```
GET /api/v1/odl/{session_id}/head
```

### Read a view
```
GET /api/v1/odl/{session_id}/view?layer={name}
```

### Build a plan (server-side planner)
```
GET /api/v1/odl/sessions/{session_id}/plan?command={text}
```
Parses the natural-language command (e.g., “design a 5 kW solar PV system”)
and returns a deterministic plan of tasks that clients can execute via `/odl/{sid}/act`.
For MVP the planner is rule-based (no model calls) and emits:
- `make_placeholders` (inverter)
- `make_placeholders` (N panels calculated from target kW and panel wattage)
- `generate_wiring`

## AI orchestrator

### Perform a typed action
```
POST /api/v1/ai/act
{
  "session_id": "s1",
  "task": "make_placeholders",
  "request_id": "uuid",
  "args": { "component_type": "panel", "count": 12, "layer": "electrical" }
}
```
Returns an ADPF envelope and applies the patch if policy allows.

### (Optional) Intent Firewall direct apply
```
POST /api/v1/ai/apply
{ "session_id": "s1", "actions": [ ... ], "user_texts": [ ... ] }
```

## Removed endpoints (not available)
The following endpoints are not part of vNext and are **not provided**:

- `/api/v1/ai/analyze-design` – use `GET /api/v1/odl/{sid}/plan` + `POST /api/v1/ai/act`
- `/api/v1/ai/plan` – use `GET /api/v1/odl/{sid}/plan`
- `/api/v1/odl/sessions/{sid}/text` – prefer `GET /api/v1/odl/{sid}/view?layer=...`

> If you need a text serializer for the "ODL Code" pane, implement
> `GET /api/v1/odl/sessions/{sid}/text` using the graph serializer and return
> `{ "session_id": sid, "version": n, "text": "..." }`.

