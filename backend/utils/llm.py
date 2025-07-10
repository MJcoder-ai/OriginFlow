from __future__ import annotations

from typing import Any, Dict, List


def safe_tool_calls(response) -> List[Dict[str, Any]]:
    """Return tool_calls array or raise ValueError for empty response."""

    calls = response.choices[0].message.tool_calls or []
    if not calls:
        raise ValueError("LLM returned no structured tool calls")
    return calls
