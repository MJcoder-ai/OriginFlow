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
from backend.services.component_library import find_by_categories
from backend.tools.selection import find_components
from backend.tools.schemas import SelectionInput
from backend.domains.registry import (
    categories_for_placeholder,
    risk_override as domain_risk_override,
)
from backend.perf.budgeter import BudgetPolicy, estimate_chars, budget_check


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

        # 1b) Budget check (cheap, before tool/LLM work)
        est_chars = estimate_chars([n.model_dump() for n in view_nodes], args.model_dump())
        decision, warns = budget_check(
            policy=BudgetPolicy(),
            view_nodes_count=len(view_nodes),
            estimated_chars=est_chars,
        )
        if decision == "block":
            return wrap_response(
                thought=f"Task '{task}' blocked by budget policy",
                card={"title": "Over Budget", "body": "; ".join(warns)},
                status="blocked",
            )
        budget_warnings = warns  # attach later if any

        # 2) Determine domain from graph meta (default 'PV')
        domain = (graph.meta or {}).get("domain") or "PV"

        # 3) Special handling for placeholder replacement: select real components, then build patch
        if task == "replace_placeholders":
            # Identify placeholders in current layer
            placeholder_nodes = [n for n in view_nodes if (n.attrs or {}).get("placeholder") is True]
            if args.placeholder_type:
                placeholder_nodes = [n for n in placeholder_nodes if n.type == args.placeholder_type]
            if not placeholder_nodes:
                return wrap_response(
                    thought="No placeholders to replace in the current layer",
                    card={"title": "Nothing to Replace", "body": "No matching placeholders found."},
                    status="complete",
                )
            # Build candidate pool
            pool = list(args.pool or [])
            if not pool:
                categories = list(args.categories or [])
                # Use domain registry when categories are not explicitly provided
                if not categories and args.placeholder_type:
                    mapped = categories_for_placeholder(domain, args.placeholder_type)
                    categories = mapped or [args.placeholder_type.replace("generic_", "")]
                min_power = None
                if args.requirements:
                    mp = args.requirements.get("target_power")
                    if mp:
                        try:
                            min_power = float(mp) / max(len(placeholder_nodes), 1)
                        except Exception:
                            pass
                pool = await db.run_sync(lambda s: find_by_categories(s, categories=categories, min_power=min_power))
            # Rank candidates (simple heuristic over provided pool)
            sel = find_components(SelectionInput(
                session_id=session_id,
                request_id=request_id,
                placeholder_type=args.placeholder_type or "generic",
                requirements=args.requirements or {},
                pool=pool,
            ))
            if not sel.candidates:
                return wrap_response(
                    thought="No suitable real components found for replacement",
                    card={"title": "No Candidates", "body": "Try relaxing requirements or adding components."},
                    status="blocked",
                )
            # Compose replacement items (naive: take the top candidate for all placeholders)
            top = sel.candidates[0]
            new_type = (args.placeholder_type or "").replace("generic_", "") or None
            repl_items = [
                {"node_id": n.id, "part_number": top.part_number, "new_type": new_type, "attrs": {"selected_name": top.name}}
                for n in placeholder_nodes
            ]
            # Build replacement patch via router
            rep_args = ActArgs(layer=args.layer, attrs={"repl_items": repl_items})
            patch = await run_task(
                task=task,
                session_id=session_id,
                request_id=request_id,
                layer_nodes=view_nodes,
                args=rep_args,
            )
        else:
            # Route to a tool
            patch = await run_task(
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

        # 4) Risk decision (allow domain override)
        decision = decide(task, risk_override=domain_risk_override(domain, task))
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
                warnings=budget_warnings or None,
            )

        # 5) Apply patch with CAS (auto-approved)
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
            warnings=budget_warnings or None,
        )
