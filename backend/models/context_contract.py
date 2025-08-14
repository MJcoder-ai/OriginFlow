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

from typing import Any, Dict, List, Optional

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

    def update_metrics(
        self,
        *,
        accept_rate: Optional[float] = None,
        avg_confidence: Optional[float] = None,
        iterations: Optional[int] = None,
        convergence: Optional[str] = None,
        **extra: Any,
    ) -> None:
        """Update tracking metrics for the session.

        Only provided values are written to the metrics dictionary.
        Additional keyword arguments are merged verbatim which allows
        templates to record custom statistics.
        """
        if accept_rate is not None:
            self.metrics["accept_rate"] = accept_rate
        if avg_confidence is not None:
            self.metrics["avg_confidence"] = avg_confidence
        if iterations is not None:
            self.metrics["iterations"] = iterations
        if convergence is not None:
            self.metrics["convergence"] = convergence
        if extra:
            self.metrics.update(extra)

    # Persistence helpers
    def save(self, session_id: str, *, path: str = "storage/contracts") -> None:
        """Persist the contract to a JSON file.

        Serialises the contract to JSON using Pydantic's ``model_dump``
        and stores it under ``path/{session_id}.json``.  The directory
        is created if it does not exist.  Useful for resuming sessions.
        """
        import os
        import json

        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, f"{session_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json_data = self.model_dump()
            json.dump(json_data, f)

    @classmethod
    def load(
        cls,
        session_id: str,
        *,
        path: str = "storage/contracts",
    ) -> "ContextContract":
        """Load a context contract from a JSON file.

        Returns a new contract if the file is missing.  Does not handle
        concurrent modifications.
        """
        import os
        import json

        file_path = os.path.join(path, f"{session_id}.json")
        if not os.path.exists(file_path):
            return cls(inputs={})
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
