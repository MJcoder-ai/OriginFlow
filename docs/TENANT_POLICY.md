# Tenant Policy (Per-Tenant Risk & Feature Configuration)

This module lets tenant admins configure:

- **Auto-approval** enable/disable  
- **Default risk threshold** (0–1) for confidence-based auto-approvals  
- **Action allow/deny lists** (whitelist/blacklist)  
- **Enabled domains** (e.g., `pv`, `wiring`, `structural`, `battery`)  
- **Feature flags** (e.g., `placeholder_fallback_enabled`, `server_side_apply_default`, `live_updates_enabled`, `agent_registry_hydrate_on_request`)  

All changes are **audit-logged** and guarded by RBAC.

## API

- `GET /api/v1/tenant/settings` *(RBAC: `tenant.settings.read`)*  
  Returns the full policy document with `version` for optimistic concurrency.

- `PUT /api/v1/tenant/settings` *(RBAC: `tenant.settings.write`)*  
  Body: partial update + required `version`. Validates ranges and shapes.  
  On success, increments `version`, returns updated doc.  
  On conflict, returns **409** with message “Version conflict”.

- `POST /api/v1/tenant/settings/test` *(RBAC: `tenant.settings.read`)*  
  Body: `{ action_type, confidence, agent_name? }` →  
  Result: `{ auto_approved, reason, threshold_used, matched_rule? }`.

## Frontend

**Settings → Tenant Policy** page provides:
- Form controls for auto-approval, threshold, allow/deny lists, domains, feature flags.  
- **Dry-run tester** to see how a candidate action would be decided.  
- Unsaved change detection and versioned saves (optimistic concurrency).

## Notes
- Existing consumers of `tenant_settings.data` continue to work; the structured fields are **additive**.
- If `ApprovalPolicyService` is present, `test` delegates to it; otherwise a safe fallback is used.
- Feature flags can be read at request time (e.g., to hydrate agent registry per tenant).

## Caching

Policies are served via an in-memory `PolicyCache` with a short TTL.
If the cache is unavailable, the system falls back to database reads.

## Where policy is enforced (runtime)

- **Analyze/Orchestration** – every proposed action is evaluated through
  `ApprovalPolicyService.is_auto_approved` using the cached policy.
- **Approvals Queue** – non auto-approved actions are persisted via
  `ApprovalQueueService.enqueue_from_action`.
- **Agent Registry Hydration** – agent specs are filtered by
  `enabled_domains` and conditioned by `feature_flags` when hydrating
  per-tenant registries.
- **Router Agent (optional)** – domain suggestions may be gated by
  enabled domains to avoid surfacing disabled capabilities.
- **All policy reads** go through `PolicyCache`; runtime decisions should
  never query the database directly.
