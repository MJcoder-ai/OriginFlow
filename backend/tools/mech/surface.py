from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.odl.schemas import ODLPatch
from backend.utils.adpf import card_from_text

async def run(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Create/update a rectangular surface."""
    name = args.get("name","R1")
    patch = ODLPatch()
    patch.set_meta(path=f"mechanical.surfaces.{name}", data={
        "tilt_deg": args.get("tilt_deg",25),
        "az_deg": args.get("az_deg",180),
        "size_m": args.get("size_m",[10.0,6.0]),
        "setbacks_m": args.get("setbacks_m",0.5)
    }, merge=False)
    return patch.to_dict(), card_from_text(f"Surface {name} defined."), []