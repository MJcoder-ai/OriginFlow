"""Datasheet ingestion utilities."""
from __future__ import annotations

from backend.odl.schemas import PatchOp
from .schemas import IngestComponentJsonInput, make_patch


def ingest_component_json(inp: IngestComponentJsonInput):
    canon = {}
    for k, v in inp.raw.items():
        canon[inp.mapping.get(k, k)] = v
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:ingest",
            op="add_edge",
            value={
                "id": f"ann:ingest:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "ingest_component_json", "component_json": canon},
            },
        )
    ]
    return make_patch(inp.request_id, ops)

