from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def add_disconnects(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Add required DC/AC disconnects per jurisdiction."""
    layer = args.get("layer", "single-line")
    patch = PatchBuilder(f"{session_id}:add_disconnects")
    # Placeholder: would add disconnect switches based on profile
    patch.add_node(kind="disconnect", attrs={"type": "dc_combiner"}, layer=layer)
    patch.add_node(kind="disconnect", attrs={"type": "ac_production_meter"}, layer=layer)
    return patch.to_dict(), card_from_text("Added required disconnects."), []