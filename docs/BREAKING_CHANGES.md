# BREAKING CHANGES (vNext)

This release intentionally **removes backward compatibility** to achieve a
cleaner, simpler, and more robust agentic architecture.

## Summary

1. **Single Response Envelope**  
   All AI/action responses now use a **single envelope**:
   ```json
   {
     "thought": "short rationale for auditability",
     "output": {
       "card": { "... optional UI advice ..." },
       "patch": { "... optional ODL patch ..." }
     },
     "status": "pending|blocked|complete",
     "warnings": ["... optional list ..."]
   }
   ```
   Top-level `card` and `patch` fields are **removed**. Clients must read
   `output.card` and `output.patch`.

2. **Legacy agent shims and compatibility layers**  
   Any helper that mirrored fields for legacy clients has been removed.
   The codebase focuses on a single orchestrator + typed tools model.

3. **Deletions / Renames (Agents → Tools; Legacy APIs removed)**  
  - All per-feature “agents” that were thin wrappers around deterministic logic
    are **deleted**. Their behavior lives in **typed tools** under
    `backend/tools/` and is invoked by the single orchestrator (`POST /ai/act`).
  - Legacy endpoints that returned duplicated envelopes or invoked
    per-feature agents are **removed**. Use:
    - ODL routes `/odl/*` for state
    - Orchestrator route `/ai/act` for actions
    - Approvals `/approvals/*` for review workflows
  - The legacy developer guide `AGENTS.md` has been archived under
    `docs/legacy/AGENTS.md`.

## Rationale
- Reduce payload size and ambiguity
- Improve testability and schema validation
- Prepare for a single-orchestrator, typed-tools architecture

## Migration
- Frontend/UI: replace any references to `card` and `patch` at the top level
  with `output.card` and `output.patch`.
- Server/integrations: if you previously post-processed top-level `card/patch`,
  update to the nested `output` object.

- Replace direct agent calls with **orchestrator-mediated** calls:
  - ❌ `POST /<legacy-agent-endpoint>`  
    ✅ `POST /ai/act` with `task` + `args`, then `/odl/{sid}/patch`
- Replace any DB-touching agent logic with **tools** (pure) and **services**
  (DB), coordinated by the orchestrator.

## Deployment Notes
1. Tag the previous release (e.g., `legacy-archive`) before merging.
2. Roll this change out together with updated frontend builds.

