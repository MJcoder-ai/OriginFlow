# backend/api/deps.py
"""FastAPI dependencies for database access and AI orchestrator."""
from __future__ import annotations

from backend.database.session import get_session
from backend.services.ai_service import AiOrchestrator

__all__ = ["get_session", "AiOrchestrator"]
