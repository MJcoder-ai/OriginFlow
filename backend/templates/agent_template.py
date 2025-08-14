"""Base classes for agent templates.

The Advanced Dynamic Prompting Framework (ADPF 2.1) introduces the
concept of **agent templates**: reusable classes that encapsulate the
reasoning protocol, cognitive mode and output schema for a specific
type of AI agent.  Templates provide a uniform interface (``run``)
for the orchestrator to execute complex tasks deterministically.

This module defines the abstract ``AgentTemplate`` base class from
which all concrete templates derive.  Derived classes should set
``name``, ``cognitive_mode``, ``protocol_steps`` and
``output_schema`` attributes and override ``run`` to implement the
five‑step reasoning scaffold: situation analysis, hypothesis
generation, synthesis/calculation, verification and reflection.

Sprint 1–2 only requires the scaffolding; concrete logic will be
implemented in later sprints.  See ``planner_template.py`` for an
example of a simple template implementation.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List

from backend.models.context_contract import ContextContract


class AgentTemplate(abc.ABC):
    """Abstract base class for all agent templates.

    Agent templates declare their cognitive mode, protocol steps and
    output schema up front.  The orchestrator can inspect these
    attributes to route tasks and validate results.  Derived classes
    implement the ``run`` coroutine to perform the actual reasoning.
    """

    #: Name of the template (e.g. "Planner", "PVDesign").
    name: str
    #: Cognitive mode (e.g. "plan", "design", "select").
    cognitive_mode: str
    #: Ordered steps in the reasoning protocol.
    protocol_steps: List[str]
    #: Schema describing the shape of the ``result`` field in the output.
    output_schema: Dict[str, Any]

    @abc.abstractmethod
    async def run(self, contract: ContextContract, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the template using the provided context and policy.

        Args:
            contract: The context contract for the current session.
            policy: The governance policy determined by the orchestrator.

        Returns:
            A dictionary conforming to the standard output envelope.  At a
            minimum this must contain a ``status`` key.  Concrete
            implementations may include ``result``, ``card``, ``metrics`` and
            ``errors`` fields.
        """
        raise NotImplementedError
