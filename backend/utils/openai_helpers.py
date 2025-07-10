from __future__ import annotations

from fastapi import HTTPException
from openai import OpenAIError



def map_openai_error(err: Exception) -> HTTPException:
    """Convert OpenAI SDK errors to HTTP responses."""

    if isinstance(err, ValueError):
        return HTTPException(422, str(err))
    return HTTPException(status_code=502, detail=str(err))
