from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def size_protection(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Size OCPD/fusing per NEC 690."""
    layer = args.get("layer", "single-line")
    ds = await store.get_meta(session_id)
    equip = ds.get("design_state", {}).get("equip", {})
    inv_kw = float(equip.get("inverter", {}).get("ac_kw", 3.8))
    # Simple OCPD sizing
    ac_breaker_A = int(inv_kw * 1000 / 240 * 1.25)  # 125% continuous
    patch = PatchBuilder(f"{session_id}:size_protection")
    patch.set_meta(path="electrical.protection", data={"ac_breaker_A": ac_breaker_A}, merge=True)
    return patch.to_dict(), card_from_text(f"Sized AC breaker: {ac_breaker_A} A."), []