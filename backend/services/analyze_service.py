from __future__ import annotations

from openai import OpenAIError

from backend.services.ai_service import AiOrchestrator
from backend.schemas.ai import AnalyzeCommandRequest, AiAction, AiActionType
from backend.schemas.component import ComponentCreate
from backend.schemas.link import LinkCreate
from backend.utils.openai_helpers import map_openai_error


class AnalyzeOrchestrator(AiOrchestrator):
    """Orchestrator aware of the design snapshot."""

    async def process(self, req: AnalyzeCommandRequest) -> list[AiAction]:
        prompt = self._serialize_snapshot(req)
        try:
            raw = await self.router_agent.handle(
                f"{prompt}\n\n{req.command}", req.snapshot.model_dump()
            )
        except (OpenAIError, ValueError) as err:  # pragma: no cover - network error
            raise map_openai_error(err)
        actions = self._validate_actions(raw)
        try:
            from backend.agents.learning_agent import LearningAgent  # type: ignore
            learner = LearningAgent()
            await learner.assign_confidence(
                actions,
                req.snapshot.model_dump(),
                [],
            )
        except Exception:
            pass
        return actions

    @staticmethod
    def _serialize_snapshot(req: AnalyzeCommandRequest) -> str:
        comp_lines = "\n".join(
            f'- Component: "{c.name}" (ID: {c.id}, Type: {c.type})'
            for c in req.snapshot.components
        )
        link_lines = "\n".join(
            f'- Link: {link.source_id} -> {link.target_id}' for link in req.snapshot.links
        )
        return (
            "The current design consists of:\n"
            f"{comp_lines or ' - none'}\n\n"
            "Existing connections:\n"
            f"{link_lines or ' - none'}"
        )

    @classmethod
    def dep(cls) -> "AnalyzeOrchestrator":
        return cls()

    def _validate_actions(self, raw: list[dict]) -> list[AiAction]:
        validated: list[AiAction] = []
        for action in raw:
            obj = AiAction.model_validate(action)
            if obj.action == AiActionType.add_component:
                ComponentCreate(**obj.payload)
            elif obj.action in (AiActionType.add_link, AiActionType.suggest_link):
                LinkCreate(**obj.payload)
            validated.append(obj)
        return validated
