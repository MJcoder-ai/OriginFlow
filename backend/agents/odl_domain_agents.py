"""Domain agents for OriginFlow Design Language (ODL) graphs.

This module defines a collection of lightweight domain agents that
operate over ODL graphs.  Each agent encapsulates a particular
engineering domain (e.g. PV design, wiring, structural analysis,
communications, assemblies) and exposes a unified ``execute`` method
which accepts a task identifier and the current graph snapshot.  The
method returns a patch describing changes to apply to the graph and an
optional ``DesignCard`` summarising the suggestion for the user.

These classes provide scaffolding for future implementations.  They
contain only stub logic at present, returning empty patches and no
cards.  In a production environment each agent would perform
detailed calculations, consult domain rules and standards, and
populate rich cards with images, specifications and actionable
commands.
"""

from __future__ import annotations

from typing import Tuple, Optional

from backend.schemas.odl import ODLGraph, GraphPatch
from backend.schemas.ai import DesignCard, CardSpecItem, CardAction


class BaseDomainAgent:
    """Abstract base class for domain agents.

    Parameters
    ----------
    session_id: str
        The current design session identifier.  Used to fetch or
        persist data specific to the user’s project.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    async def execute(self, task_id: str, graph: ODLGraph) -> Tuple[GraphPatch, Optional[DesignCard]]:
        """Execute a task on the given graph.

        Subclasses must override this method.  It should analyse
        ``task_id`` and the ``graph`` to determine what changes are
        needed, then return a ``GraphPatch`` describing those changes
        along with an optional ``DesignCard`` providing a summary of
        the recommendation.

        Parameters
        ----------
        task_id: str
            Identifier of the task produced by the planner (e.g. "prelim").
        graph: ODLGraph
            The current state of the ODL graph for this session.

        Returns
        -------
        Tuple[GraphPatch, Optional[DesignCard]]
            A patch to apply to the graph and, if applicable, a card
            summarising the change for the user.  The default
            implementation returns an empty patch and ``None``.
        """
        # Default: no changes
        empty_patch = GraphPatch()
        return empty_patch, None


class PVDesignAgent(BaseDomainAgent):
    """Agent responsible for selecting PV components and sizing arrays.

    In future implementations this agent will analyse the required
    capacity, roof constraints and available components to propose
    appropriate PV modules and inverters.  It will produce a
    ``GraphPatch`` adding component nodes and electrical connections,
    and a ``DesignCard`` summarising the selection.
    """

    async def execute(self, task_id: str, graph: ODLGraph) -> Tuple[GraphPatch, Optional[DesignCard]]:
        # TODO: Implement PV sizing logic and card generation
        return await super().execute(task_id, graph)


class WiringAgent(BaseDomainAgent):
    """Agent responsible for wire sizing and electrical connections.

    This stub agent simply calls the base implementation.  A full
    version would calculate wire gauge, voltage drop and protective
    devices, then update the graph accordingly.
    """

    async def execute(self, task_id: str, graph: ODLGraph) -> Tuple[GraphPatch, Optional[DesignCard]]:
        # TODO: Implement wire sizing and connection logic
        return await super().execute(task_id, graph)


class StructuralAgent(BaseDomainAgent):
    """Agent responsible for structural and civil calculations.

    In a production system this agent would validate mounting points,
    structural loads and clearances.  It would interact with the
    structural layer of the graph to add or modify support elements.
    """

    async def execute(self, task_id: str, graph: ODLGraph) -> Tuple[GraphPatch, Optional[DesignCard]]:
        # TODO: Implement structural design logic
        return await super().execute(task_id, graph)


class NetworkAgent(BaseDomainAgent):
    """Agent responsible for network and monitoring design.

    This agent will eventually specify monitoring devices and
    communications links in the graph.  For now it returns no
    changes.
    """

    async def execute(self, task_id: str, graph: ODLGraph) -> Tuple[GraphPatch, Optional[DesignCard]]:
        # TODO: Implement network/monitoring design logic
        return await super().execute(task_id, graph)


class AssemblyAgent(BaseDomainAgent):
    """Agent responsible for grouping components into assemblies.

    Assemblies encapsulate subgraphs representing modules or kits.
    A complete implementation would identify logical groupings in the
    graph and update both the BOM and layout layers accordingly.
    """

    async def execute(self, task_id: str, graph: ODLGraph) -> Tuple[GraphPatch, Optional[DesignCard]]:
        # TODO: Implement assembly management logic
        return await super().execute(task_id, graph)
