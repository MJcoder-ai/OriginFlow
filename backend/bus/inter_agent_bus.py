"""In-memory publish/subscribe bus for inter-agent communication."""
from __future__ import annotations

from typing import Any, Callable, Dict, List


class InterAgentBus:
    """A very small synchronous message bus.

    Agents can subscribe callbacks for named events.  Publishing an
    event will invoke the callbacks in the order they were registered.
    Exceptions in callbacks are caught and ignored to avoid breaking
    the orchestrator.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        self._subscribers.setdefault(event, []).append(callback)

    def publish(self, event: str, payload: Any) -> None:
        for callback in self._subscribers.get(event, []):
            try:
                callback(payload)
            except Exception:
                # Swallow exceptions to prevent cascading failures.
                continue
