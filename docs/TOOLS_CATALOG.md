# Tools Catalog (Phase 3)

Tools are **pure functions** with typed inputs and outputs. They never access
the database or ODL store directly. The orchestrator will compose tools,
apply their returned `ODLPatch` objects via the ODL API, and manage risk,
approvals, memory, and audit.

## Files
- `backend/tools/schemas.py` — shared Pydantic models and `make_patch()`
- `backend/tools/selection.py` — rank library components for placeholders
- `backend/tools/wiring.py` — generate electrical edges between panels/inverters
- `backend/tools/structural.py` — create mount nodes and mechanical edges
- `backend/tools/monitoring.py` — add monitoring node and data edges
- `backend/tools/placeholders.py` — create placeholder nodes for early design
- `backend/tools/consensus.py` — rank candidates by different objectives

## General pattern
Inputs include:
- `session_id` (opaque), `request_id` (idempotency scope)
- View nodes (`ODLNode[]`) for the layer the tool operates on
- Tool-specific parameters (e.g., layer name, device type)

Outputs:
- An `ODLPatch` with `patch_id = "patch:{request_id}"` and per-op `op_id`s
  derived from the request id, ensuring **idempotency** if the same call is
  repeated.

## Example (wiring)
```python
from backend.tools.schemas import GenerateWiringInput
from backend.tools.wiring import generate_wiring

patch = generate_wiring(GenerateWiringInput(
    session_id="sess-1",
    request_id="req-123",
    view_nodes=electrical_view.nodes,
    edge_kind="electrical",
))
# orchestrator -> POST /odl/{session_id}/patch with If-Match header
```

## Notes
- Tools target **simplicity and determinism**. Advanced logic belongs in the
  orchestrator (Phase 4) and policy layers (risk/approvals).
- Use Pydantic v2 models for all tool inputs/outputs to catch errors early.

## Electrical/PV
- select_equipment: choose inverter/module placeholders or real parts from requirements
- select_dc_stringing: compute series/parallel grouping across MPPTs
- select_ocp_dc: size DC-side protection (fuses/breakers)
- select_conductors_v2: determine conductor sizes with derates
- generate_wiring: auto–link placeholders and sized conductors
- check_compliance_v2: run rule set and emit warnings
- generate_bom: derive BOM items and quantities
