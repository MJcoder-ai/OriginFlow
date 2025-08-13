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
    if g is not None:
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
    
    # Handle edge updates
    for edge in patch.get("update_edges", []):
        src = edge.get("source")
        dst = edge.get("target")
        if src is None or dst is None:
            return False, "Edge source and target are required for update"
        if g.has_edge(src, dst):
            # Update edge attributes
            g.edges[src, dst].update(edge.get("data", {}))

    # bump version
    g.graph["version"] = g.graph.get("version", 0) + 1
    # persist updated graph
    await save_graph(session_id, g)
    # persist the patch as a separate record for diff/undo, but exclude the
    # version key from the stored patch to avoid confusion on replay
    stored_patch = {
        key: val
        for key, val in patch.items()
        if key in {"add_nodes", "add_edges", "remove_nodes", "remove_edges", "update_edges"}
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


def serialize_to_text(graph: nx.DiGraph) -> str:
    """Generate human-readable ODL text representation."""
    lines = []
    
    try:
        # Add header with metadata
        lines.append("# OriginFlow ODL Design")
        lines.append(f"# Version: {graph.graph.get('version', 1)}")
        lines.append(f"# Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
        lines.append("")
        
        # Add requirements section
        requirements = graph.graph.get("requirements", {})
        if requirements:
            lines.append("# Requirements")
            for key, value in requirements.items():
                if value is not None and not key.startswith("estimated_"):
                    if isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    else:
                        value_str = str(value)
                    lines.append(f"requirement {key} = {value_str}")
            lines.append("")
        
        # Add estimated values if available
        estimated_fields = {k: v for k, v in requirements.items() if k.startswith("estimated_") and v is not None}
        if estimated_fields:
            lines.append("# Estimated Values")
            for key, value in estimated_fields.items():
                lines.append(f"{key} = {value}")
            lines.append("")
        
        # Group nodes by layer and type
        nodes_by_layer = {}
        placeholder_nodes = []
        real_nodes = []
        
        for node_id, node_data in graph.nodes(data=True):
            layer = node_data.get("layer", "default")
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = []
            nodes_by_layer[layer].append((node_id, node_data))
            
            # Track placeholder vs real components
            if node_data.get("placeholder", False):
                placeholder_nodes.append((node_id, node_data))
            else:
                real_nodes.append((node_id, node_data))
        
        # Add summary statistics
        if placeholder_nodes or real_nodes:
            lines.append("# Component Summary")
            if real_nodes:
                lines.append(f"# Real components: {len(real_nodes)}")
            if placeholder_nodes:
                lines.append(f"# Placeholder components: {len(placeholder_nodes)}")
            lines.append("")
        
        # Add nodes by layer
        for layer, nodes in sorted(nodes_by_layer.items()):
            if layer != "default":
                lines.append(f"# Layer: {layer}")
            
            # Group nodes by type within layer
            nodes_by_type = {}
            for node_id, node_data in nodes:
                node_type = node_data.get("type", "unknown")
                if node_type not in nodes_by_type:
                    nodes_by_type[node_type] = []
                nodes_by_type[node_type].append((node_id, node_data))
            
            # Output nodes by type
            for node_type, type_nodes in sorted(nodes_by_type.items()):
                for node_id, node_data in type_nodes:
                    placeholder_flag = " [PLACEHOLDER]" if node_data.get("placeholder", False) else ""
                    
                    # Format node attributes (exclude system fields)
                    attrs = []
                    exclude_keys = {"type", "layer", "placeholder", "candidate_components", "replacement_history"}
                    
                    for key, value in node_data.items():
                        if key not in exclude_keys and not key.startswith("_"):
                            if isinstance(value, (int, float)):
                                if key in ["power", "capacity"]:
                                    attrs.append(f"{key}={value}W")
                                elif key in ["voltage", "voltage_rating"]:
                                    attrs.append(f"{key}={value}V")
                                elif key in ["price", "cost"]:
                                    attrs.append(f"{key}=${value}")
                                else:
                                    attrs.append(f"{key}={value}")
                            elif isinstance(value, str) and value:
                                attrs.append(f"{key}='{value}'")
                    
                    attr_str = f"({', '.join(attrs)})" if attrs else ""
                    lines.append(f"{node_type} {node_id}{attr_str}{placeholder_flag}")
                    
                    # Add candidate components for placeholders
                    candidates = node_data.get("candidate_components", [])
                    if candidates:
                        lines.append(f"  # Candidates: {', '.join(candidates[:3])}{'...' if len(candidates) > 3 else ''}")
            
            lines.append("")
        
        # Add edges/connections
        if graph.edges:
            lines.append("# Connections")
            
            # Group edges by type
            edges_by_type = {}
            for source, target, edge_data in graph.edges(data=True):
                edge_type = edge_data.get("type", "connected")
                if edge_type not in edges_by_type:
                    edges_by_type[edge_type] = []
                edges_by_type[edge_type].append((source, target, edge_data))
            
            # Output edges by type
            for edge_type, type_edges in sorted(edges_by_type.items()):
                if len(type_edges) > 1:
                    lines.append(f"  # {edge_type.title()} connections:")
                
                for source, target, edge_data in type_edges:
                    provisional_flag = " [PROVISIONAL]" if edge_data.get("provisional", False) else ""
                    
                    # Add connection attributes if any
                    attrs = []
                    exclude_keys = {"type", "provisional"}
                    for key, value in edge_data.items():
                        if key not in exclude_keys and not key.startswith("_"):
                            if isinstance(value, (int, float)):
                                attrs.append(f"{key}={value}")
                            elif isinstance(value, str) and value:
                                attrs.append(f"{key}='{value}'")
                    
                    attr_str = f" ({', '.join(attrs)})" if attrs else ""
                    lines.append(f"  {source} --{edge_type}--> {target}{attr_str}{provisional_flag}")
            
            lines.append("")
        
        # Add design analysis
        analysis = analyze_placeholder_status(graph)
        if analysis["total_placeholders"] > 0:
            lines.append("# Design Status")
            lines.append(f"# Completion: {analysis['completion_percentage']:.1f}%")
            lines.append(f"# Placeholders remaining: {analysis['total_placeholders']}")
            
            if analysis["blocking_issues"]:
                lines.append("# Blocking Issues:")
                for issue in analysis["blocking_issues"]:
                    lines.append(f"#   - {issue}")
            
            lines.append("")
    
    except Exception as e:
        # Fallback to basic representation if detailed parsing fails
        lines = [
            "# OriginFlow ODL Design",
            f"# Error generating detailed view: {str(e)}",
            "",
            "# Basic Node List:",
        ]
        
        for node_id, node_data in graph.nodes(data=True):
            node_type = node_data.get("type", "unknown")
            placeholder = " [PLACEHOLDER]" if node_data.get("placeholder", False) else ""
            lines.append(f"{node_type} {node_id}{placeholder}")
    
    return "\n".join(lines)


async def get_graph_with_text(session_id: str) -> Optional[Dict[str, Any]]:
    """Get graph data including text representation."""
    try:
        graph = await get_graph(session_id)
        if graph is None:
            return None
        
        # Convert to standard format
        nodes = [{"id": n, "data": dict(graph.nodes[n]), "layer": graph.nodes[n].get("layer")} for n in graph.nodes]
        edges = [{"source": u, "target": v, "data": dict(graph.edges[u, v])} for u, v in graph.edges]
        
        # Generate text representation
        text_representation = serialize_to_text(graph)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "graph_data": dict(graph.graph),
            "version": graph.graph.get("version", 1),
            "text": text_representation,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "last_updated": graph.graph.get("last_updated")
        }
    
    except Exception as e:
        print(f"Error getting graph with text for session {session_id}: {e}")
        return None


def analyze_placeholder_status(graph: nx.DiGraph) -> Dict[str, Any]:
    """Analyze placeholder component status in the graph."""
    try:
        # Count placeholders by type
        placeholders_by_type = {}
        total_placeholders = 0
        total_components = 0
        
        for node_id, node_data in graph.nodes(data=True):
            total_components += 1
            if node_data.get("placeholder", False):
                total_placeholders += 1
                node_type = node_data.get("type", "unknown")
                placeholders_by_type[node_type] = placeholders_by_type.get(node_type, 0) + 1
        
        # Calculate completion percentage
        completion_percentage = 0.0
        if total_components > 0:
            real_components = total_components - total_placeholders
            completion_percentage = (real_components / total_components) * 100
        
        # Identify blocking issues
        blocking_issues = []
        
        # Check for common issues
        requirements = graph.graph.get("requirements", {})
        missing_reqs = [k for k in ["target_power", "roof_area", "budget"] if not requirements.get(k)]
        if missing_reqs:
            blocking_issues.append(f"Missing requirements: {', '.join(missing_reqs)}")
        
        # Check for placeholder types without available replacements
        for placeholder_type in placeholders_by_type.keys():
            # This would be enhanced with actual component availability check
            if placeholder_type.startswith("generic_"):
                real_type = placeholder_type.replace("generic_", "")
                blocking_issues.append(f"Need {real_type} components in library")
        
        # Check for design connectivity issues
        isolated_nodes = [n for n in graph.nodes() if graph.degree(n) == 0 and total_components > 1]
        if isolated_nodes:
            blocking_issues.append(f"{len(isolated_nodes)} isolated components")
        
        return {
            "total_placeholders": total_placeholders,
            "placeholders_by_type": placeholders_by_type,
            "completion_percentage": completion_percentage,
            "blocking_issues": blocking_issues,
            "available_replacements": {},  # Would be populated by component service
        }
    
    except Exception as e:
        print(f"Error analyzing placeholder status: {e}")
        return {
            "total_placeholders": 0,
            "placeholders_by_type": {},
            "completion_percentage": 100.0,
            "blocking_issues": [f"Analysis error: {str(e)}"],
            "available_replacements": {},
        }


async def update_requirements(session_id: str, requirements: Dict[str, Any]) -> bool:
    """Update design requirements for a session."""
    try:
        graph = await get_graph(session_id)
        if graph is None:
            return False
        
        # Update requirements in graph
        current_requirements = graph.graph.get("requirements", {})
        current_requirements.update(requirements)
        
        # Add metadata
        from datetime import datetime
        current_requirements["last_updated"] = datetime.utcnow().isoformat()
        
        # Calculate completion status
        required_fields = ["target_power", "roof_area", "budget"]
        completed_fields = sum(1 for field in required_fields if current_requirements.get(field))
        current_requirements["completion_status"] = completed_fields / len(required_fields)
        
        graph.graph["requirements"] = current_requirements
        
        # Save updated graph
        await save_graph(session_id, graph)
        return True
    
    except Exception as e:
        print(f"Error updating requirements for session {session_id}: {e}")
        return False