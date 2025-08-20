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
from backend.services.ai.intent_firewall import resolve_canonical_class
from backend.services.ai.state_action_resolver import StateAwareActionResolver

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
    HIGH_CONF_FOR_EXPLICIT = float(os.getenv("SAAR_EXPLICIT_LOCK", "0.85"))
    explicit_from_text = resolve_canonical_class(user_text)  # may be None
    llm_conf = float(result.get("_llm_confidence", 0.5))

    # If the user explicitly asked for a class, prefer it unless SAAR is extremely sure *against* it.
    if explicit_from_text:
        if predicted != explicit_from_text and conf >= HIGH_CONF_FOR_EXPLICIT:
            # SAAR is very confident in a different class → keep SAAR
            logger.info(
                "Action guard: SAAR overrides explicit intent '%s' with '%s' (conf=%.3f >= %.2f)",
                explicit_from_text, predicted, conf, HIGH_CONF_FOR_EXPLICIT
            )
        else:
            # Honor explicit user intent
            result["type"] = explicit_from_text
            result["component_type"] = explicit_from_text
            logger.info("Action guard: honoring explicit intent '%s'", explicit_from_text)
            return result

    # Otherwise, allow SAAR to override weak/unknown LLM classifications.
    if predicted and predicted != "unknown" and conf >= MIN_SAAR_OVERRIDE:
        # Don't stomp very high confidence LLM unless SAAR is clearly confident.
        llm_conf = float(result.get("_llm_confidence") or 0.0)
        if llm_conf >= 0.90 and predicted != result["type"] and conf < 0.90:
            logger.info(
                "Action guard: preserving high-confidence LLM type '%s' (LLM=%.2f, SAAR=%s@%.2f)",
                result["type"], llm_conf, predicted, conf
            )
        else:
            logger.info(
                "Action guard: correcting component type from '%s' to '%s' (SAAR conf: %.3f)",
                result["type"], predicted, conf
            )
            result["type"] = predicted
            result["component_type"] = predicted

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
