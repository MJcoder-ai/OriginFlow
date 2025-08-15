"""Simple saga-style workflow engine for coordinating graph modifications.

The workflow engine executes a sequence of steps, each producing an
``ODLGraphPatch``.  Patches are applied to the session's graph using the
existing :mod:`backend.services.odl_graph_service`.  If any step fails, the
engine automatically applies compensating patches in reverse order to keep the
design graph consistent.

This module provides a lightweight foundation that can later be replaced or
extended with a full-fledged workflow orchestrator such as Temporal.io.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, List, Optional

from backend.services.odl_graph_service import ODLGraphPatch, odl_graph_service
from backend.utils.errors import (
    DesignConflictError,
    InvalidPatchError,
    SessionNotFoundError,
)


@dataclass
class SagaStep:
    """Single step in a saga workflow.

    Each step exposes a ``forward`` coroutine returning an
    :class:`~backend.services.odl_graph_service.ODLGraphPatch`.  An optional
    ``compensate`` coroutine can be supplied to override the automatic reverse
    behaviour.
    """

    name: str
    forward: Callable[[str], Awaitable[ODLGraphPatch]]
    compensate: Optional[Callable[[str, ODLGraphPatch], Awaitable[None]]] = None


class WorkflowEngine:
    """Execute ordered saga steps with automatic compensation on failure."""

    async def run(self, session_id: str, steps: List[SagaStep]) -> None:
        """Run all saga ``steps`` sequentially for ``session_id``.

        If any step raises an exception, previously applied patches are rolled
        back in reverse order before the original exception is re-raised.
        """

        applied: List[tuple[SagaStep, ODLGraphPatch]] = []
        for step in steps:
            try:
                patch = await step.forward(session_id)
                # Apply patch to graph, converting to primitive dict structure.
                await odl_graph_service.apply_patch(session_id, patch.model_dump())
                applied.append((step, patch))
            except (InvalidPatchError, DesignConflictError, SessionNotFoundError):
                await self._compensate(session_id, applied)
                raise
            except Exception:
                await self._compensate(session_id, applied)
                raise

    async def _compensate(
        self, session_id: str, applied: List[tuple[SagaStep, ODLGraphPatch]]
    ) -> None:
        """Run compensation for previously applied steps."""

        for step, patch in reversed(applied):
            try:
                if step.compensate:
                    await step.compensate(session_id, patch)
                else:
                    reverse_patch = patch.reverse()
                    await odl_graph_service.apply_patch(
                        session_id, reverse_patch.model_dump()
                    )
            except Exception:  # pragma: no cover - best-effort compensation
                import logging

                logging.getLogger("originflow.workflow").exception(
                    "Failed to compensate step %s during saga rollback", step.name
                )

