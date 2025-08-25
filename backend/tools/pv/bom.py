from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def compute_bom(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Compute BOM from design state."""
    ds = await store.get_meta(session_id)
    stringing = ds.get("design_state", {}).get("stringing", {})
    conductors = ds.get("electrical", {}).get("conductors", {})
    modules_total = stringing.get("modules_total", 8)
    
    items = [
        {"item": "Solar Module", "qty": modules_total, "unit": "ea"},
        {"item": "String Inverter", "qty": 1, "unit": "ea"},
        {"item": f"DC Wire {conductors.get('dc_awg', '12')} AWG", "qty": 100, "unit": "ft"},
        {"item": f"AC Wire {conductors.get('ac_awg', '10')} AWG", "qty": 50, "unit": "ft"},
    ]
    
    patch = PatchBuilder(f"{session_id}:compute_bom")
    patch.set_meta(path="bom", data={"items": items}, merge=False)
    return patch.to_dict(), card_from_text(f"Computed BOM: {len(items)} line items."), []