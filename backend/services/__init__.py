"""
backend.services package

Keep this file import-light. Do not import orchestrators or agents here to
avoid circular imports during test discovery. Import submodules explicitly:

    from backend.services.orchestrator import PlannerOrchestrator
    from backend.services.vector_store import VectorStore
"""

__all__ = [
    # Intentionally empty to avoid heavy side effects on import.
]
