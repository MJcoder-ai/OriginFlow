Coding Standards

Python: Pydantic v2 for schemas; typing annotations required.

Pure tools: no DB access; operate on typed inputs; return ODLPatch.

Idempotency: every patch operation has a stable op_id; every patch has a stable patch_id.

CAS everywhere: ODL mutations require If-Match version; never blind-write.

Single envelope: only thought, output, status, warnings?. No legacy top-level card/patch.

Logging/Audit: every important action should emit an audited event via the audit helper.

Tests: aim for fast unit tests; E2E flows covered by eval scenarios.
