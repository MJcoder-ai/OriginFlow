"""
Orchestrator context minimizer.

Fetch only the ODL information a tool needs (graph version and layer nodes).
Avoid dumping full chat history or entire graph when not necessary.
"""
from __future__ import annotations

from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.odl.store import ODLStore
from backend.odl.schemas import ODLNode, ODLGraph
from backend.odl.views import layer_view


async def load_graph_and_view_nodes(
    db: AsyncSession,
    session_id: str,
    layer: str,
) -> Tuple[ODLGraph, List[ODLNode]]:
    """Return current graph and a minimal list of nodes for the layer view."""
    store = ODLStore()
    g = await store.get_graph(db, session_id)
    if not g:
        raise KeyError("Session not found")
    v = layer_view(g, layer)
    return g, v.nodes
