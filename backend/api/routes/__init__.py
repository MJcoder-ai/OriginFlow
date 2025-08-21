"""
Route aggregator. Only the vNext API surfaces are imported here.
No legacy compatibility routes are mounted.
"""
from . import components    # noqa: F401
from . import links         # noqa: F401
from . import files         # noqa: F401
from . import odl           # noqa: F401
from . import ai_act        # noqa: F401
from . import odl_plan      # noqa: F401  # server-side planner endpoint
# Optional: Intent Firewall direct apply (if present in this deployment)
try:  # pragma: no cover
    from . import ai_apply  # noqa: F401
except Exception:  # pragma: no cover
    pass

