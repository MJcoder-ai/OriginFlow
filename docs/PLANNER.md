# Server-side planner (Phase 3)

## Overview
The planner converts a natural-language request into a deterministic list of
typed tasks the orchestrator can execute. It deliberately avoids model calls
for MVP reliability and testability.

### Endpoint
```
GET /api/v1/odl/sessions/{session_id}/plan?command=...
```
Response:
```json
{
  "tasks": [
    { "id": "make_placeholders", "title": "Create inverter", "status": "pending",
      "args": { "component_type": "inverter", "count": 1, "layer": "electrical" } },
    { "id": "make_placeholders", "title": "Create 12 panels", "status": "pending",
      "args": { "component_type": "panel", "count": 12, "layer": "electrical" } },
    { "id": "generate_wiring", "title": "Generate wiring", "status": "pending",
      "args": { "layer": "electrical" } }
  ],
  "metadata": {
    "session_id": "s1",
    "parsed": { "target_kw": 5.0, "panel_watts": 400, "layer": "electrical" },
    "assumptions": { "defaulted_target_kw": false, "defaulted_panel_watts": true, "defaulted_layer": false }
  }
}
```

### Parsing
`backend/planner/parser.py` recognizes:
- Target size: `(\d+(\.\d+)?)\s*kW` (defaults to 5 kW)
- Panel wattage hints: `(\d{3,4})\s*W` when “panel/module” is mentioned (defaults to 400 W)
- Layer hints: `single-line` or `electrical` (defaults to `electrical`)

### Execution
Clients call `/odl/{sid}/act` with the `args` from each task. The orchestrator
applies patches with optimistic concurrency (respecting `If-Match`).
