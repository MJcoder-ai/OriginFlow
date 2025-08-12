import os
import os
import sys
from pathlib import Path

import pytest
from uuid import uuid4

# Ensure environment vars so settings load
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services import odl_graph_service  # noqa: E402
from backend.services.odl_graph_service import get_patch_diff, revert_to_version  # noqa: E402


@pytest.mark.asyncio
async def test_version_conflict_detection():
    session_id = f"conflict-{uuid4()}"
    await odl_graph_service.create_graph(session_id)

    patch = {"add_nodes": [{"id": "n1", "data": {}}], "version": 0}
    success, _ = await odl_graph_service.apply_patch(session_id, patch)
    assert success

    # Reapply with stale version
    patch2 = {"add_nodes": [{"id": "n2", "data": {}}], "version": 0}
    success, err = await odl_graph_service.apply_patch(session_id, patch2)
    assert not success
    assert "Version conflict" in err


@pytest.mark.asyncio
async def test_versions_diff_and_revert():
    session_id = f"diff-{uuid4()}"
    await odl_graph_service.create_graph(session_id)

    await odl_graph_service.apply_patch(
        session_id,
        {"add_nodes": [{"id": "a", "data": {}}], "version": 0},
    )
    await odl_graph_service.apply_patch(
        session_id,
        {"add_nodes": [{"id": "b", "data": {}}], "version": 1},
    )
    patches = get_patch_diff(session_id, 0, 2)
    assert patches is not None
    assert len(patches) == 2

    success = await revert_to_version(session_id, 1)
    assert success

    graph = await odl_graph_service.get_graph(session_id)
    assert graph.graph.get("version") == 1
