from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.odl.schemas import ODLPatch
from backend.libraries.conductors import find_smallest_awg

async def size_conductors(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Size conductors using full AWG library with derates and voltage drop budgets."""
    layer = args.get("layer", "single-line")
    ds = await store.get_meta(session_id)
    targets = ds.get("design_state", {}).get("targets", {})
    dc_vdrop = float(args.get("dc_vdrop_pct", targets.get("dc_vdrop_pct", 2.0)))
    ac_vdrop = float(args.get("ac_vdrop_pct", targets.get("ac_vdrop_pct", 3.0)))
    equip = ds.get("design_state", {}).get("equip", {})
    inv_kw = float(equip.get("inverter", {}).get("ac_kw", 3.8))
    V_ll = 240.0
    I_ac = inv_kw*1000.0/V_ll
    # Use routes lengths if present, else fallback
    routes = ds.get("physical", {}).get("routes", [])
    L_ac = float(args.get("ac_len_m", next((r["segments"][0]["len_m"] for r in routes if r.get("bundle")=="AC_TRUNK"), 20.0)))
    L_dc_avg = sum(seg["len_m"] for r in routes if r.get("bundle","").startswith("STR_") for seg in r.get("segments",[])) \
               / max(1, len([r for r in routes if r.get("bundle","").startswith("STR_")]))
    L_dc = float(args.get("dc_len_m", L_dc_avg if L_dc_avg>0 else 15.0))
    # DC string current ~ Imp; use module meta
    I_dc = float(equip.get("module", {}).get("imp", 10.7))
    series = ds.get("design_state",{}).get("stringing",{}).get("series_per_string",8)
    V_string = float(equip.get("module",{}).get("vmp",41.5))*series
    # Assume 125% continuous
    ac = find_smallest_awg(required_ampacity=1.25*I_ac, max_vdrop_pct=ac_vdrop, length_m_oneway=L_ac,
                           current_A=I_ac, system_V=V_ll, temp_C=float(ds.get("design_state",{}).get("env",{}).get("tmax_C",45)),
                           ccc=int(args.get("ccc_ac",3)))
    dc = find_smallest_awg(required_ampacity=1.25*I_dc, max_vdrop_pct=dc_vdrop, length_m_oneway=L_dc,
                           current_A=I_dc, system_V=V_string, temp_C=float(ds.get("design_state",{}).get("env",{}).get("tmax_C",45)),
                           ccc=int(args.get("ccc_dc",2)))
    patch = ODLPatch()
    patch.set_meta(path="electrical.conductors", data={
        "ac_awg": ac["awg"], "dc_awg": dc["awg"],
        "calc": {"ac": ac, "dc": dc},
        "lengths_m": {"ac": L_ac, "dc": L_dc}}, merge=True)
    return patch.to_dict(), card_from_text(f"Sized conductors: AC {ac['awg']} AWG, DC {dc['awg']} AWG (vd AC {ac['vd_pct']}%, DC {dc['vd_pct']}%)."), []