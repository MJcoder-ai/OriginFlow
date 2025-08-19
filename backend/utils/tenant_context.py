from __future__ import annotations
from contextvars import ContextVar
from typing import Optional

_tenant_id: ContextVar[str] = ContextVar("_tenant_id", default="default")

def set_tenant_id(tenant_id: Optional[str]) -> None:
    _tenant_id.set(tenant_id or "default")

def get_tenant_id() -> str:
    return _tenant_id.get()
