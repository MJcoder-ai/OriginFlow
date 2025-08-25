from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def apply_stringing(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Apply stringing plan by creating DC links."""
    layer = args.get("layer", "single-line")
    ds = await store.get_meta(session_id)
    stringing = ds.get("design_state", {}).get("stringing", {})
    patch = PatchBuilder(f"{session_id}:apply_stringing")
    # Placeholder: would create actual DC links based on stringing plan
    patch.auto_link(layer=layer)
    return patch.to_dict(), card_from_text(f"Applied stringing: {stringing.get('strings',0)} strings."), []