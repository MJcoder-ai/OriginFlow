"""
Route aggregator. Only the OriginFlow API surfaces are imported here.
No legacy compatibility routes are mounted.
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

# Optionally mount explicit 410s for removed endpoints so misconfigured clients are obvious.
# Enterprises may want this disabled in production to reduce noise.
import os as _os
if _os.getenv("ENABLE_LEGACY_410_ROUTES", "0") == "1":
    try:  # pragma: no cover - optional
        from . import compat_legacy  # noqa: F401
    except Exception:  # pragma: no cover
        pass

