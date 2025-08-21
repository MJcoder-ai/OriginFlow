"""
This module intentionally raises to flag **deleted legacy agents**.
Agents were replaced by:
  - Typed tools under `backend/tools/`
  - Single orchestrator route `/ai/act`
  - ODL single source of truth under `/odl/*`

If you see this error, migrate your call site to:
  1) Build/Fetch the minimal ODL slice (or let /ai/act do it)
  2) Call `POST /ai/act` with `task` and `args`
  3) If review is required, use `/approvals/*`
"""


class AgentsRemovedError(ImportError):
    pass


def __getattr__(name: str):
    raise AgentsRemovedError(
        f"Legacy agents are removed. Importing '{name}' from agent modules is no longer supported. "
        "Use typed tools (`backend/tools/*`) via the orchestrator (`POST /ai/act`). "
        "See docs/ARCHITECTURE_OVERVIEW.md and docs/API_CONTRACTS.md."
    )
