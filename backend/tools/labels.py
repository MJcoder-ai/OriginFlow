from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, ODLEdge, ODLNode, make_patch


class GenerateLabelsInput(ToolBase):
    view_nodes: List[ODLNode] | List[Dict] = Field(default_factory=list)
    view_edges: List[ODLEdge] | List[Dict] = Field(default_factory=list)
    include_conduit_ids: bool = True
    include_service_labels: bool = True


def _infer_labels(nodes: List[ODLNode], edges: List[ODLEdge]) -> List[Dict]:
    labels = []
    # helper accessors
    def n_type(n):
        return n.get("type") if isinstance(n, dict) else getattr(n, "type", "")

    def e_kind(e):
        return e.get("kind") if isinstance(e, dict) else getattr(e, "kind", "")

    def e_attrs(e):
        return e.get("attrs", {}) if isinstance(e, dict) else getattr(e, "attrs", {})

    # Service / interconnection
    if any("service_panel" in n_type(n) for n in nodes):
        labels.append(
            {
                "kind": "placard",
                "text": "PV SYSTEM CONNECTED TO THIS SERVICE",
                "location": "service_panel",
            }
        )
    # Rapid Shutdown
    if any("mlpe_rsd" in n_type(n) for n in nodes):
        labels.append(
            {
                "kind": "placard",
                "text": "RAPID SHUTDOWN SWITCH FOR SOLAR PV SYSTEM",
                "location": "ac_disconnect_or_service",
            }
        )
    # DC / AC Disconnects
    for n in nodes:
        t = n_type(n)
        if t == "ac_disconnect":
            labels.append(
                {
                    "kind": "device_label",
                    "text": "PV SYSTEM AC DISCONNECT",
                    "target_id": n.get("id") if isinstance(n, dict) else getattr(n, "id", None),
                }
            )
        if t == "string_inverter":
            labels.append(
                {
                    "kind": "device_label",
                    "text": "PV SYSTEM DC DISCONNECT (IF EQUIPPED)",
                    "target_id": n.get("id") if isinstance(n, dict) else getattr(n, "id", None),
                }
            )
    # Conduit / Cable markers
    dc_edges = [
        e
        for e in edges
        if e_kind(e) in ("electrical", "bundle")
        and (
            e_attrs(e).get("connection") == "dc_pv"
            or e_attrs(e).get("function", "").startswith("PV")
        )
    ]
    ac_edges = [
        e
        for e in edges
        if e_kind(e) in ("electrical", "bundle")
        and (
            "ac_" in str(e_attrs(e).get("connection", ""))
            or e_attrs(e).get("function", "") in ("L1", "L2", "L3", "N", "PE")
        )
    ]
    if dc_edges:
        labels.append({"kind": "conduit_id", "text": "SOLAR PV DC CIRCUIT", "count": len(dc_edges)})
    if ac_edges:
        labels.append({"kind": "conduit_id", "text": "SOLAR PV AC CIRCUIT", "count": len(ac_edges)})
    return labels


def generate_labels(inp: GenerateLabelsInput):
    labels = _infer_labels(inp.view_nodes, inp.view_edges)
    ops: List[PatchOp] = []
    # Store under meta.physical.labels
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:labels",
            op="set_meta",
            value={"path": "physical.labels", "merge": True, "data": labels},
        )
    )
    # Add annotation for UI to render summary
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:labels",
            op="add_edge",
            value={
                "id": f"ann:labels:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "generate_labels",
                    "summary": f"{len(labels)} labels/placards generated",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["generate_labels", "GenerateLabelsInput"]

