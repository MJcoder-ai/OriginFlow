from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text

async def run(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Explain the design for homeowner and engineer views."""
    ds = await store.get_meta(session_id)
    stringing = ds.get("design_state", {}).get("stringing", {})
    equip = ds.get("design_state", {}).get("equip", {})
    
    explanation = f"""Design Summary:
- {stringing.get('modules_total', 8)} solar modules in {stringing.get('strings', 1)} strings
- String inverter: {equip.get('inverter', {}).get('ac_kw', 3.8)} kW AC
- MLPE mode: {equip.get('mlpe', 'none')}
- Estimated annual production: {equip.get('inverter', {}).get('ac_kw', 3.8) * 1400:.0f} kWh"""
    
    card = {
        "title": "Design Explanation",
        "body": explanation
    }
    return {}, card, []