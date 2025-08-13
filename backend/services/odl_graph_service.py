"""
ODL graph service: persist and manage per-session graphs and patches.

This module replaces the previous in-memory `_GRAPHS` dict with a simple
SQLite-backed store. Each session's graph is serialized to JSON and
persisted alongside a monotonic `version` integer for optimistic concurrency.
Incremental patches are also stored to support diffing and undo/redo.

Schema:
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        graph_json TEXT NOT NULL,
        version INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS patches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        version INTEGER NOT NULL,
        patch_json TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx

# SQLite database file used to persist graphs and patches.  A `data` directory
# under backend/services will be created automatically.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "odl_sessions.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_db() -> None:
    """Initialise the sessions and patches tables if they do not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                graph_json TEXT NOT NULL,
                version INTEGER NOT NULL
            )
            """
        )
        # New patches table stores each incremental patch applied to a session.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                patch_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
            """
        )
        conn.commit()


def _serialize_graph(g: nx.DiGraph) -> str:
    """Return a JSON representation of the given graph."""
    payload = {
        "graph": dict(g.graph),
        "nodes": [{"id": n, "data": dict(g.nodes[n])} for n in g.nodes],
        "edges": [
            {"source": u, "target": v, "data": dict(g.edges[u, v])}
            for u, v in g.edges
        ],
    }
    return json.dumps(payload)


def _deserialize_graph(data: str) -> nx.DiGraph:
    """Construct a NetworkX graph from its JSON representation."""
    payload = json.loads(data)
    g = nx.DiGraph()
    g.graph.update(payload.get("graph", {}))
    for node in payload.get("nodes", []):
        g.add_node(node["id"], **node.get("data", {}))
    for edge in payload.get("edges", []):
        g.add_edge(edge["source"], edge["target"], **edge.get("data", {}))
    return g


async def create_graph(session_id: str) -> nx.DiGraph:
    """Create a new graph for ``session_id`` if none exists."""
    _init_db()
    # ``get_graph`` is async, so we must await it here; the previous
    # implementation returned a coroutine and short‑circuited creation.
    g = await get_graph(session_id)
    if g:
        return g
    g = nx.DiGraph()
    g.graph["version"] = 0
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, graph_json, version) VALUES (?, ?, ?)",
            (session_id, _serialize_graph(g), 0),
        )
        conn.commit()
    return g


async def get_graph(session_id: str) -> Optional[nx.DiGraph]:
    """Load and return the graph for `session_id`, or ``None`` if it does not exist."""
    _init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT graph_json FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return _deserialize_graph(row[0])


async def save_graph(session_id: str, g: nx.DiGraph) -> None:
    """Persist the provided graph back to storage."""
    _init_db()
    version = g.graph.get("version", 0)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE sessions SET graph_json = ?, version = ? WHERE session_id = ?",
            (_serialize_graph(g), version, session_id),
        )
        conn.commit()


def delete_graph(session_id: str) -> None:
    """Remove a session from persistence."""
    _init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()


async def apply_patch(session_id: str, patch: Dict[str, List[Dict]]) -> Tuple[bool, str]:
    """
    Apply an add/remove patch to the given session’s graph.  This version
    checks optimistic concurrency by comparing the incoming version (if
    provided in the patch) against the persisted version.  After
    modifications, the updated graph and patch are persisted.
    """
    g = await get_graph(session_id)
    if g is None:
        return False, f"Session {session_id} does not exist"

    # Concurrency: if the caller includes 'version' in the patch, ensure it matches.
    incoming_version = patch.get("version")
    current_version = g.graph.get("version", 0)
    if incoming_version is not None and incoming_version != current_version:
        return False, f"Version conflict: client has {incoming_version}, server has {current_version}"

    for node_id in patch.get("remove_nodes", []):
        if g.has_node(node_id):
            g.remove_node(node_id)
    for edge in patch.get("remove_edges", []):
        u = edge.get("source")
        v = edge.get("target")
        if u is not None and v is not None and g.has_edge(u, v):
            g.remove_edge(u, v)
    for node in patch.get("add_nodes", []):
        node_id = node.get("id")
        if node_id is None:
            return False, "Node id is required"
        g.add_node(node_id, **node.get("data", {}))
    for edge in patch.get("add_edges", []):
        src = edge.get("source")
        dst = edge.get("target")
        if src is None or dst is None:
            return False, "Edge source and target are required"
        g.add_edge(src, dst, **edge.get("data", {}))

    # bump version
    g.graph["version"] = g.graph.get("version", 0) + 1
    # persist updated graph
    await save_graph(session_id, g)
    # persist the patch as a separate record for diff/undo, but exclude the
    # version key from the stored patch to avoid confusion on replay
    stored_patch = {
        key: val
        for key, val in patch.items()
        if key in {"add_nodes", "add_edges", "remove_nodes", "remove_edges"}
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO patches (session_id, version, patch_json) VALUES (?, ?, ?)",
            (
                session_id,
                g.graph["version"],
                json.dumps(stored_patch),
            ),
        )
        conn.commit()
    return True, ""


