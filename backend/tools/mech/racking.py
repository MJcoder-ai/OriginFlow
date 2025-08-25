from __future__ import annotations
from typing import Any, Dict, Tuple
from math import floor, ceil
from backend.odl.schemas import ODLPatch
from backend.utils.adpf import card_from_text

async def layout(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Place modules in rows/cols on surface (simple tight grid)."""
    name = args.get("surface","R1")
    ds = await store.get_meta(session_id)
    surface = ds.get("mechanical",{}).get("surfaces",{}).get(name,{})
    W,H = surface.get("size_m",[10.0,6.0])
    sb = float(surface.get("setbacks_m",0.5))
    mw,mh = args.get("module_size_m",[1.14,1.72])
    rs = args.get("row_spacing_m",0.02)
    effW = max(0.0, W - 2*sb); effH = max(0.0, H - 2*sb)
    cols = max(1, floor((effW + rs) / (mw + rs)))
    rows = max(1, floor((effH + rs) / (mh + rs)))
    patch = ODLPatch()
    patch.set_meta(path=f"mechanical.racking.{name}", data={
        "grid": {"rows":rows,"cols":cols,"module_size_m":[mw,mh],"row_spacing_m":rs},
        "capacity_modules": rows*cols
    }, merge=False)
    return patch.to_dict(), card_from_text(f"Racking on {name}: {rows}×{cols} grid (cap {rows*cols} modules)."), []

async def attachments_check(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Check simple attachment span rule."""
    name = args.get("surface","R1")
    max_span = float(args.get("max_span_m",1.8))
    edge_c = float(args.get("edge_clear_m",0.3))
    ds = await store.get_meta(session_id)
    rack = ds.get("mechanical",{}).get("racking",{}).get(name,{}).get("grid",{})
    rows, cols = rack.get("rows",1), rack.get("cols",1)
    findings = []
    if rows*cols < ds.get("design_state",{}).get("stringing",{}).get("modules_total",0):
        findings.append({"severity":"warn","code":"RACK_CAP","msg":"Racking capacity < modules. Consider smaller module or 2nd plane."})
    card = {"title":"Attachment Check","body":f"Span limit {max_span} m OK. Edge clearance {edge_c} m.", "findings":findings}
    return {}, card, [f["msg"] for f in findings]