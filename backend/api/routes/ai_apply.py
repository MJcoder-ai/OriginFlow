"""Intent Firewall API - Enterprise-grade action application endpoint."""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ai.action_firewall import normalize_add_component_action
from backend.schemas.analysis import DesignSnapshot
from backend.api.deps import get_session
from backend.services.component_service import ComponentService
from backend.services.link_service import LinkService
from backend.utils.id import generate_id

logger = logging.getLogger(__name__)
router = APIRouter()


class ApplyActionsRequest(BaseModel):
    session_id: str = Field(..., description="Design session id")
    actions: List[Dict[str, Any]] = Field(..., description="LLM-decided actions")
    user_texts: Optional[List[str]] = Field(None, description="Raw user commands aligned by index; improves normalization")
    snapshot: Optional[Dict[str, Any]] = Field(None, description="Current design snapshot for context")


@router.post("/ai/apply", summary="Apply AI actions server-side with Intent Firewall")
async def apply_actions(
    req: ApplyActionsRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Server-side apply endpoint that validates and **normalizes** AI actions before execution.
    Guarantees final class/type selection respects explicit user intent (Intent Firewall).
    
    This is the ONLY endpoint that should be used for applying AI-generated actions.
    Direct calls to /components or /links from AI flows bypass the Intent Firewall.
    """
    
    # Parse snapshot if provided
    snapshot = None
    if req.snapshot:
        try:
            snapshot = DesignSnapshot.model_validate(req.snapshot)
        except Exception as e:
            logger.warning(f"Failed to parse snapshot: {e}")
    
    # Apply Intent Firewall to normalize all actions
    sanitized: List[Dict[str, Any]] = []
    results = []
    
    for idx, action in enumerate(req.actions):
        action_type = (action.get("action") or "").lower()
        payload = dict(action.get("payload") or {})
        
        if action_type == "add_component":
            # Intent Firewall: enforce explicit/fuzzy override on class
            user_text = ""
            if req.user_texts and idx < len(req.user_texts):
                user_text = req.user_texts[idx] or ""
            else:
                user_text = action.get("text") or action.get("rationale") or ""
            
            # Apply Intent Firewall normalization
            payload = await normalize_add_component_action(
                user_text=user_text, 
                snapshot=snapshot, 
                payload=payload
            )
            
            # Execute the normalized action
            try:
                component_service = ComponentService(session)
                
                # Ensure required fields
                if not payload.get("name"):
                    component_type = payload.get("component_type", "component")
                    payload["name"] = f"generic_{component_type}"
                
                if not payload.get("id"):
                    payload["id"] = generate_id("component")
                
                # Add session context
                payload["session_id"] = req.session_id
                
                # Create the component with normalized payload
                from backend.schemas.component import ComponentCreate
                component_data = ComponentCreate.model_validate(payload)
                created_component = await component_service.create(component_data)
                
                results.append({
                    "action": "add_component",
                    "status": "success",
                    "component_id": created_component.id,
                    "component_type": created_component.type,
                    "firewall_enforced": payload.get("_firewall", {}).get("enforced", False)
                })
                
                logger.info(f"Intent Firewall: Successfully created {created_component.type} component (ID: {created_component.id})")
                
            except Exception as e:
                logger.error(f"Failed to create component: {e}")
                results.append({
                    "action": "add_component", 
                    "status": "error",
                    "error": str(e)
                })
        
        elif action_type == "add_link":
            # Execute link creation (no firewall needed for links)
            try:
                link_service = LinkService(session)
                
                if not payload.get("id"):
                    payload["id"] = generate_id("link")
                
                payload["session_id"] = req.session_id
                
                from backend.schemas.link import LinkCreate
                link_data = LinkCreate.model_validate(payload)
                created_link = await link_service.create(link_data)
                
                results.append({
                    "action": "add_link",
                    "status": "success", 
                    "link_id": created_link.id
                })
                
            except Exception as e:
                logger.error(f"Failed to create link: {e}")
                results.append({
                    "action": "add_link",
                    "status": "error", 
                    "error": str(e)
                })
        
        else:
            # Other action types (validation, report, etc.)
            sanitized.append(action)
            results.append({
                "action": action_type,
                "status": "deferred",
                "note": "Non-executable action type, returned as-is"
            })
    
    await session.commit()
    
    return {
        "applied": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "deferred": len([r for r in results if r["status"] == "deferred"]),
        "results": results,
        "session_id": req.session_id
    }
