"""Simple learning agent for confidence estimation.

The :class:`LearningAgent` reads historical feedback from the
``ai_action_log`` table and computes empirical approval rates for
different action types.  These rates are used as confidence scores when
dispatching new AI actions.  The agent is intentionally simple—it
doesn't require external ML libraries and can be extended later to
incorporate richer features (e.g. prompt semantics or component
categories).  Approved and auto‑executed actions are treated as
approvals for the purposes of confidence estimation.

Usage:

.. code-block:: python

    learner = LearningAgent()
    await learner.assign_confidence(actions)

After calling :func:`assign_confidence`, each :class:`AiAction` in
``actions`` will have its ``confidence`` attribute set based on prior
user feedback.  If there is no historical data for a given action
type, the existing confidence is left unchanged.
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Optional
import os

from sqlalchemy import select

from backend.database.session import SessionMaker
from backend.models.ai_action_log import AiActionLog
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import get_vector_store
from backend.services.reference_confidence_service import ReferenceConfidenceService

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - optional dep
    OpenAI = None  # type: ignore
from backend.schemas.ai import AiAction, AiActionType


class LearningAgent:
    """Compute confidence scores for AI actions based on past feedback.

    This agent reads the :class:`AiActionLog` table, counts approvals
    and rejections per action type, and computes an empirical approval
    rate.  The computed rate (a float in ``[0, 1]``) is assigned to
    each :class:`AiAction` via its ``confidence`` field.  If no logs
    exist for a given action type, the existing confidence is left
    unchanged.
    """

    async def assign_confidence(self, actions: List[AiAction]) -> None:
        """Assign confidence to a list of actions in place.

        Args:
            actions: List of actions returned by the AI orchestrator.

        This method queries all records from the ``ai_action_log`` table,
        groups them by ``proposed_action['action']`` and counts how
        often each action type was approved or auto‑executed (treated as
        approved) versus rejected.  It then computes an approval ratio
        for each action type and assigns it to the corresponding
        actions.  If no historical data is available for an action type,
        the existing confidence is left unchanged.
        """
        # Early exit if there are no actions
        if not actions:
            return
        # Fetch all past logs.  In a production setting you might
        # restrict this query to recent history or aggregate results at
        # write time to avoid scanning the whole table.
        async with SessionMaker() as session:
            result = await session.execute(
                select(
                    AiActionLog.proposed_action,
                    AiActionLog.user_decision,
                    AiActionLog.prompt_text,
                )
            )
            rows = result.all()

        # Aggregate approval counts per action type and domain.  Each entry
        # in ``stats`` is a nested dictionary keyed first by action
        # (string) and then by domain (string).  The innermost dict
        # stores counts for approved and total decisions.  We treat
        # both ``approved`` and ``auto`` decisions as approvals.
        stats: Dict[str, Dict[str, Dict[str, int]]] = {}
        for proposed_action, decision, prompt_text in rows:
            # Skip malformed rows
            if not proposed_action or 'action' not in proposed_action:
                continue
            action_type = proposed_action['action']
            if not action_type:
                continue
            # Determine the domain of the original prompt.  This can help
            # distinguish between PV, HVAC or water domains when
            # computing approval rates.
            domain = self._determine_domain_from_text(prompt_text)
            rec = stats.setdefault(action_type, {}).setdefault(domain, {'approved': 0, 'total': 0})
            if decision in ('approved', 'auto'):
                rec['approved'] += 1
                rec['total'] += 1
            elif decision == 'rejected':
                rec['total'] += 1

        # Compute approval ratios for each (action_type, domain).  We
        # store the global (domain='general') ratio separately as a
        # fallback if a domain-specific ratio is not available.
        ratios: Dict[str, Dict[str, float]] = {}
        for atype, dom_dict in stats.items():
            ratios.setdefault(atype, {})
            for dom, rec in dom_dict.items():
                if rec['total'] > 0:
                    ratios[atype][dom] = rec['approved'] / rec['total']

        # Instantiate retrieval-based confidence service
        embedder = EmbeddingService()
        try:
            store = get_vector_store()
        except Exception:  # pragma: no cover - missing deps
            store = None
        llm_client = None
        if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
            llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        ref_service = ReferenceConfidenceService(store, embedder, llm_client) if store else None

        # Assign confidence values. First try retrieval-based method, then
        # fall back to empirical ratios if that fails.
        for action in actions:
            if ref_service:
                try:
                    result = await ref_service.evaluate_action(action, {}, {})
                    action.confidence = result["confidence"]
                    if hasattr(action, "meta") and isinstance(action.meta, dict):
                        action.meta["confidence_reasoning"] = result["reasoning"]
                    else:
                        action.meta = {"confidence_reasoning": result["reasoning"]}
                    continue
                except Exception:
                    pass

            # Determine the action type as a string
            atype_str = action.action.value if isinstance(action.action, AiActionType) else str(action.action)
            if atype_str not in ratios:
                continue
            # Guess the domain for this action based on the payload
            domain = self._determine_domain_from_action(action)
            # Prefer domain-specific ratio; fallback to 'general'
            dom_ratios = ratios[atype_str]
            if domain in dom_ratios:
                action.confidence = dom_ratios[domain]
            elif 'general' in dom_ratios:
                action.confidence = dom_ratios['general']

    def _determine_domain_from_text(self, text: Optional[str]) -> str:
        """Infer a domain (solar, hvac, pump, general) from natural language.

        Args:
            text: The user's original natural-language command from the user.
                If None, defaults to 'general'.

        Returns:
            A string representing the inferred domain: ``'solar'``,
            ``'hvac'``, ``'pump'``, or ``'general'``.

        This helper performs a simple keyword search on the lowercased
        text.  Future versions could use NLP models for improved
        accuracy.
        """
        if not text:
            return 'general'
        t = text.lower()
        if any(kw in t for kw in ('hvac', 'air')):
            return 'hvac'
        if any(kw in t for kw in ('pump', 'water')):
            return 'pump'
        if any(kw in t for kw in ('solar', 'pv')):
            return 'solar'
        return 'general'

    def _determine_domain_from_action(self, action: AiAction) -> str:
        """Infer a domain based on an action's payload.

        For ``addComponent`` actions we inspect the ``type`` field of
        the payload: PV-related types map to ``solar``; compressors or
        ductwork map to ``hvac``; pumps map to ``pump``; otherwise
        ``general``.  Other action types default to the domain of the
        action type (``general``).  This heuristic can be expanded as
        richer payloads are added.
        """
        try:
            # Only addComponent has a type field.  Fallback to general.
            if action.action == AiActionType.add_component:
                ctype = action.payload.get('type', '')
                if isinstance(ctype, str):
                    ctype_low = ctype.lower()
                    if ctype_low in {'panel', 'inverter', 'battery', 'charge_controller', 'pv_module'}:
                        return 'solar'
                    if ctype_low in {'compressor', 'evaporator', 'condensor', 'hvac', 'duct', 'thermostat'}:
                        return 'hvac'
                    if ctype_low in {'pump', 'valve', 'pipe'}:
                        return 'pump'
            # SuggestLink and other actions default to general
            return 'general'
        except Exception:
            return 'general'
