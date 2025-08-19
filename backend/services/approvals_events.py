from __future__ import annotations
import asyncio
import time
from typing import Dict, Set

class _TenantBus:
    def __init__(self) -> None:
        self.subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1024)
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self.subscribers.discard(q)

    def publish(self, event: dict) -> None:
        dead = []
        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                except Exception:
                    pass
                try:
                    q.put_nowait(event)
                except Exception:
                    dead.append(q)
            except Exception:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)

class ApprovalsEventBus:
    """Minimal in-process event bus for approvals live updates.
    Tenants are isolated by tenant_id.
    """
    _tenants: Dict[str, _TenantBus] = {}

    @classmethod
    def _get(cls, tenant_id: str) -> _TenantBus:
        tb = cls._tenants.get(tenant_id)
        if not tb:
            tb = _TenantBus()
            cls._tenants[tenant_id] = tb
        return tb

    @classmethod
    def subscribe(cls, tenant_id: str) -> asyncio.Queue:
        return cls._get(tenant_id).subscribe()

    @classmethod
    def unsubscribe(cls, tenant_id: str, q: asyncio.Queue) -> None:
        cls._get(tenant_id).unsubscribe(q)

    @classmethod
    def publish_created(cls, tenant_id: str, item: dict) -> None:
        cls._get(tenant_id).publish({"type": "pending.created", "item": item})

    @classmethod
    def publish_updated(cls, tenant_id: str, item: dict) -> None:
        cls._get(tenant_id).publish({"type": "pending.updated", "item": item})

    @classmethod
    def publish_approved(cls, tenant_id: str, item: dict) -> None:
        cls._get(tenant_id).publish({"type": "pending.approved", "item": item})

    @classmethod
    def publish_rejected(cls, tenant_id: str, item: dict) -> None:
        cls._get(tenant_id).publish({"type": "pending.rejected", "item": item})

    @classmethod
    def publish_applied(cls, tenant_id: str, item: dict) -> None:
        cls._get(tenant_id).publish({"type": "pending.applied", "item": item})

    @classmethod
    def heartbeat(cls, tenant_id: str) -> None:
        cls._get(tenant_id).publish({"type": "heartbeat", "ts": int(time.time())})
