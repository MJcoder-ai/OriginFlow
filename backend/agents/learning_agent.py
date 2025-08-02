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

from typing import Dict, List

from sqlalchemy import select

from backend.database.session import SessionMaker
from backend.models.ai_action_log import AiActionLog
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
                select(AiActionLog.proposed_action, AiActionLog.user_decision)
            )
            rows = result.all()

        # Aggregate approval counts per action type.  We count both
        # ``approved`` and ``auto`` as approvals.  ``rejected`` counts
        # against the total.  Unknown decisions are ignored.
        stats: Dict[str, Dict[str, int]] = {}
        for proposed_action, decision in rows:
            # proposed_action is a dict containing at least an 'action'
            # key; skip if missing
            if not proposed_action or 'action' not in proposed_action:
                continue
            action_type = proposed_action['action']
            if action_type is None:
                continue
            rec = stats.setdefault(action_type, {'approved': 0, 'total': 0})
            if decision in ('approved', 'auto'):
                rec['approved'] += 1
                rec['total'] += 1
            elif decision == 'rejected':
                rec['total'] += 1

        # Compute approval ratios.  Avoid division by zero.
        ratios: Dict[str, float] = {}
        for atype, rec in stats.items():
            if rec['total'] > 0:
                ratios[atype] = rec['approved'] / rec['total']

        # Assign confidence values.  We only override the existing
        # confidence if we have data for that action type.
        for action in actions:
            # action.action is an Enum; cast to its value
            atype_str = action.action.value if isinstance(action.action, AiActionType) else str(action.action)
            if atype_str in ratios:
                action.confidence = ratios[atype_str]
