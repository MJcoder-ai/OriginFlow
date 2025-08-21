"""
Route aggregator. Only vNext surfaces should be imported here.
Any legacy endpoints are exposed via a 410 "Gone" compatibility router.
"""
from . import components  # noqa: F401
from . import links       # noqa: F401
from . import files       # noqa: F401
from . import odl         # noqa: F401
from . import ai_act      # noqa: F401
from . import odl_plan    # noqa: F401  # server-side planner endpoint

# Optional: Intent Firewall direct apply
try:  # pragma: no cover - optional
    from . import ai_apply  # noqa: F401
except Exception:  # pragma: no cover
    pass

# Mount explicit 410s for removed endpoints so misconfigured clients are obvious.
try:  # pragma: no cover - optional
    from . import compat_legacy  # noqa: F401
except Exception:  # pragma: no cover
    pass

