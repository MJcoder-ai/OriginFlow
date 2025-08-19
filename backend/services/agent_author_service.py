from __future__ import annotations

import logging
from typing import Optional
from pydantic import ValidationError

from backend.schemas.agent_spec import (
    AgentAssistSynthesizeRequest,
    AgentAssistRefineRequest,
    AgentSpecModel,
)
from backend.services.ai_clients import get_openai_client  # existing helper

logger = logging.getLogger(__name__)


SYSTEM_SYNTHESIZE = """You are an expert Agent designer. Given an 'idea', produce a JSON AgentSpecModel with:
- name (snake_case), display_name, description, domain (if known)
- patterns: include diverse keyword/regex triggers
- llm_tools: suggest relevant tool names (leave as strings)
- capabilities: list core actions with brief description
- config: reasonable defaults
Return ONLY valid JSON for the schema; no prose."""

SYSTEM_REFINE = """Refine the provided AgentSpecModel JSON according to the critique.
Preserve name unless change is explicitly requested. Return ONLY valid JSON."""


class AgentAuthorService:
    """
    Leverages the configured OpenAI client to draft/refine AgentSpecModel JSON.
    """

    @staticmethod
    async def synthesize(req: AgentAssistSynthesizeRequest) -> AgentSpecModel:
        client = get_openai_client()
        prompt = f"Idea:\n{req.idea}\nDomain: {req.target_domain or 'unknown'}\nTarget actions: {', '.join(req.target_actions or [])}"
        # We keep model selection consistent with your existing usage
        chat = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_SYNTHESIZE},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = chat.choices[0].message.content or "{}"
        try:
            import json
            data = json.loads(text)
            return AgentSpecModel.model_validate(data)
        except Exception as e:
            logger.exception("Failed to parse or validate synthesized spec: %s", e)
            raise

    @staticmethod
    async def refine(req: AgentAssistRefineRequest) -> AgentSpecModel:
        client = get_openai_client()
        current = req.current_spec.model_dump()
        prompt = f"Current Spec JSON:\n```json\n{current}\n```\nCritique:\n{req.critique}"
        chat = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_REFINE},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = chat.choices[0].message.content or "{}"
        try:
            import json
            data = json.loads(text)
            return AgentSpecModel.model_validate(data)
        except ValidationError:
            logger.exception("Refined spec failed validation.")
            raise

