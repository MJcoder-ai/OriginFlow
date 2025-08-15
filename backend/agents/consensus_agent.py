"""
ConsensusAgent implements a simple consensus mechanism across multiple
candidate outputs from other domain agents.

In certain scenarios, multiple agents may propose alternative designs or
corrections for the same task (e.g. different wiring sizes or structural
layouts).  This agent aggregates these candidate outputs (passed in via
``kwargs`` as ``candidates``) and selects a single consensus output based
on confidence scores or a predefined heuristic.  The selected output is
returned in an ADPF envelope with a summary of the decision.

Future versions may implement more sophisticated consensus algorithms
(e.g. weighted voting, intersection of design patches, or negotiation
protocols) and allow manual override by the user.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.utils.adpf import wrap_response


class ConsensusAgent(AgentBase):
    """Agent that selects a consensus design from multiple candidates."""

    name = "consensus_agent"
    description = "Selects a consensus design among candidate outputs."

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """This agent relies on ``execute``; ``handle`` returns no actions."""
        return []

    async def execute(self, session_id: str, tid: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Select the best candidate design among multiple alternatives.

        The ``candidates`` argument should be a list of ADPF envelopes
        (dictionaries) produced by other agents for the same task.  Each
        candidate may include a ``card`` with an optional ``confidence`` field
        (float) indicating the agent's confidence in its output.  The
        consensus mechanism picks the candidate with the highest confidence; if
        no confidence values are present, the first candidate is selected.

        Args:
            session_id: Identifier of the design session (unused).
            tid: Task identifier; must be ``consensus``.
            **kwargs: Additional context; must include ``candidates``.

        Returns:
            An ADPF envelope containing the selected candidate's card and
            patch, along with a summary of the decision.
        """
        task = tid.lower().strip()
        thought = "Selecting a consensus design from multiple candidates."
        if task != "consensus":
            return wrap_response(
                thought=f"Unsupported consensus task '{tid}'.",
                card={
                    "title": "Consensus",
                    "body": f"Task '{tid}' is not handled by ConsensusAgent.",
                },
                patch=None,
                status="pending",
            )

        candidates: Optional[List[Dict[str, Any]]] = kwargs.get("candidates")
        if not candidates:
            return wrap_response(
                thought="No candidate designs were provided for consensus.",
                card={
                    "title": "Consensus",
                    "body": "No candidate designs to choose from.",
                },
                patch=None,
                status="blocked",
            )

        def _confidence(candidate: Dict[str, Any]) -> float:
            card = candidate.get("output", {}).get("card") or candidate.get("card", {})
            return float(card.get("confidence", 0.5)) if isinstance(card, dict) else 0.5

        best_candidate = max(candidates, key=_confidence)
        selected_card = best_candidate.get("output", {}).get("card") or best_candidate.get("card")
        selected_patch = best_candidate.get("output", {}).get("patch") or best_candidate.get("patch")
        summary_body = (
            f"Selected the design proposal with confidence {_confidence(best_candidate):.2f} "
            f"out of {len(candidates)} candidate(s)."
        )
        card = {
            "title": "Consensus decision",
            "body": summary_body,
            "selected_card": selected_card,
        }
        return wrap_response(
            thought=thought,
            card=card,
            patch=selected_patch,
            status="complete",
            warnings=None,
        )


consensus_agent = register(ConsensusAgent())
register_spec(
    name=ConsensusAgent.name,
    domain="orchestration",
    risk_class="medium",
    capabilities=["select_design"],
)
