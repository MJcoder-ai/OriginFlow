"""API routes for managing design snapshots and versions."""

from fastapi import APIRouter, HTTPException

from backend.schemas.analysis import DesignSnapshot
from backend.services.snapshot_service import SnapshotService
from backend.services.metrics_service import metrics


router = APIRouter()
_service = SnapshotService()


@router.post(
    "/snapshots/{session_id}",
    response_model=DesignSnapshot,
    summary="Save a new snapshot",
    description="Store a new version of the design snapshot for the given session.",
)
async def save_snapshot(session_id: str, snapshot: DesignSnapshot) -> DesignSnapshot:
    """Create a new snapshot version for a session."""
    import time

    snapshot.session_id = session_id
    start = time.perf_counter()
    saved = await _service.save_snapshot(session_id, snapshot)
    duration = time.perf_counter() - start
    metrics.record_latency("save_snapshot", duration)
    metrics.increment_counter("snapshots_saved")
    return saved


@router.get(
    "/snapshots/{session_id}",
    response_model=list[DesignSnapshot],
    summary="List snapshots",
    description="Retrieve all snapshots associated with a session.",
)
async def list_snapshots(session_id: str) -> list[DesignSnapshot]:
    """Return all snapshots for a session."""
    snapshots = await _service.list_snapshots(session_id)
    metrics.increment_counter("snapshots_listed")
    return snapshots


@router.get(
    "/snapshots/{session_id}/{version}",
    response_model=DesignSnapshot,
    summary="Get snapshot by version",
    description="Retrieve a specific snapshot by its version number.",
)
async def get_snapshot(session_id: str, version: int) -> DesignSnapshot:
    """Retrieve a single snapshot version."""
    snapshot = await _service.get_snapshot(session_id, version)
    metrics.increment_counter("snapshots_retrieved")
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot


@router.get(
    "/snapshots/{session_id}/{v1}/diff/{v2}",
    summary="Diff two snapshots",
    description="Compute a simple diff between two snapshot versions. Returns added and removed nodes/links.",
)
async def diff_snapshots(session_id: str, v1: int, v2: int) -> dict[str, list[str]]:
    """Compute differences between two snapshots of the same session."""
    import time

    old = await _service.get_snapshot(session_id, v1)
    new = await _service.get_snapshot(session_id, v2)
    if not old or not new:
        raise HTTPException(status_code=404, detail="One or both snapshots not found")
    start = time.perf_counter()
    diff = await _service.diff_snapshots(old, new)
    duration = time.perf_counter() - start
    metrics.record_latency("snapshot_diff", duration)
    metrics.increment_counter("snapshots_diffs")
    return diff
