# Action Approvals v1

This document describes the tenant-scoped approval pipeline for AI-proposed actions.

## Data model
- `pending_actions`:
  - Keys: `tenant_id`, `project_id?`, `session_id?`, `agent_name?`,
    `action_type`, `payload`, `confidence?`
  - State machine: `pending -> approved|rejected -> applied`
  - Audit fields: `requested_by_id`, `approved_by_id`, timestamps, `reason`

## Policy
Resolved per-tenant:
- Threshold: `approvals.threshold` (tenant setting) or `APPROVALS_THRESHOLD` env; default **0.85**
- Allow/Deny lists: `approvals.allowlist`, `approvals.denylist`
  (or env `APPROVALS_ALLOWLIST`, `APPROVALS_DENYLIST`, comma-separated)
Evaluation order: **denylist → allowlist → threshold(compare confidence)**.

## Backend integration
`AiOrchestrator.process` (and other action planners) now:
1. Plan and validate actions as before.
2. For each action, call `ApprovalPolicyService.evaluate(...)`.
3. If **auto-approved**: proceed normally.
4. If **not auto-approved**: enqueue in `pending_actions` and skip execution.
   If anything fails during evaluation, a warning is logged and the original
   behaviour continues.

## API
- `GET /api/v1/approvals?status=pending&session_id=...` — list (RBAC: `approvals.read`)
- `POST /api/v1/approvals/{id}/approve` — approve and optionally apply (RBAC: `approvals.approve`)
  - Body: `{ "note"?: string, "approve_and_apply"?: boolean }`
  - If `approve_and_apply=true` the backend executes the action and marks it `applied`.
- `POST /api/v1/approvals/{id}/reject` — reject (RBAC: `approvals.approve`)
- `POST /api/v1/approvals/batch` — batch approve/reject (RBAC: `approvals.approve`)

> Approve response includes `apply_client_side: true` when the server did not
> execute the action. Clients may then POST to `/api/v1/odl/sessions/{session_id}/act`
> with the returned payload.

## Frontend (MVP)
New sidebar item **Approvals** showing pending items with Approve/Reject.
On Approve, the client can choose to:
1) Call `/approvals/{id}/approve` with `approve_and_apply=true` to execute
   server-side, **or**
2) Call `/approvals/{id}/approve` (default), then POST to
   `/api/v1/odl/sessions/{session_id}/act` with the returned payload to apply
   client-side.

Polling is used initially (no WS dependency). SSE/WS can be added later.

## RBAC
- `approvals.read` to view the queue
- `approvals.approve` to decide items

## Notes
- This patch is additive and safe. If anything in policy evaluation fails, the service logs a warning and continues with the original execute path.
- You can tune thresholds/allowlists per tenant via settings or env immediately—no redeploy required.

