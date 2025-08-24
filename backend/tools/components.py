"""Component metadata enrichment."""
from __future__ import annotations

from backend.odl.schemas import PatchOp
from .schemas import EnrichComponentMetadataInput, make_patch


def enrich_component_metadata(inp: EnrichComponentMetadataInput):
    out = dict(inp.existing_json)
    out.update(inp.new_attrs)
    prov = list(out.get("provenance") or [])
    if inp.provenance:
        prov.append(inp.provenance)
    out["provenance"] = prov
    old_v = str(out.get("version", "1.0.0")).split(".")
    try:
        old_v[1] = str(int(old_v[1]) + 1)
    except Exception:
        pass
    out["version"] = ".".join(old_v)
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:enrich",
            op="add_edge",
            value={
                "id": f"ann:component_enrich:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "enrich_component_metadata", "component_json": out},
            },
        )
    ]
    return make_patch(inp.request_id, ops)

