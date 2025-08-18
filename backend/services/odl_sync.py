from __future__ import annotations
"""Utilities to keep ODL representations in sync with design snapshots."""

from backend.services.odl_compiler import snapshot_to_odl


async def rebuild_odl_for_session(session_id: str) -> None:
    """Rebuild the ODL representation for ``session_id``.

    This is currently a lightweight stub that tries to fetch the latest snapshot
    (if a snapshot provider is available) and compiles it to ODL text. The text
    is computed but not persisted; integrating persistence is left for the
    production system.
    """

    try:  # optional dependency used in API routes
        from backend.services.snapshot_provider import get_current_snapshot  # type: ignore
    except Exception:  # pragma: no cover - optional provider
        return

    snapshot = await get_current_snapshot(session_id=session_id)
    if snapshot is None:
        return
    # Generate ODL text to ensure snapshot is valid; result discarded for now
    snapshot_to_odl(snapshot)


__all__ = ["rebuild_odl_for_session"]

