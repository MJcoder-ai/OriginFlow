# backend/schemas/__init__.py
"""
Pydantic schemas for the OriginFlow backend.

Each schema module defines a Pydantic model that mirrors the fields of
its corresponding SQLAlchemy ORM model.  When adding a new ORM model,
ensure that a matching Pydantic schema is added here and imported so
that FastAPI can discover it automatically.  Keeping these layers in
sync prevents subtle bugs where fields appear in one layer but not
another:contentReference[oaicite:2]{index=2}.
"""

from .component_master import ComponentMasterCreate, ComponentMasterInDB  # noqa: F401
from .memory import Memory as MemorySchema  # noqa: F401
from .governance import TenantSettingsRead, TenantSettingsUpdate  # noqa: F401
from .tenant_policy import (
    PolicyDoc,
    PolicyUpdate,
    PolicyTestRequest,
    PolicyTestResult,
)  # noqa: F401
from .approvals import (
    ApprovalListQuery,
    ApprovalDecision,
    BatchDecisionRequest,
)  # noqa: F401
