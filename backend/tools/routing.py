from __future__ import annotations
from typing import List, Dict, Tuple
from math import sqrt
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class Pose(BaseModel):
    x: float
    y: float
    z: float = 0.0


class Waypoint(BaseModel):
    id: str
    pose: Pose


class BundleRef(BaseModel):
    id: str
    source_id: str
    target_id: str
    system: str
    # optional conductor summary; not required here
    attrs: Dict = Field(default_factory=dict)


class PlanRoutesInput(ToolBase):
    """
    Plan route segments for bundles. If poses are provided for nodes/waypoints,
    we compute straight-line or waypointed distances; otherwise we fallback to a default length.
    """

    bundles: List[BundleRef]
    node_poses: Dict[str, Pose] = Field(default_factory=dict)
    waypoints: Dict[str, List[Waypoint]] = Field(default_factory=dict)  # bundle_id -> list of waypoints
    default_env: str = "indoor"
    default_length_m: float = 1.0


def _seg_len(a: Pose, b: Pose) -> float:
    dx, dy, dz = a.x - b.x, a.y - b.y, a.z - b.z
    return sqrt(dx * dx + dy * dy + dz * dz)


def plan_routes(inp: PlanRoutesInput):
    routes = []
    bundle_lengths: Dict[str, float] = {}
    for b in inp.bundles:
        pts: List[Tuple[str, Pose]] = []
        a = inp.node_poses.get(b.source_id)
        z = inp.node_poses.get(b.target_id)
        if a and z:
            pts.append((b.source_id, a))
            for wp in inp.waypoints.get(b.id, []):
                pts.append((wp.id, wp.pose))
            pts.append((b.target_id, z))
            # build segments along pts
            segs = []
            total = 0.0
            for (ida, pa), (idb, pb) in zip(pts, pts[1:]):
                L = _seg_len(pa, pb)
                segs.append({"from": ida, "to": idb, "env": inp.default_env, "len_m": round(L, 3)})
                total += L
            bundle_lengths[b.id] = round(total, 3)
            routes.append({"bundle_id": b.id, "segments": segs})
        else:
            # Fallback: one synthetic segment with default length
            L = inp.default_length_m
            bundle_lengths[b.id] = L
            routes.append(
                {
                    "bundle_id": b.id,
                    "segments": [
                        {"from": b.source_id, "to": b.target_id, "env": inp.default_env, "len_m": L}
                    ],
                }
            )

    ops: List[PatchOp] = []
    # Persist routes under meta.physical.routes
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:routes",
            op="set_meta",
            value={"path": "physical.routes", "merge": True, "data": routes},
        )
    )
    # Update bundles with computed lengths if they exist in meta.physical.bundles
    for bid, L in bundle_lengths.items():
        ops.append(
            PatchOp(
                op_id=f"{inp.request_id}:meta:bundle_len:{bid}",
                op="set_meta",
                value={"path": f"physical.bundles.{bid}.length_m", "merge": True, "data": L},
            )
        )
    # Annotation
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:routes",
            op="add_edge",
            value={
                "id": f"ann:routes:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "plan_routes",
                    "bundles": len(inp.bundles),
                    "routed": len(routes),
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["plan_routes", "PlanRoutesInput", "BundleRef", "Pose", "Waypoint"]

