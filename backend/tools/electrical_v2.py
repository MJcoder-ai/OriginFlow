"""Minimal electrical v2 tools used by auto-designer tests.

These are lightweight wrappers that emit annotation-only patches. They are
placeholders until full electrical_v2 implementations are available."""
from __future__ import annotations

from typing import List
from pydantic import BaseModel

from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class SelectOcpACV2Input(ToolBase):
    inverter_inom_A: float


def select_ocp_ac_v2(inp: SelectOcpACV2Input):
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:ocpac",
            op="add_edge",
            value={
                "id": f"ann:ocpac:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "select_ocp_ac_v2", "inom_A": inp.inverter_inom_A},
            },
        )
    ]
    return make_patch(inp.request_id, ops)


class SelectConductorsV2Input(ToolBase):
    circuit_kind: str
    current_A: float
    length_m: float
    system_v: float


def select_conductors_v2(inp: SelectConductorsV2Input):
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:conductor",
            op="add_edge",
            value={
                "id": f"ann:conductor:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "select_conductors_v2",
                    "kind": inp.circuit_kind,
                    "current_A": inp.current_A,
                },
            },
        )
    ]
    return make_patch(inp.request_id, ops)


class ExpandConnectionsV2Input(ToolBase):
    source_id: str
    target_id: str
    connection_type: str
    add_ground: bool = False


def expand_connections_v2(inp: ExpandConnectionsV2Input):
    bundle_id = f"bundle:{inp.source_id}:{inp.target_id}:{inp.connection_type}"
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:edge:bundle",
            op="add_edge",
            value={
                "id": bundle_id,
                "source_id": inp.source_id,
                "target_id": inp.target_id,
                "kind": "bundle",
                "attrs": {"system": inp.connection_type},
            },
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:bundle",
            op="add_edge",
            value={
                "id": f"ann:bundle:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "expand_connections_v2", "bundle_id": bundle_id},
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = [
    "SelectOcpACV2Input",
    "select_ocp_ac_v2",
    "SelectConductorsV2Input",
    "select_conductors_v2",
    "ExpandConnectionsV2Input",
    "expand_connections_v2",
]