def get_patch_diff(session_id: str, from_version: int, to_version: int) -> Optional[List[Dict]]:
    """
    Return a list of patches needed to transform the graph from `from_version`
    to `to_version` (exclusive of from_version, inclusive of to_version).
    If no patches exist or the versions are invalid, return None.
    """
    _init_db()
    if from_version >= to_version:
        return []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT patch_json FROM patches
            WHERE session_id = ? AND version > ? AND version <= ?
            ORDER BY version ASC
            """,
            (session_id, from_version, to_version),
        )
        rows = cur.fetchall()
        if not rows:
            return None
        patches = [json.loads(row[0]) for row in rows]
        return patches


async def revert_to_version(session_id: str, target_version: int) -> bool:
    """
    Revert the graph to a previous version by reapplying patches up to the
    target version.  Returns False if the target version does not exist.
    """
    g = await get_graph(session_id)
    if g is None:
        return False
    current_version = g.graph.get("version", 0)
    if target_version > current_version:
        return False
    # Fetch patches to retain before mutating storage
    patches = get_patch_diff(session_id, 0, target_version)
    if patches is None:
        return False
    # Reset stored graph to version 0 and clear existing patches
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT graph_json FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cur.fetchone()
        if not row:
            return False
        base_graph = _deserialize_graph(row[0])
        base_graph.graph["version"] = 0
        conn.execute(
            "UPDATE sessions SET graph_json = ?, version = 0 WHERE session_id = ?",
            (_serialize_graph(base_graph), session_id),
        )
        conn.execute("DELETE FROM patches WHERE session_id = ?", (session_id,))
        conn.commit()
    # Reapply patches sequentially up to the target version
    for p in patches:
        await apply_patch(
            session_id,
            {k: p.get(k, []) for k in ["add_nodes", "add_edges", "remove_nodes", "remove_edges"]},
        )
    return True


def describe_graph(g: nx.DiGraph) -> str:
    """Return a compact description of the current session graph.
    
    This helper function supports dynamic planning by providing a summary that
    includes:
    - Component counts by type (panels, inverters, mounts, cables)
    - Graph version
    - Any warnings about missing components or issues
    
    Args:
        g: The NetworkX DiGraph to summarize
        
    Returns:
        A human-readable string describing the graph state
    """
    if not g:
        return "version=0, empty graph"
    
    # Count components by type
    counts = Counter(n_data.get("type", "unknown") for _, n_data in g.nodes(data=True))
    
    # Format counts as readable strings
    parts = [f"{v} {k}{'s' if v != 1 else ''}" for k, v in counts.items() if v > 0]
    
    # Get version and basic graph stats
    version = g.graph.get("version", 0)
    node_count = len(g.nodes)
    edge_count = len(g.edges)
    
    # Build summary components
    summary_parts = [f"version={version}"]
    
    if parts:
        summary_parts.append(", ".join(parts))
    else:
        summary_parts.append("no components")
    
    # Add basic graph statistics
    summary_parts.append(f"({node_count} nodes, {edge_count} edges)")
    
    # Check for warnings
    warnings = []
    
    # Check for common design issues
    panels = [n for n, d in g.nodes(data=True) if d.get("type") == "panel"]
    inverters = [n for n, d in g.nodes(data=True) if d.get("type") == "inverter"]
    mounts = [n for n, d in g.nodes(data=True) if d.get("type") == "mount"]
    
    if panels and not inverters:
        warnings.append("panels without inverters")
    elif inverters and not panels:
        warnings.append("inverters without panels")
    
    if panels and not mounts:
        warnings.append("panels without mounting")
    
    # Check for isolated components
    isolated = [n for n in g.nodes() if g.degree(n) == 0]
    if isolated:
        warnings.append(f"{len(isolated)} isolated component{'s' if len(isolated) != 1 else ''}")
    
    # Requirements status
    requirements = g.graph.get("requirements", {})
    missing_reqs = [k for k in ["target_power", "roof_area", "budget"] if not requirements.get(k)]
    if missing_reqs:
        warnings.append(f"missing requirements: {', '.join(missing_reqs)}")
    
    # Add warnings if any
    if warnings:
        summary_parts.append(f"warnings: {'; '.join(warnings)}")
    
    return " | ".join(summary_parts)

