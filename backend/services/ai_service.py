# backend/services/ai_service.py
"""Orchestrator for AI agents and validation."""
from __future__ import annotations

from typing import List

from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from openai import OpenAIError

from backend.agents.router_agent import RouterAgent
from backend.utils.openai_helpers import map_openai_error
from backend.schemas.ai import AiAction, AiActionType
from backend.schemas.component import ComponentCreate
from backend.schemas.link import LinkCreate

limiter = Limiter(key_func=get_remote_address)


class AiOrchestrator:
    """High-level orchestrator coordinating agent calls."""

    router_agent = RouterAgent()

    async def process(self, command: str) -> List[AiAction]:
        """Run the router agent and validate the returned actions."""

        try:
            raw = await self.router_agent.handle(command)
        except (OpenAIError, ValueError) as err:
            raise map_openai_error(err)
        validated: List[AiAction] = []
        for action in raw:
            try:
                obj = AiAction.model_validate(action)
            except Exception as exc:  # pragma: no cover - defensive
                raise HTTPException(422, f"Invalid action schema: {exc}") from exc
            if obj.action == AiActionType.add_component:
                ComponentCreate(**obj.payload)
            elif obj.action == AiActionType.add_link:
                LinkCreate(**obj.payload)
            validated.append(obj)
        return validated

    @classmethod
    def dep(cls) -> "AiOrchestrator":
        """Return orchestrator instance for FastAPI dependency injection."""

        return cls()
