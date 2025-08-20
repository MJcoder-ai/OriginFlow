"""
Single orchestrator: plan→tool→patch flow with risk gating.

Responsibilities:
- Minimize context (layer-only view of ODL)
- Route the task to a typed tool
- Enforce risk policy (auto/review/blocked)
- Apply returned ODLPatch via ODL store with CAS
- Return a single ADPF envelope
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.adpf import wrap_response
from backend.orchestrator.context import load_graph_and_view_nodes
from backend.orchestrator.router import run_task, ActArgs
from backend.orchestrator.policy import decide
from backend.odl.store import ODLStore


class Orchestrator:
    """High-level orchestrator that composes tools to mutate ODL state."""

    async def run(
        self,
        *,
        db: AsyncSession,
        session_id: str,
        task: str,
        request_id: str,
        args: ActArgs,
    ):
        # 1) Load minimal context
        try:
            graph, view_nodes = await load_graph_and_view_nodes(db, session_id, args.layer)
        except KeyError:
            return wrap_response(
                thought=f"Cannot execute {task}: session not found",
                card={"title": "Not Found", "body": f"Session {session_id} does not exist."},
                patch=None,
                status="blocked",
            )

        # 2) Route to a tool
        patch = run_task(
            task=task,
            session_id=session_id,
            request_id=request_id,
            layer_nodes=view_nodes,
            args=args,
        )
        if patch is None:
            return wrap_response(
                thought=f"Unknown task '{task}'",
                card={"title": "Unknown Task", "body": f"Task '{task}' is not supported."},
                status="blocked",
            )

        # 3) Risk decision
        decision = decide(task)
        if decision == "blocked":
            return wrap_response(
                thought=f"Task '{task}' blocked by policy",
                card={"title": "Blocked by Policy", "body": "This action requires elevated privileges."},
                status="blocked",
            )
        if decision == "review_required":
            # Do not apply patch; return for human approval
            return wrap_response(
                thought=f"Task '{task}' requires approval before applying patch",
                card={
                    "title": "Approval Required",
                    "body": "Review the proposed change and approve to apply.",
                    "actions": [{"type": "propose_patch", "payload": patch.model_dump()}],
                },
                patch=None,
                status="pending",
            )

        # 4) Apply patch with CAS (auto-approved)
        store = ODLStore()
        new_graph, new_version = await store.apply_patch_cas(
            db=db,
            session_id=session_id,
            expected_version=graph.version,
            patch=patch,
        )
        return wrap_response(
            thought=f"Applied '{task}' via request {request_id}",
            card={"title": "Patch Applied", "subtitle": f"New version: {new_version}"},
            patch={"session_id": session_id, "version": new_version},
            status="complete",
        )
