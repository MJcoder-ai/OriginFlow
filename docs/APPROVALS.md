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
`AnalyzeService.process` now:
1. Plans & validates actions as before.
2. For each action, calls `ApprovalPolicyService.evaluate(...)`.
3. If **auto-approved**: executes normally.
4. If **not auto-approved**: enqueues in `pending_actions`, **skips execution**, and returns `{"status":"queued","queued":[...]}`.
   (Existing behavior is preserved on any failure; pipeline remains robust.)

## API
- `GET /api/v1/approvals?status=pending&session_id=...` — list (RBAC: `approvals.read`)
- `POST /api/v1/approvals/{id}/approve` — approve (RBAC: `approvals.approve`)
- `POST /api/v1/approvals/{id}/reject` — reject (RBAC: `approvals.approve`)
- `POST /api/v1/approvals/batch` — batch approve/reject (RBAC: `approvals.approve`)

> Approve response includes the action `payload` so the client can call the **existing** `/act` endpoint to apply.
> (Applying on the server can be added later if you prefer server-side execution.)

## Frontend (MVP)
New sidebar item **Approvals** showing pending items with Approve/Reject.
On Approve, the client:
1) Calls `/approvals/{id}/approve`,
2) Then POSTs to `/api/v1/odl/sessions/{session_id}/act` with returned payload to apply.

Polling is used initially (no WS dependency). SSE/WS can be added later.

## RBAC
- `approvals.read` to view the queue
- `approvals.approve` to decide items

## Notes
- This patch is additive and safe. If anything in policy evaluation fails, the service logs a warning and continues with the original execute path.
- You can tune thresholds/allowlists per tenant via settings or env immediately—no redeploy required.

