# Governance (Risk, Approvals)

The orchestrator assigns a **risk class** to each task. In Phase 4 we used a
static policy (`low`, `medium`, `high`) → decision (`auto`, `review_required`,
`blocked`). In Phase 6 we connect this to a lightweight approvals API so
`review_required` actions propose a patch for human approval.

## Flow
1. Orchestrator returns `status="pending"` with a `propose_patch` action.
2. Client calls `POST /approvals/propose` with that patch payload.
3. Reviewer calls `POST /approvals/{id}/decision` with `approve|reject`.
   - On **approve**, the server applies the patch via ODL CAS and logs audit
     events (`patch_approved`, `patch_applied`).
   - On **reject**, the server logs `patch_rejected`.

## Extend
- Add calibrated confidence, org/user policy, and per-task thresholds.
- Surface pending approvals in the UI with diffs of ODL patches.
