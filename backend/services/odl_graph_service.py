"""In-memory ODL graph service.

This module provides a simple in-memory store for OriginFlow
Design Language (ODL) graphs and helper functions to operate on
these graphs. It uses networkx to maintain the graph structure
and keeps a per-session mapping of graphs so that multiple users
can work independently. In a production environment this
service should be replaced with a database-backed implementation
to ensure persistence and concurrent access.

The main responsibilities of this service are:

* Creating and retrieving graphs for a given session ID.
* Converting between the internal networkx representation and
  Pydantic models defined in ``backend/schemas/odl.py``.
* Applying patches to graphs and computing diffs.

This service does not contain any domain logic; domain agents
should use these functions to read and write graphs. See
``backend/agents/odl_domain_agents.py`` for agent examples.
"""
from __future__ import annotations
from typing import Dict
import networkx as nx
from backend.schemas.odl import (
    ODLNode,
    ODLEdge,
    ODLGraph,
    GraphPatch,
    GraphDiff,
)

_GRAPHS: Dict[str, nx.DiGraph] = {}

def create_graph(session_id):
    """Create a new empty graph for the given session.
    If a graph already exists for the session it will be
    overwritten.
    """
    _GRAPHS[session_id] = nx.DiGraph()

def get_graph(session_id):
    """Retrieve the networkx graph for a session."""
    return _GRAPHS[session_id]

def serialize_graph(graph):
    """Convert a networkx graph into an ODLGraph model."""
    nodes = []
    for node_id in graph.nodes:
        n_type = graph.nodes[node_id].get("type", "unknown")
        n_data = dict(graph.nodes[node_id].get("data", {}))
        nodes.append(ODLNode(id=node_id, type=n_type, data=n_data))
    edges = []
    for (src, tgt) in graph.edges:
        e_type = graph[src][tgt].get("type", "related")
        e_data = dict(graph[src][tgt].get("data", {}))
        edges.append(ODLEdge(source=src, target=tgt, type=e_type, data=e_data))
    return ODLGraph(nodes=nodes, edges=edges)

def apply_patch(session_id, patch):
    """Apply a graph patch to the graph of a session and return a diff."""
    g = get_graph(session_id)
    added_nodes = []
    removed_nodes = []
    added_edges = []
    removed_edges = []
    if patch.add_nodes:
        for node in patch.add_nodes:
            if node.id not in g:
                g.add_node(node.id, type=node.type, data=node.data)
                added_nodes.append(node.id)
    if patch.remove_node_ids:
        for node_id in patch.remove_node_ids:
            if g.has_node(node_id):
                g.remove_node(node_id)
                removed_nodes.append(node_id)
    if patch.add_edges:
        for edge in patch.add_edges:
            if not g.has_edge(edge.source, edge.target):
                if not g.has_node(edge.source):
                    g.add_node(edge.source, type="unknown", data={})
                if not g.has_node(edge.target):
                    g.add_node(edge.target, type="unknown", data={})
                g.add_edge(edge.source, edge.target, type=edge.type, data=edge.data)
                added_edges.append({"source": edge.source, "target": edge.target})
    if patch.remove_edges:
        for edge_spec in patch.remove_edges:
            src = edge_spec.get("source")
            tgt = edge_spec.get("target")
            if src is not None and tgt is not None and g.has_edge(src, tgt):
                g.remove_edge(src, tgt)
                removed_edges.append({"source": src, "target": tgt})
    return GraphDiff(
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
    )

def init_session(session_id, base_graph=None):
    """Initialise a session with an optional base graph."""
    create_graph(session_id)
    if base_graph:
        g = get_graph(session_id)
        for node in base_graph.nodes:
            g.add_node(node.id, type=node.type, data=node.data)
        for edge in base_graph.edges:
            g.add_edge(edge.source, edge.target, type=edge.type, data=edge.data)

def diff_graphs(g_old, g_new):
    """Compute a diff between two ODLGraph snapshots."""
    old_nodes = {n.id for n in g_old.nodes}
    new_nodes = {n.id for n in g_new.nodes}
    old_edges = {(e.source, e.target) for e in g_old.edges}
    new_edges = {(e.source, e.target) for e in g_new.edges}
    added_nodes = list(new_nodes - old_nodes)
    removed_nodes = list(old_nodes - new_nodes)
    added_edges = [
        {"source": src, "target": tgt}
        for (src, tgt) in new_edges - old_edges
    ]
    removed_edges = [
        {"source": src, "target": tgt}
        for (src, tgt) in old_edges - new_edges
    ]
    return GraphDiff(
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
    )
