from __future__ import annotations
from typing import Any, Dict, Tuple
from backend.utils.adpf import card_from_text
from backend.odl.schemas import ODLPatch

async def set_assumptions(*, store, session_id: str, args: Dict[str, Any]) -> Tuple[dict, dict, list[str]]:
    """Set design assumptions (environment, targets, service)."""
    patch = ODLPatch()
    patch.set_meta(path="design_state", data=args, merge=True)
    return patch.to_dict(), card_from_text("Design assumptions updated."), []