from __future__ import annotations
from contextvars import ContextVar
from typing import Optional

_rid: ContextVar[Optional[str]] = ContextVar("_request_id", default=None)

def set_request_id(request_id: Optional[str]) -> None:
    _rid.set(request_id)

def get_request_id() -> Optional[str]:
    return _rid.get()
