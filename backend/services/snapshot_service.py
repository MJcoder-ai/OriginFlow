"""Snapshot management service.

This service provides in-memory storage and basic versioning for
DesignSnapshot objects. It assigns version numbers, stores a history of
snapshots per session, and computes simple diffs between snapshots.

In a production system, this service would interface with a persistent
database and implement efficient diffing algorithms. Here, it uses a
simple dictionary for storage and returns naive diffs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.schemas.analysis import CanvasLink, DesignSnapshot


@dataclass
class SnapshotVersion:
    """Internal representation of a snapshot version."""

    version: int
    snapshot: DesignSnapshot


class SnapshotService:
    """Service for storing and retrieving design snapshots with versioning."""

    def __init__(self) -> None:
        self._store: Dict[str, List[SnapshotVersion]] = {}

    async def save_snapshot(self, session_id: str, snapshot: DesignSnapshot) -> DesignSnapshot:
        """Save a snapshot and assign the next version number."""
        versions = self._store.setdefault(session_id, [])
        next_version = versions[-1].version + 1 if versions else 1
        snapshot.version = next_version
        snapshot.session_id = session_id
        versions.append(SnapshotVersion(next_version, snapshot))
        return snapshot

    async def list_snapshots(self, session_id: str) -> List[DesignSnapshot]:
        """Return all snapshots for a session in chronological order."""
        return [sv.snapshot for sv in self._store.get(session_id, [])]

    async def get_snapshot(self, session_id: str, version: int) -> Optional[DesignSnapshot]:
        """Retrieve a snapshot by version."""
        versions = self._store.get(session_id, [])
        for sv in versions:
            if sv.version == version:
                return sv.snapshot
        return None

    async def diff_snapshots(self, old: DesignSnapshot, new: DesignSnapshot) -> Dict[str, List[str]]:
        """Compute a simple diff between two snapshots."""

        def link_key(link: CanvasLink) -> str:
            return f"{link.source_id}->{link.target_id}"

        old_nodes = {node.id for node in old.components}
        new_nodes = {node.id for node in new.components}
        old_links = {link_key(link) for link in old.links}
        new_links = {link_key(link) for link in new.links}
        return {
            "added_nodes": sorted(new_nodes - old_nodes),
            "removed_nodes": sorted(old_nodes - new_nodes),
            "added_links": sorted(new_links - old_links),
            "removed_links": sorted(old_links - new_links),
        }
