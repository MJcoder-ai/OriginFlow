"""Context contract model for ADPF 2.1.

A *context contract* captures the evolving state of a design session,
including explicit inputs, assumptions, constraints, decisions and
metrics.  The contract is passed through every layer of the
`DynamicPromptOrchestratorV2` to ensure deterministic reasoning and
reproducibility.

This initial implementation provides a lightweight Pydantic model with
helper methods to append assumptions and decisions or update metrics.
Future sprints will extend this with persistence hooks to the ODL graph
service and richer validation.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ContextContract(BaseModel):
    """Data model describing session context and state."""

    inputs: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    def add_assumption(self, assumption: str) -> None:
        self.assumptions.append(assumption)

    def add_decision(self, decision: str) -> None:
        self.decisions.append(decision)

    def update_metrics(self, **new_metrics: Any) -> None:
        self.metrics.update(new_metrics)
