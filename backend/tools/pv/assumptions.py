from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.tools.patch_builder import PatchBuilder

async def set_assumptions(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Set design assumptions (environment, targets, service)."""
    patch = PatchBuilder(f"{session_id}:assumptions")
    patch.set_meta(path="design_state", data=args, merge=True)
    return patch.to_dict(), card_from_text("Design assumptions updated."), []