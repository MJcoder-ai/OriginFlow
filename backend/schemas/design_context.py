from pydantic import BaseModel
from typing import Optional, Dict, Any


class DesignSnapshot(BaseModel):
    project_id: str
    revision: Optional[str] = None
    layer: Optional[str] = None
    selection: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class RequestContext(BaseModel):
    trace_id: str
    snapshot: Optional[DesignSnapshot] = None
    user_id: Optional[str] = None
