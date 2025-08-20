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

## Rationale
- Reduce payload size and ambiguity
- Improve testability and schema validation
- Prepare for a single-orchestrator, typed-tools architecture

## Migration
- Frontend/UI: replace any references to `card` and `patch` at the top level
  with `output.card` and `output.patch`.
- Server/integrations: if you previously post-processed top-level `card/patch`,
  update to the nested `output` object.

## Deployment Notes
1. Tag the previous release (e.g., `legacy-archive`) before merging.
2. Roll this change out together with updated frontend builds.

