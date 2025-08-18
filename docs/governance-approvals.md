# Governance & Approvals (MVP)

This module introduces **per-tenant settings** and a **manual approval queue** for AI actions.

## Concepts

- **TenantSettings** – per-tenant risk thresholds, auto-approval toggle, action whitelists, and feature flags.
- **PendingAction** – an AI-proposed action that requires manual approval (status: pending/approved/rejected).
- **RiskPolicy** – now supports tenant overrides and whitelists; defaults remain unchanged if settings are absent.

## API

- `GET /api/v1/tenant/{tenant_id}/settings` – read settings
- `PUT /api/v1/tenant/{tenant_id}/settings` – update settings (requires `policy:edit`)
- `GET /api/v1/tenant/{tenant_id}/approvals?status=pending|approved|rejected&project_id=...` – list (requires `approvals:review`)
- `POST /api/v1/approvals/{id}/approve|reject` – decide (requires `approvals:review`)

## Frontend

- Settings → Governance & Approvals shows settings and a queue (polling every 10s). This uses simple REST polling and can be upgraded to websockets later.

## How it works

1. Router/Analyze orchestrators validate actions as before.
2. Risk-based decision uses tenant thresholds and whitelists when available; otherwise defaults apply.
3. Actions not auto-approved are persisted to `pending_actions` along with metadata.
4. Reviewers approve or reject via the API or UI; decisions are stored for audit.

## Backwards compatibility

- Existing action schemas and orchestrator flows remain unchanged; tenant context is optional and defaults to `tenant_default` when not provided.

## Future enhancements

- Project-level approval views and websocket notifications.
- Per-action RBAC and delegated approvals.

