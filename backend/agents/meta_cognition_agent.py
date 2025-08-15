"""
MetaCognitionAgent provides a meta‑cognitive layer for OriginFlow agents.

This agent is invoked when a design task is blocked due to missing
context or ambiguous requirements.  It introspects the task context
(passed via ``kwargs``) and generates clarifying questions or
recommended next actions for the user.  The goal is to enable agents
to reason about their own knowledge gaps and ask for additional
information rather than failing silently.

The agent produces an ADPF‑compliant envelope with a design card
containing:

* ``questions`` – a list of clarifying questions the user should answer
  to unblock the workflow.
* ``recommended_actions`` – suggested next steps (e.g. upload
datasheets, specify backup hours) when questions cannot be formulated.

Future versions may integrate natural‑language summarisation of past
steps, retrieval of relevant context from the graph or requirements,
and dynamic prompting to gather more precise information.
"""
from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.utils.adpf import wrap_response


class MetaCognitionAgent(AgentBase):
    """Agent that generates clarifying questions when tasks are blocked."""

    name = "meta_cognition_agent"
    description = "Generates clarifying questions for blocked tasks."

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """This agent uses ``execute``; ``handle`` returns no actions."""
        return []

    async def execute(self, session_id: str, tid: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Examine the task context to propose clarifying questions.

        The meta‑cognition task is triggered when another agent returns
        ``status='blocked'`` due to missing information.  The triggering
        agent should pass a ``missing`` list (e.g. ``['inverter type',
        'mounting zone']``) or a ``reason`` string to the
        ``MetaCognitionAgent`` via ``kwargs``.  The agent then constructs
        a design card with questions or recommended actions.

        Args:
            session_id: Identifier of the current design session (unused).
            tid: Task identifier; must be ``meta_cognition``.
            **kwargs: Additional context such as ``missing`` or ``reason``.

        Returns:
            An ADPF envelope with a design card and no patch.
        """
        task = tid.lower().strip()
        thought = "Formulating clarifying questions to unblock the workflow."
        if task != "meta_cognition":
            return wrap_response(
                thought=f"Unsupported meta‑cognition task '{tid}'.",
                card={
                    "title": "Meta‑cognition",
                    "body": f"Task '{tid}' is not handled by MetaCognitionAgent.",
                },
                patch=None,
                status="pending",
            )

        missing: List[str] = kwargs.get("missing", []) or []
        reason: str = kwargs.get("reason", "")
        questions: List[str] = []
        recommended_actions: List[str] = []
        if missing:
            questions = [f"Please provide the {item}." for item in missing]
        elif reason:
            questions = [f"Could you clarify the following: {reason}?"]
        else:
            recommended_actions = [
                "Review the design requirements and ensure all fields are complete.",
                "Attach any missing datasheets or specifications.",
            ]

        card = {
            "title": "Clarifying questions",
            "body": "Additional information is required to proceed.",
            "questions": questions,
            "recommended_actions": recommended_actions,
        }
        return wrap_response(
            thought=thought,
            card=card,
            patch=None,
            status="blocked",
            warnings=None,
        )


meta_cognition_agent = register(MetaCognitionAgent())
register_spec(
    name=MetaCognitionAgent.name,
    domain="meta",
    risk_class="low",
    capabilities=["ask_question"],
)
