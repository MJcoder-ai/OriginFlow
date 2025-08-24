# API Endpoints — OriginFlow

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
GET /api/v1/odl/sessions/{session_id}/plan?command={text}[&layer=single-line|electrical]
```
Returns a **LongPlan** – a typed, multi-step plan tailored to the current
session. The planner deterministically converts natural language (for example,
"design a 5 kW PV system") into a sequence of tool invocations with
dependencies. Clients then execute each step via `POST /ai/act`.

The default PV workflow includes tasks such as:

- `select_equipment`
- `select_dc_stringing`
- `select_ocp_dc`
- `select_conductors_v2`
- `generate_wiring`
- `check_compliance_v2`
- `generate_bom`

### Get canonical ODL text (for the active layer)
```
GET /api/v1/odl/sessions/{session_id}/text?layer=single-line|electrical
```
Returns:
```json
{ "session_id": "demo", "version": 7, "text": "node inv1 : inverter\nlink inv1 -> p1\n" }
```
This is a stable, line-oriented format intended for copy/paste, diff, and export.
If `layer` is omitted, `single-line` is used.

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

The following endpoints are not part of the current OriginFlow API and are **not provided**:


- `/api/v1/ai/analyze-design` – use `GET /api/v1/odl/{sid}/plan` + `POST /api/v1/ai/act`
- `/api/v1/ai/plan` – use `GET /api/v1/odl/{sid}/plan`

