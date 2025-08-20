"""Action guard for normalizing AI-generated component actions.

This module implements a mandatory guardrail that ensures all addComponent
actions are processed through the StateAwareActionResolver, preventing
LLM misclassifications from reaching the execution layer.
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import logging
import os

from backend.schemas.analysis import DesignSnapshot

logger = logging.getLogger(__name__)


async def normalize_add_component(
    user_text: str,
    snapshot: Optional[DesignSnapshot],
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize the component type for an ``add_component`` action.

    Returns a copy of ``payload`` that **always** includes BOTH keys:
      - ``type``: canonical component type
      - ``component_type``: same as ``type`` (kept for backwards compatibility)

    Rules:
      1) If ``snapshot`` is None **or** SAAR errors → return the original payload unchanged.
      2) Only override the LLM-provided type when SAAR confidence >= MIN_SAAR_OVERRIDE (env: SAAR_MIN_OVERRIDE, default 0.55).
      3) Do not overrule an explicit user intent unless SAAR >= 0.85.
    """
    result = dict(payload)  # do not mutate caller's dict

    # Normalize existing keys immediately (back-compat)
    llm_type = (result.get("component_type") or result.get("type"))
    if llm_type:
        result["type"] = llm_type
        result["component_type"] = llm_type

    # Without a snapshot, guard does nothing. (Stateless fixes happen in AiOrchestrator)
    if snapshot is None:
        logger.info("Action guard: snapshot missing; returning original payload unchanged.")
        return result

    # Try SAAR (state-aware resolver)
    try:
        from backend.services.ai.state_action_resolver import StateAwareActionResolver
        resolver = StateAwareActionResolver()
        decision = resolver.resolve_add_component(user_text=user_text, snapshot=snapshot)
        predicted = decision.component_class
        conf = decision.confidence
    except Exception as ex:  # pragma: no cover — defensive
        logger.warning("Action guard: SAAR failed; keeping original type. err=%s", ex)
        return result

    MIN_SAAR_OVERRIDE = float(os.getenv("SAAR_MIN_OVERRIDE", "0.55"))
    HIGH_CONF_FOR_EXPLICIT = 0.85
    explicit_from_text = resolve_canonical_class(user_text)  # may be None
    llm_conf = float(result.get("_llm_confidence", 0.5))

    # Only consider override if SAAR beats both the minimum threshold and LLM confidence
    if conf >= max(MIN_SAAR_OVERRIDE, llm_conf):
        if explicit_from_text and llm_type and explicit_from_text != llm_type and conf < HIGH_CONF_FOR_EXPLICIT:
            logger.info(
                "Action guard: Keeping LLM type '%s' despite SAAR '%s' (explicit intent, conf=%.3f)",
                llm_type, predicted, conf
            )
            return result
        if predicted and predicted != llm_type:
            logger.info(
                "Action guard: Correcting component type from '%s' to '%s' (SAAR confidence: %.3f)",
                llm_type, predicted, conf
            )
            result["type"] = predicted
            result["component_type"] = predicted
    else:
        logger.info("Action guard: SAAR conf %.3f below threshold; keeping '%s'", conf, llm_type)

    return result


# Use the canonical implementation from StateAwareActionResolver
def explicit_class_from_text(text: str) -> Optional[str]:
    """Detect explicitly mentioned component class from user text."""
    try:
        from backend.services.ai.state_action_resolver import StateAwareActionResolver
        resolver = StateAwareActionResolver()
        return resolver._explicit_class_from_text(text)
    except Exception as e:
        logger.warning(f"Failed to detect explicit class from text '{text}': {e}")
        return None
