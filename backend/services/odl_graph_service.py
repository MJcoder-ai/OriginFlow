"""
ODL graph service: persist and manage per-session graphs.

This module replaces the previous in-memory `_GRAPHS` dict with a simple
SQLite-backed store. Each session’s graph is serialized to JSON and
persisted alongside a monotonic `version` integer for optimistic concurrency.
Graphs are loaded, patched, and saved through the helpers below.

Schema:
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        graph_json TEXT NOT NULL,
        version INTEGER NOT NULL
    );
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx

# SQLite database file used to persist graphs.  A `data` directory under
# backend/services will be created automatically.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "odl_sessions.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_db() -> None:
    """Initialise the sessions table if it does not exist."""
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


def create_graph(session_id: str) -> nx.DiGraph:
    """Create a new graph for `session_id` if none exists."""
    _init_db()
    g = get_graph(session_id)
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


def get_graph(session_id: str) -> Optional[nx.DiGraph]:
    """Load and return the graph for `session_id`, or None if it does not exist."""
    _init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT graph_json FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return _deserialize_graph(row[0])


def save_graph(session_id: str, g: nx.DiGraph) -> None:
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


def apply_patch(session_id: str, patch: Dict[str, List]) -> Tuple[bool, str]:
    """Apply an add/remove patch to the given session’s graph."""
    g = get_graph(session_id)
    if not g:
        return False, f"Session {session_id} does not exist"

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

    g.graph["version"] = g.graph.get("version", 0) + 1
    save_graph(session_id, g)
    return True, ""
