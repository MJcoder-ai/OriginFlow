"""Enhanced learning agent with confidence estimation and auto-execution.

The :class:`LearningAgent` reads historical feedback from the
``ai_action_log`` table and computes empirical approval rates for
different action types.  These rates are used as confidence scores when
dispatching new AI actions. The agent now supports:

- Dynamic confidence thresholds for auto-execution
- Contextual learning based on design state
- User feedback integration for continuous improvement
- Risk assessment for different action types

High-confidence simple actions (like link creation) can be auto-executed
to improve user experience while maintaining safety through thresholds.

Usage:

.. code-block:: python

    learner = LearningAgent()
    await learner.assign_confidence(actions)

    # Inject custom implementations for testing or experimentation
    learner = LearningAgent(vector_store=my_store, embedding_service=my_embedder)

After calling :func:`assign_confidence`, each :class:`AiAction` in
``actions`` will have its ``confidence`` attribute set based on prior
user feedback.  If there is no historical data for a given action
type, the existing confidence is left unchanged.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import os
import json
from datetime import datetime, timedelta

from sqlalchemy import select, func

from backend.database.session import SessionMaker
from backend.models.ai_action_log import AiActionLog
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore, get_vector_store
from backend.services.reference_confidence_service import ReferenceConfidenceService

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - optional dep
    OpenAI = None  # type: ignore
from backend.schemas.ai import AiAction, AiActionType


class LearningAgent:
    """Enhanced learning agent with confidence estimation and auto-execution.

    This agent reads the :class:`AiActionLog` table, counts approvals
    and rejections per action type, and computes an empirical approval
    rate.  The computed rate (a float in ``[0, 1]``) is assigned to
    each :class:`AiAction` via its ``confidence`` field.  
    
    New features:
    - Auto-execution thresholds based on action risk levels
    - Contextual confidence adjustment based on design state
    - User feedback integration for continuous improvement
    - Risk assessment for different action types
    """

    # Auto-execution thresholds by action type (risk level)
    AUTO_EXECUTION_THRESHOLDS = {
        # Low risk actions - can auto-execute with high confidence
        'addLink': 0.85,
        'suggestLink': 0.80,
        'positionComponent': 0.75,
        
        # Medium risk actions - require very high confidence
        'addComponent': 0.95,
        'removeComponent': 0.90,
        'removeLink': 0.85,
        
        # High risk actions - never auto-execute
        'bomReport': 1.1,  # Impossible threshold
        'clearCanvas': 1.1,
    }

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_service: EmbeddingService | None = None,
        enable_auto_execution: bool = True,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.enable_auto_execution = enable_auto_execution
        
        if vector_store is not None:
            self.vector_store: VectorStore | None = vector_store
        else:
            try:
                self.vector_store = get_vector_store()
            except Exception:  # pragma: no cover - optional dependency
                self.vector_store = None

    async def assign_confidence(
        self,
        actions: List[AiAction],
        design_context: Dict[str, Any] | None = None,
        recent_actions: List[Dict[str, Any]] | None = None,
    ) -> None:
        """Assign confidence to a list of actions in place.

        Args:
            actions: List of actions returned by the AI orchestrator.
            design_context: Current design snapshot passed from the caller.
            recent_actions: Short history of preceding actions.

        This method queries all records from the ``ai_action_log`` table,
        groups them by ``proposed_action['action']`` and counts how
        often each action type was approved or auto‑executed (treated as
        approved) versus rejected.  It then computes an approval ratio
        for each action type and assigns it to the corresponding
        actions.  If no historical data is available for an action type,
        the existing confidence is left unchanged.  When a reference
        confidence service is available, it is consulted first using the
        provided ``design_context`` and ``recent_actions`` to perform
        retrieval-based scoring.
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
        store = self.vector_store
        embedder = self.embedding_service
        llm_client = None
        if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
            llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        ref_service = ReferenceConfidenceService(store, embedder, llm_client) if store else None

        # Assign confidence values. First try retrieval-based method, then
        # fall back to empirical ratios if that fails.
        ctx = design_context or {}
        history = recent_actions or []
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Learning agent processing {len(actions)} actions with {len(ratios)} learned ratios")
        if ratios:
            logger.info(f"Available action types in ratios: {list(ratios.keys())}")
        
        for action in actions:
            if ref_service:
                try:
                    result = await ref_service.evaluate_action(action, ctx, history)
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
            logger.info(f"Processing action {atype_str} with current confidence {action.confidence}")
            
            if atype_str not in ratios:
                logger.info(f"No historical data for action type {atype_str}, keeping default confidence")
                continue
                
            # Guess the domain for this action based on the payload
            domain = self._determine_domain_from_action(action)
            logger.info(f"Determined domain: {domain} for action {atype_str}")
            
            # Prefer domain-specific ratio; fallback to 'general'
            dom_ratios = ratios[atype_str]
            logger.info(f"Available domains for {atype_str}: {list(dom_ratios.keys())}")
            
            # Try to find a matching domain ratio
            confidence_updated = False
            if domain in dom_ratios:
                old_confidence = action.confidence
                action.confidence = dom_ratios[domain]
                logger.info(f"Updated confidence from {old_confidence} to {action.confidence} using domain {domain}")
                confidence_updated = True
            elif 'general' in dom_ratios:
                old_confidence = action.confidence
                action.confidence = dom_ratios['general']
                logger.info(f"Updated confidence from {old_confidence} to {action.confidence} using general domain")
                confidence_updated = True
            else:
                # If no exact match, try any available domain for non-component actions
                # This helps with domain mismatches like addLink getting 'general' but data stored under 'solar'
                if action.action != AiActionType.add_component and dom_ratios:
                    # Use the first available domain's ratio
                    available_domain = list(dom_ratios.keys())[0]
                    old_confidence = action.confidence
                    action.confidence = dom_ratios[available_domain]
                    logger.info(f"Updated confidence from {old_confidence} to {action.confidence} using fallback domain {available_domain}")
                    confidence_updated = True
            
            if not confidence_updated:
                logger.info(f"No suitable domain data found for {atype_str}, keeping default confidence")
            
            # Mark actions for auto-execution if confidence is high enough
            if self.enable_auto_execution and self._should_auto_execute(action):
                if hasattr(action, "meta") and isinstance(action.meta, dict):
                    action.meta["auto_execute"] = True
                    action.meta["auto_reason"] = f"High confidence ({action.confidence:.2f}) for low-risk action"
                else:
                    action.meta = {
                        "auto_execute": True,
                        "auto_reason": f"High confidence ({action.confidence:.2f}) for low-risk action"
                    }

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
    
    def _should_auto_execute(self, action: AiAction) -> bool:
        """Determine if an action should be auto-executed based on confidence and risk."""
        if not self.enable_auto_execution:
            return False
        
        atype_str = action.action.value if isinstance(action.action, AiActionType) else str(action.action)
        threshold = self.AUTO_EXECUTION_THRESHOLDS.get(atype_str, 1.1)  # Default: never auto-execute
        
        return action.confidence >= threshold
    
    async def process_user_feedback(
        self, 
        action: AiAction, 
        feedback: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Process user feedback to improve future confidence estimates.
        
        Args:
            action: The action that received feedback
            feedback: 'accepted', 'rejected', or 'modified'
            context: Additional context about the feedback
        """
        # Store feedback in the action log for future learning
        async with SessionMaker() as session:
            entry = AiActionLog(
                session_id=context.get('session_id') if context else None,
                prompt_text=context.get('original_prompt', '') if context else '',
                proposed_action=action.payload,
                user_decision=feedback,
                meta=json.dumps({
                    'confidence': action.confidence,
                    'auto_executed': getattr(action, 'meta', {}).get('auto_execute', False),
                    'feedback_context': context or {},
                    'timestamp': datetime.now().isoformat()
                })
            )
            session.add(entry)
            await session.commit()
    
    async def get_confidence_explanation(self, action: AiAction) -> Dict[str, Any]:
        """Get a detailed explanation of how confidence was calculated.
        
        Returns:
            Dictionary with confidence breakdown and reasoning
        """
        atype_str = action.action.value if isinstance(action.action, AiActionType) else str(action.action)
        domain = self._determine_domain_from_action(action)
        
        # Get historical data for this action type
        async with SessionMaker() as session:
            result = await session.execute(
                select(
                    func.count().label('total'),
                    func.sum(
                        func.case(
                            (AiActionLog.user_decision.in_(['approved', 'auto']), 1),
                            else_=0
                        )
                    ).label('approved')
                ).where(
                    AiActionLog.proposed_action['action'].astext == atype_str
                )
            )
            stats = result.first()
        
        total = stats.total if stats else 0
        approved = stats.approved if stats else 0
        approval_rate = approved / total if total > 0 else None
        
        auto_execute_threshold = self.AUTO_EXECUTION_THRESHOLDS.get(atype_str, 1.1)
        can_auto_execute = action.confidence >= auto_execute_threshold
        
        return {
            'action_type': atype_str,
            'domain': domain,
            'confidence': action.confidence,
            'historical_data': {
                'total_actions': total,
                'approved_actions': approved,
                'approval_rate': approval_rate
            },
            'auto_execution': {
                'can_auto_execute': can_auto_execute,
                'threshold': auto_execute_threshold,
                'enabled': self.enable_auto_execution
            },
            'confidence_source': 'historical_data' if approval_rate is not None else 'default',
            'risk_level': self._get_risk_level(atype_str)
        }
    
    def _get_risk_level(self, action_type: str) -> str:
        """Get the risk level for an action type."""
        threshold = self.AUTO_EXECUTION_THRESHOLDS.get(action_type, 1.1)
        
        if threshold >= 1.0:
            return 'high'
        elif threshold >= 0.90:
            return 'medium'
        else:
            return 'low'
    
    async def update_auto_execution_threshold(
        self, 
        action_type: str, 
        new_threshold: float
    ) -> None:
        """Update auto-execution threshold for an action type.
        
        This allows dynamic adjustment of thresholds based on performance.
        """
        if 0.0 <= new_threshold <= 1.1:
            self.AUTO_EXECUTION_THRESHOLDS[action_type] = new_threshold
        else:
            raise ValueError("Threshold must be between 0.0 and 1.1")
    
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get metrics about the learning agent's performance."""
        async with SessionMaker() as session:
            # Get recent feedback stats
            week_ago = datetime.now() - timedelta(days=7)
            
            result = await session.execute(
                select(
                    AiActionLog.proposed_action['action'].astext.label('action_type'),
                    AiActionLog.user_decision,
                    func.count().label('count')
                ).where(
                    AiActionLog.timestamp >= week_ago
                ).group_by(
                    AiActionLog.proposed_action['action'].astext,
                    AiActionLog.user_decision
                )
            )
            
            stats = {}
            for row in result:
                action_type = row.action_type
                decision = row.user_decision
                count = row.count
                
                if action_type not in stats:
                    stats[action_type] = {'approved': 0, 'rejected': 0, 'auto': 0, 'total': 0}
                
                stats[action_type][decision] = count
                stats[action_type]['total'] += count
            
            # Calculate approval rates and auto-execution stats
            for action_type, data in stats.items():
                if data['total'] > 0:
                    data['approval_rate'] = (data['approved'] + data['auto']) / data['total']
                    data['auto_execution_rate'] = data['auto'] / data['total']
                else:
                    data['approval_rate'] = 0.0
                    data['auto_execution_rate'] = 0.0
        
        return {
            'enabled': self.enable_auto_execution,
            'thresholds': self.AUTO_EXECUTION_THRESHOLDS,
            'recent_stats': stats,
            'metrics_period': '7_days'
        }
