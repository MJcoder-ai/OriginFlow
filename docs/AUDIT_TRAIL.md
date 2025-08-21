# Audit Trail

All key events are written to `audit_events`:
- `patch_proposed` – user or orchestrator proposed a change
- `patch_approved` – reviewer approved
- `patch_applied` – change persisted via ODL CAS
- `patch_rejected` – reviewer rejected

Use this to build a timeline per session for compliance and debugging.
