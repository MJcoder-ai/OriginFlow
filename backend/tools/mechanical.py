from __future__ import annotations
from typing import List, Dict
from math import ceil
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


# --- Inputs ---


class RoofPlane(BaseModel):
    id: str
    tilt_deg: float
    azimuth_deg: float
    width_m: float
    height_m: float
    setback_m: float = 0.45  # default fire/walkway setback


class ModuleDims(BaseModel):
    width_m: float = 1.134
    height_m: float = 1.722
    frame_gap_m: float = 0.02


class RailSpec(BaseModel):
    allowable_span_m: float = 1.52  # example allowable span at given loads
    rail_length_m: float = 4.2  # stock rail length


class WindSnow(BaseModel):
    wind_speed_mph: float = 110
    ground_snow_load_psf: float = 0


class LayoutRackingInput(ToolBase):
    roof: RoofPlane
    modules_count: int
    module_dims: ModuleDims = ModuleDims()
    rail_spec: RailSpec = RailSpec()
    loads: WindSnow = WindSnow()


class AttachmentSpacingInput(ToolBase):
    span_request_m: float
    rail_spec: RailSpec


# --- Helpers ---


def _grid_pack(roof: RoofPlane, dims: ModuleDims, n: int) -> Dict:
    usable_w = max(roof.width_m - 2 * roof.setback_m, 0)
    usable_h = max(roof.height_m - 2 * roof.setback_m, 0)
    pitch_w = dims.width_m + dims.frame_gap_m
    pitch_h = dims.height_m + dims.frame_gap_m
    max_cols = int(usable_w // pitch_w) if pitch_w > 0 else 0
    max_rows = int(usable_h // pitch_h) if pitch_h > 0 else 0
    capacity = max_rows * max_cols
    place = min(n, capacity)
    rows = min(max_rows, max(1, place // max(1, max_cols) + (1 if place % max_cols else 0)))
    cols = min(max_cols, max_cols if rows > 1 else min(place, max_cols))
    return {
        "rows": rows,
        "cols": cols,
        "capacity": capacity,
        "pitch_w": round(pitch_w, 3),
        "pitch_h": round(pitch_h, 3),
        "usable_w": round(usable_w, 3),
        "usable_h": round(usable_h, 3),
    }


# --- Tools ---


def layout_racking(inp: LayoutRackingInput):
    pack = _grid_pack(inp.roof, inp.module_dims, inp.modules_count)
    # Rails: assume landscape, two rails per row
    rail_runs = []
    for r in range(pack["rows"]):
        y = (
            inp.roof.setback_m
            + (r + 0.5) * inp.module_dims.height_m
            + r * inp.module_dims.frame_gap_m
        )
        rail_runs.append({"id": f"rail_top_{r+1}", "y_m": round(y - 0.25, 3)})
        rail_runs.append({"id": f"rail_bot_{r+1}", "y_m": round(y + 0.25, 3)})
    # Attachments: simple spacing along rails
    attachments = []
    span = min(inp.rail_spec.allowable_span_m, max(1.0, inp.roof.width_m / 4))
    per_rail = ceil(inp.roof.width_m / span) + 1
    total_atts = per_rail * len(rail_runs)
    for rail in rail_runs:
        x = inp.roof.setback_m
        for _ in range(per_rail):
            attachments.append(
                {"rail_id": rail["id"], "x_m": round(x, 3), "y_m": rail["y_m"]}
            )
            x += span
    mech = {
        "roof": inp.roof.model_dump(),
        "layout": {"rows": pack["rows"], "cols": pack["cols"]},
        "rails": rail_runs,
        "attachments": attachments,
        "notes": f"capacity={pack['capacity']}, usable_w={pack['usable_w']}m, usable_h={pack['usable_h']}m",
    }
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:mechanical:layout",
            op="set_meta",
            value={"path": "mechanical", "merge": True, "data": mech},
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:mechanical",
            op="add_edge",
            value={
                "id": f"ann:mechanical:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "layout_racking",
                    "summary": f"{len(rail_runs)} rails, {total_atts} attachments",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


def attachment_spacing(inp: AttachmentSpacingInput):
    span = inp.span_request_m
    ok = span <= inp.rail_spec.allowable_span_m
    finding = []
    if not ok:
        finding.append(
            {
                "code": "SPAN_EXCEEDED",
                "severity": "warn",
                "message": f"Requested span {span:.2f} m exceeds allowable {inp.rail_spec.allowable_span_m:.2f} m",
                "suggest": "Increase attachment density or choose heavier rail",
            }
        )
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:att_span",
            op="add_edge",
            value={
                "id": f"ann:att_span:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "attachment_spacing",
                    "result": {"findings": finding},
                    "span_ok": ok,
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = [
    "layout_racking",
    "attachment_spacing",
    "LayoutRackingInput",
    "AttachmentSpacingInput",
    "RoofPlane",
    "RailSpec",
    "ModuleDims",
    "WindSnow",
]

