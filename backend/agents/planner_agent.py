"""Planner agent for multi-layer engineering designs.

This module defines the ``PlannerAgent`` which decomposes free-form
natural language commands into ordered lists of high-level tasks and
suggested quick actions.  These tasks drive the plan–act loop used
throughout the OriginFlow platform.  The planner operates over the
OriginFlow Design Language (ODL) graph for a given session, but does
not directly edit the graph itself.  Instead, it yields ``PlanTask``
objects and ``QuickAction`` suggestions which downstream agents and
the orchestrator can interpret and execute.

The initial implementation is intentionally simple: it performs
lightweight keyword analysis on the command string and returns a
generic sequence of tasks when appropriate.  Future versions will
incorporate deep domain analysis, retrieval-augmented planning and
integration with the learning agent to adapt plans based on user
preferences and historical data.
"""

from __future__ import annotations

from typing import List, Tuple

from backend.schemas.ai import PlanTask, PlanTaskStatus, QuickAction
from backend.services.odl_graph_service import get_graph, serialize_graph


class PlannerAgent:
    """High-level planner for OriginFlow commands.

    The planner receives a natural language command and a session ID
    identifying the active ODL graph.  It returns a list of high-level
    ``PlanTask`` instances describing the steps necessary to fulfil
    the command, along with optional ``QuickAction`` suggestions.  It
    does not execute any domain logic itself; that responsibility is
    delegated to specialised domain agents.

    Parameters
    ----------
    session_id: str
        Identifier for the current design session.  Used to retrieve
        the ODL graph for context, though the default implementation
        currently does not inspect the graph contents.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    async def create_plan(self, command: str) -> Tuple[List[PlanTask], List[QuickAction]]:
        """Generate a high-level plan from a natural language command.

        This method performs a naive analysis of the command string
        and returns a static set of tasks when it detects common
        keywords such as ``"design"``.  It is meant to be replaced by
        a more sophisticated planner in future iterations.

        Parameters
        ----------
        command: str
            The user’s free-form instruction (e.g., "Design a 10 kW
            rooftop PV system").

        Returns
        -------
        (List[PlanTask], List[QuickAction])
            A tuple containing an ordered list of tasks and any quick
            actions.  If no plan is applicable the lists will be
            empty.
        """

        cmd = command.lower().strip()
        tasks: List[PlanTask] = []
        actions: List[QuickAction] = []

        # Example rule: if the command requests a design, propose
        # a three-step plan.  This is a placeholder; custom logic
        # should inspect the ODL graph via ``get_graph`` to derive
        # tasks appropriate for the current session.
        if "design" in cmd:
            tasks = [
                PlanTask(
                    id="gather_requirements",
                    title="Gather requirements",
                    description="Compile constraints, budgets and performance targets",
                    status=PlanTaskStatus.pending,
                ),
                PlanTask(
                    id="generate_design",
                    title="Generate preliminary design",
                    description="Select candidate components and estimate sizing",
                    status=PlanTaskStatus.pending,
                ),
                PlanTask(
                    id="refine_validate",
                    title="Refine and validate",
                    description="Optimise the design and verify against rules and standards",
                    status=PlanTaskStatus.pending,
                ),
            ]
            actions = [
                QuickAction(id="bom", label="Generate BOM", command="generate bill of materials"),
                QuickAction(id="analysis", label="Run analysis", command="validate my design"),
            ]

        return tasks, actions

    async def describe_graph(self) -> str:
        """Return a human-readable summary of the current ODL graph.

        This helper method illustrates how the planner might inspect
        graph contents to adjust its plan.  It serialises the graph
        into an ``ODLGraph`` model and summarises node and edge
        counts.  The current implementation returns a simple string.

        Returns
        -------
        str
            A summary of the graph nodes and edges.
        """
        g = get_graph(self.session_id)
        odl_graph = serialize_graph(g)
        num_nodes = len(odl_graph.nodes)
        num_edges = len(odl_graph.edges)
        return f"Graph contains {num_nodes} nodes and {num_edges} edges"
