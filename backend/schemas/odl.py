"""ODL graph schemas for multi-layer engineering designs.

This module defines lightweight Pydantic models for representing
nodes, edges and patches within the OriginFlow Design Language
(ODL).  An ODL graph is modelled as a collection of typed nodes
connected by edges.  These models are purely structural and
contain no business logic; they are used by the API layer and
agents to serialise and deserialise graph data.  See the
``backend/services/odl_graph_service.py`` module for functions
that operate on these models.

Each node has a unique identifier, a ``type`` that describes
its role in the design (e.g. ``panel``, ``inverter``, ``roof``,
``network_device``) and an arbitrary ``data`` dictionary to
store domain-specific attributes.  Edges describe directed
relationships between nodes and may also include an arbitrary
``data`` dictionary for metadata (e.g. wire gauge or cable
length).

Patches are used to express incremental updates to a graph.
Adding or removing nodes and edges is done via the ``GraphPatch``
model.  A patch can be applied to an existing graph to produce
a new version, and the difference between two graphs can be
serialised as a patch.

These types are intentionally minimal to keep the public API
stable.  Additional properties can be added in future without
breaking existing clients.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ODLNode(BaseModel):
    """Represents a single node in an ODL graph.

    Attributes:
        id: Globally unique identifier for the node.
        type: A short string describing the node's role (e.g.
            ``"panel"``, ``"inverter"``, ``"roof"``).  Agents
            and the UI use this field to determine how to
            interpret the node.
        data: Arbitrary key/value pairs storing domain specific
            attributes (e.g. rated_power, manufacturer, position).
    """

    id: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ODLEdge(BaseModel):
    """Represents a directed edge between two nodes in an ODL graph.

    Attributes:
        source: The ID of the upstream node.
        target: The ID of the downstream node.
        type: A short string describing the relationship (e.g.
            ``"electrical"``, ``"mechanical"``, ``"network"``).
        data: Arbitrary key/value pairs for metadata (e.g. wire
            gauge, cable length, data rate).
    """

    source: str
    target: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ODLGraph(BaseModel):
    """A full ODL graph containing nodes and edges.

    This model is used to transmit complete graph states between
    the backend and the frontend or between services.  For
    partial updates, use :class:`GraphPatch`.
    """

    nodes: List[ODLNode]
    edges: List[ODLEdge]


class GraphPatch(BaseModel):
    """Describes incremental modifications to an ODL graph.

    Use this model to add or remove nodes and edges in a single
    operation.  All lists are optional; any omitted field is
    treated as an empty list.
    """

    add_nodes: List[ODLNode] | None = None
    remove_node_ids: List[str] | None = None
    add_edges: List[ODLEdge] | None = None
    remove_edges: List[Dict[str, str]] | None = None


class GraphDiff(BaseModel):
    """A diff summary between two ODL graphs.

    Contains lists of added and removed node/edge IDs to allow
    the frontend to display changes concisely.
    """

    added_nodes: List[str]
    removed_nodes: List[str]
    added_edges: List[Dict[str, str]]
    removed_edges: List[Dict[str, str]]
