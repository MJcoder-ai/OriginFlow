from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.odl.schemas import ODLPatch

async def compliance_check(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Enhanced compliance check with voltage drop enforcement."""
    layer = args.get("layer", "single-line")
    profile = args.get("profile", "NEC_2023")
    ds = await store.get_meta(session_id)
    targets = ds.get("design_state", {}).get("targets", {})
    service = ds.get("design_state", {}).get("service", {})
    protection = ds.get("electrical", {}).get("protection", {})
    conductors = ds.get("electrical", {}).get("conductors", {})
    
    findings = []
    fixes = []
    
    # 120% rule
    bus = float(service.get("bus_A", 200))
    main = float(service.get("main_A", 200))
    ac_breaker = float(protection.get("ac_breaker_A", 20))
    if main + ac_breaker > 1.2*bus:
        findings.append({"severity":"error","code":"BUS_120","msg":f"Main {main} A + PV {ac_breaker} A > 120% of bus {bus} A."})
        fixes.append({"task":"pv_size_protection","args":{"layer":"single-line"}})
    # v-drop
    ac_awg = conductors.get("ac_awg"); dc_awg = conductors.get("dc_awg")
    if not ac_awg or not dc_awg:
        findings.append({"severity":"warn","code":"VDROP_SIZE","msg":"Conductor sizes missing; run sizing."})
        fixes.append({"task":"pv_size_conductors","args":{"layer":"single-line"}})
    else:
        # Enforce stated vdrop targets
        ac_vd = conductors.get("calc",{}).get("ac",{}).get("vd_pct", 9.9)
        dc_vd = conductors.get("calc",{}).get("dc",{}).get("vd_pct", 9.9)
        if ac_vd > targets.get("ac_vdrop_pct",3.0):
            findings.append({"severity":"error","code":"VDROP_AC","msg":f"AC voltage drop {ac_vd:.2f}% exceeds target {targets.get('ac_vdrop_pct',3.0)}%."})
            fixes.append({"task":"pv_size_conductors","args":{"layer":"single-line","ac_len_m": max(1.0, ds.get('electrical',{}).get('conductors',{}).get('lengths_m',{}).get('ac',20.0)-1.5)}})
        if dc_vd > targets.get("dc_vdrop_pct",2.0):
            findings.append({"severity":"error","code":"VDROP_DC","msg":f"DC voltage drop {dc_vd:.2f}% exceeds target {targets.get('dc_vdrop_pct',2.0)}%."})
            fixes.append({"task":"pv_size_conductors","args":{"layer":"single-line","dc_len_m": max(1.0, ds.get('electrical',{}).get('conductors',{}).get('lengths_m',{}).get('dc',15.0)-1.5)}})

    severity = "error" if any(f["severity"]=="error" for f in findings) else "warn" if findings else "pass"
    card = {
        "title": f"Compliance Check ({profile})",
        "body": f"Status: {severity.upper()}" + (f" ({len(findings)} issues)" if findings else ""),
        "findings": findings,
        "fixes": fixes
    }
    return {}, card, [f["msg"] for f in findings if f["severity"]=="error"]