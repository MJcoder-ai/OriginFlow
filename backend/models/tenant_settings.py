from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Float, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class TenantSettings(Base):
    """Per-tenant governance and feature configuration."""

    __tablename__ = "tenant_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    # Governance
    ai_auto_approve: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_threshold_low: Mapped[float] = mapped_column(Float, default=0.0)
    risk_threshold_medium: Mapped[float] = mapped_column(Float, default=0.75)
    risk_threshold_high: Mapped[float] = mapped_column(Float, default=1.1)  # never auto
    whitelisted_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"items": ["add_component", ...]}

    # Domain & features
    enabled_domains: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"items": ["pv","structural"]}
    feature_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)    # {"battery": true, ...}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def whitelist_set(self) -> set[str]:
        items = (self.whitelisted_actions or {}).get("items", [])
        return set(items)

    def thresholds(self) -> dict[str, float]:
        return {
            "low": self.risk_threshold_low,
            "medium": self.risk_threshold_medium,
            "high": self.risk_threshold_high,
        }

