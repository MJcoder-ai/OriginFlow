from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def size_protection(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Size OCPD/fusing per NEC 690 and add protection device nodes."""
    layer = args.get("layer", "single-line")
    ds = await store.get_meta(session_id)
    equip = ds.get("design_state", {}).get("equip", {})
    inv_kw = float(equip.get("inverter", {}).get("ac_kw", 3.8))
    
    # Calculate protection device ratings
    ac_breaker_A = int(inv_kw * 1000 / 240 * 1.25)  # 125% continuous for AC side
    dc_fuse_A = int(15.0 * 1.25)  # 125% of string Isc, assuming ~15A typical
    
    patch = PatchBuilder(f"{session_id}:size_protection")
    
    # Add AC overcurrent protection device (production breaker)
    ac_ocpd_attrs = {
        "type": "ac_breaker",
        "rating_A": ac_breaker_A,
        "voltage_rating_V": 240,
        "part_number": f"SQD-QO{ac_breaker_A}",
        "name": f"Square D QO {ac_breaker_A}A Circuit Breaker", 
        "manufacturer": "Square D",
        "application": "AC production disconnect"
    }
    patch.add_node(kind="protection", attrs=ac_ocpd_attrs, layer=layer,
                   node_id=f"ac_breaker_{ac_breaker_A}A")
    
    # Add DC fuse/breaker per string (combiners)
    stringing = ds.get("design_state", {}).get("stringing", {})
    strings_total = stringing.get("strings_total", 1)
    
    for i in range(strings_total):
        dc_ocpd_attrs = {
            "type": "dc_fuse",
            "rating_A": dc_fuse_A,
            "voltage_rating_V": 600,
            "part_number": f"LIT-KLDR{dc_fuse_A}",
            "name": f"Littelfuse KLDR {dc_fuse_A}A DC Fuse",
            "manufacturer": "Littelfuse", 
            "application": f"String {i+1} DC protection"
        }
        patch.add_node(kind="protection", attrs=dc_ocpd_attrs, layer=layer,
                       node_id=f"dc_fuse_str{i+1}_{dc_fuse_A}A")
    
    # Store calculations in metadata for other tools
    protection_meta = {
        "ac_breaker_A": ac_breaker_A,
        "dc_fuse_A": dc_fuse_A,
        "strings_total": strings_total
    }
    patch.set_meta(path="electrical.protection", data=protection_meta, merge=True)
    
    return patch.to_dict(), card_from_text(f"Added protection: {ac_breaker_A}A AC breaker + {strings_total} × {dc_fuse_A}A DC fuses."), []