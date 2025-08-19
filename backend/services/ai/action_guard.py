"""Action guard for normalizing AI-generated component actions.

This module implements a mandatory guardrail that ensures all addComponent
actions are processed through the StateAwareActionResolver, preventing
LLM misclassifications from reaching the execution layer.
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import logging

from backend.schemas.analysis import DesignSnapshot

logger = logging.getLogger(__name__)


async def normalize_add_component(
    user_text: str, 
    snapshot: Optional[DesignSnapshot], 
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Normalize component addition payload through SAAR guardrail.
    
    This function ensures that all addComponent actions are validated
    through the StateAwareActionResolver, regardless of which agent
    or LLM generated the original action.
    
    Args:
        user_text: The original user command text
        snapshot: Current design snapshot for context
        payload: The component payload to normalize
        
    Returns:
        Normalized payload with corrected component type
    """
    try:
        from backend.services.ai.state_action_resolver import StateAwareActionResolver
        
        # Get SAAR classification
        resolver = StateAwareActionResolver()
        decision = resolver.resolve_add_component(user_text=user_text, snapshot=snapshot)
        
        # Extract LLM's component type from payload
        llm_type = payload.get("type") or payload.get("component_type")
        llm_confidence = payload.get("_llm_confidence", 0.0)
        
        # Decision logic: Use SAAR unless LLM beats it by a clear margin
        should_override = (
            not llm_type or 
            llm_type != decision.component_class or 
            llm_confidence < decision.confidence - 0.2
        )
        
        if should_override:
            logger.info(
                f"Action guard: Correcting component type from '{llm_type}' to '{decision.component_class}' "
                f"for user text: '{user_text}' (SAAR confidence: {decision.confidence:.3f})"
            )
            payload["type"] = decision.component_class
            payload["component_type"] = decision.component_class
        else:
            logger.info(
                f"Action guard: Keeping LLM component type '{llm_type}' "
                f"(LLM confidence: {llm_confidence:.3f} vs SAAR: {decision.confidence:.3f})"
            )
        
        # Always add SAAR metadata for traceability
        payload["_resolver"] = {
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "original_llm_type": llm_type,
            "corrected": should_override
        }
        
        # Set target layer if not specified
        payload.setdefault("target_layer", decision.target_layer or "single_line")
        
        return payload
        
    except Exception as e:
        logger.error(f"Action guard failed for user_text='{user_text}': {e}")
        # Return original payload if guard fails to avoid breaking the system
        return payload


def explicit_class_from_text(text: str) -> Optional[str]:
    """Detect explicitly mentioned component class from user text.
    
    Args:
        text: User input text to analyze
        
    Returns:
        Component class if exactly one is mentioned, None otherwise
    """
    try:
        from backend.ai.ontology import ONTOLOGY
        
        text_lower = text.lower()
        hits = []
        
        for cls, synonyms in ONTOLOGY.classes.items():
            # Check class name and all synonyms
            all_terms = [cls.lower()] + [syn.lower() for syn in synonyms]
            if any(term in text_lower for term in all_terms):
                hits.append(cls)
        
        # Return class only if exactly one is mentioned (unambiguous)
        unique_hits = list(set(hits))
        return unique_hits[0] if len(unique_hits) == 1 else None
        
    except Exception as e:
        logger.warning(f"Failed to detect explicit class from text '{text}': {e}")
        return None
