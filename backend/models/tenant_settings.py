from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Float, JSON, DateTime, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class TenantSettings(Base):
    """Per-tenant governance and feature configuration."""

    __tablename__ = "tenant_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    # ---- Structured policy fields (queryable & validated) ----
    auto_approve_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("1"))
    risk_threshold_default: Mapped[float] = mapped_column(Float, server_default=text("0.80"))
    action_whitelist: Mapped[dict] = mapped_column(JSON, default=dict)  # {"actions": ["component.create", ...]}
    action_blacklist: Mapped[dict] = mapped_column(JSON, default=dict)  # {"actions": ["remove_link", ...]}
    enabled_domains: Mapped[dict] = mapped_column(JSON, default=dict)   # {"domains": ["pv","wiring",...]}
    feature_flags: Mapped[dict] = mapped_column(JSON, default=dict)     # {"placeholder_fallback_enabled": true, ...}
    # Misc bag for forward-compat (kept for existing consumers)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    # Optimistic concurrency
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    updated_by_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    # --- Legacy fields retained for backward compatibility ---
    ai_auto_approve: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_threshold_low: Mapped[float] = mapped_column(Float, default=0.0)
    risk_threshold_medium: Mapped[float] = mapped_column(Float, default=0.75)
    risk_threshold_high: Mapped[float] = mapped_column(Float, default=1.1)  # never auto
    whitelisted_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"items": ["add_component", ...]}

    def whitelist_set(self) -> set[str]:
        actions = (self.action_whitelist or {}).get("actions", [])
        return set(actions)

    def thresholds(self) -> dict[str, float]:
        return {
            "default": self.risk_threshold_default,
            "low": self.risk_threshold_low,
            "medium": self.risk_threshold_medium,
            "high": self.risk_threshold_high,
        }

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "auto_approve_enabled": bool(self.auto_approve_enabled),
            "risk_threshold_default": float(self.risk_threshold_default or 0.0),
            "action_whitelist": self.action_whitelist or {"actions": []},
            "action_blacklist": self.action_blacklist or {"actions": []},
            "enabled_domains": self.enabled_domains or {"domains": []},
            "feature_flags": self.feature_flags or {},
            "data": self.data or {},
            "version": int(self.version or 1),
            "updated_by_id": self.updated_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

