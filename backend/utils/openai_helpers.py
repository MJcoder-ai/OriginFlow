from __future__ import annotations

from fastapi import HTTPException
from openai import OpenAIError


def map_openai_error(err: OpenAIError) -> HTTPException:
    """Convert OpenAI SDK errors to HTTP responses."""

    return HTTPException(status_code=502, detail=str(err))
