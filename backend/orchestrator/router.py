"""
Task router: translate high-level tasks into typed tool invocations.

The router never touches the database or ODL store; it builds tool inputs
from minimal context and returns the resulting ODLPatch (or None).
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from backend.odl.schemas import ODLPatch, ODLNode
from backend.tools.schemas import (
    GenerateWiringInput, GenerateMountsInput, AddMonitoringInput,
    MakePlaceholdersInput,
)
from backend.tools import wiring, structural, monitoring, placeholders


class ActArgs(BaseModel):
    layer: str = Field("single-line", description="ODL layer for the tool view")
    # Tool-specific args (optional)
    edge_kind: str | None = None
    mount_type: str | None = None
    device_type: str | None = None
    placeholder_type: str | None = None
    count: int | None = None
    attrs: dict[str, object] | None = None


def run_task(
    *,
    task: str,
    session_id: str,
    request_id: str,
    layer_nodes: list[ODLNode],
    args: ActArgs,
) -> Optional[ODLPatch]:
    """Build tool input for `task`, invoke, and return an ODLPatch (or None)."""
    if task == "generate_wiring":
        inp = GenerateWiringInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            edge_kind=args.edge_kind or "electrical",
        )
        return wiring.generate_wiring(inp)

    if task == "generate_mounts":
        inp = GenerateMountsInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            mount_type=args.mount_type or "mount",
            layer=args.layer or "structural",
        )
        return structural.generate_mounts(inp)

    if task == "add_monitoring":
        inp = AddMonitoringInput(
            session_id=session_id,
            request_id=request_id,
            view_nodes=layer_nodes,
            device_type=args.device_type or "monitoring",
            layer=args.layer or "electrical",
        )
        return monitoring.add_monitoring_device(inp)

    if task == "make_placeholders":
        inp = MakePlaceholdersInput(
            session_id=session_id,
            request_id=request_id,
            count=args.count or 1,
            placeholder_type=args.placeholder_type or "generic_panel",
            attrs=args.attrs or {"layer": args.layer},
        )
        return placeholders.make_placeholders(inp)

    return None
