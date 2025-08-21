# API Contracts (vNext)

This document captures the **current** API surface. Backward compatibility with legacy envelopes/endpoints is intentionally **not** maintained.

## Response envelope (ADPF)
```json
{
  "thought": "short rationale for audit",
  "output": {
    "card":  { /* optional UI hint */ },
    "patch": { /* optional small patch ack */ }
  },
  "status": "pending|blocked|complete",
  "warnings": ["optional strings"]
}
```
`thought` is concise; persisted to audit logs.

`output.card` is for UI; `output.patch` is a small payload (full ODL fetched via /odl).

`status` drives UI affordances (apply, approve, or retry).

`warnings` communicates budget or policy notes.

## Endpoints (selected)

### ODL
- `POST /odl/sessions?session_id=SID`
- `GET /odl/{SID}`
- `POST /odl/{SID}/patch` (headers: `If-Match: <version>`)
- `GET /odl/{SID}/view?layer=LAYER`
- `GET /odl/{SID}/head`
- `GET /odl/{SID}/view_delta?since=VER&layer=LAYER`

### Orchestrator
- `POST /ai/act`
  body:
  ```json
  {
    "session_id": "SID",
    "task": "generate_wiring|generate_mounts|add_monitoring|make_placeholders|replace_placeholders",
    "request_id": "RID",
    "args": { "layer": "electrical", "...": "tool-specific" }
  }
  ```

### Approvals (governance)
- `POST /approvals/propose`
- `POST /approvals/{id}/decision` `{ "decision": "approve|reject" }`
- `GET /approvals?session_id=SID`

### Naming policy
- `GET /naming-policy` / `PUT /naming-policy`
