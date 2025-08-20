from __future__ import annotations
"""
Intent Firewall (server-side, final boundary).

This normalizes every incoming AI action *before* it can create/modify resources.
It ensures explicit user intent (e.g., "add inverter") is respected even if an
upstream agent or the frontend passed a wrong component_type.
"""
import logging
from typing import Dict, Optional
from backend.schemas.analysis import DesignSnapshot
from backend.ai.ontology import resolve_canonical_class

logger = logging.getLogger(__name__)

async def normalize_add_component_action(
    *,
    user_text: str,
    snapshot: Optional[DesignSnapshot],
    payload: Dict,
) -> Dict:
    """
    Final normalization for add_component.
    Rules:
    - If user_text clearly names exactly one class (explicit or fuzzy),
      FORCE that canonical class (overrides priors/heuristics).
    - Otherwise, keep existing payload['component_type'] (assumed upstream SAAR).
    - Never change to *another* class due to library availability; if no real
      model exists, fall back to generic of the *same* class.
    """
    original_type = payload.get("component_type") or payload.get("type")
    
    # Use Intent Firewall to resolve user intent
    requested = resolve_canonical_class(user_text or "")
    
    if requested:
        # User explicitly mentioned a component type - FORCE it
        logger.info(f"Intent Firewall: User explicitly requested '{requested}' from text: '{user_text}' (was: {original_type})")
        payload["component_type"] = requested
        payload["type"] = requested
        
        # Add firewall metadata for traceability
        payload["_firewall"] = {
            "enforced": True,
            "user_intent": requested,
            "original_type": original_type,
            "confidence": 1.0,
            "rationale": f"Explicit mention of '{requested}' in user text"
        }
    else:
        # No explicit mention - trust upstream SAAR/agent decision
        if original_type:
            logger.info(f"Intent Firewall: No explicit mention, preserving upstream decision: '{original_type}'")
            payload["component_type"] = original_type
            payload["type"] = original_type
        
        payload["_firewall"] = {
            "enforced": False,
            "user_intent": None,
            "original_type": original_type,
            "confidence": 0.5,
            "rationale": "No explicit mention found, trusting upstream classification"
        }
    
    return payload
