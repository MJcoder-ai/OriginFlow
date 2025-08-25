from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def add_disconnects(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Add required DC/AC disconnects per jurisdiction with proper specifications."""
    layer = args.get("layer", "single-line")
    
    ds = await store.get_meta(session_id)
    equip = ds.get("design_state", {}).get("equip", {})
    inv_kw = float(equip.get("inverter", {}).get("ac_kw", 3.8))
    
    patch = PatchBuilder(f"{session_id}:add_disconnects")
    
    # DC combiner disconnect (NEC 690.15)
    dc_disconnect_attrs = {
        "type": "dc_combiner_disconnect", 
        "rating_A": 30,  # Typical for residential strings
        "voltage_rating_V": 600,
        "part_number": "SQD-DU321",
        "name": "Square D DU 30A 3P 600V DC Disconnect",
        "manufacturer": "Square D",
        "application": "DC combiner disconnect per NEC 690.15",
        "location": "accessible_rooftop"
    }
    patch.add_node(kind="disconnect", attrs=dc_disconnect_attrs, layer=layer,
                   node_id="dc_combiner_disconnect")
    
    # AC production meter disconnect (NEC 690.64)
    ac_disconnect_attrs = {
        "type": "ac_production_meter_disconnect",
        "rating_A": int(inv_kw * 1.25 * 1000 / 240),  # 125% of inverter rating
        "voltage_rating_V": 240,
        "part_number": f"SQD-QO{int(inv_kw * 1.25 * 1000 / 240)}",
        "name": f"Square D QO {int(inv_kw * 1.25 * 1000 / 240)}A Production Meter Disconnect",
        "manufacturer": "Square D", 
        "application": "AC production meter disconnect per NEC 690.64",
        "location": "next_to_main_panel"
    }
    patch.add_node(kind="disconnect", attrs=ac_disconnect_attrs, layer=layer,
                   node_id="ac_production_disconnect")
    
    return patch.to_dict(), card_from_text("Added required disconnects: DC combiner + AC production meter."), []