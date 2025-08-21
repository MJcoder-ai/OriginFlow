# backend/api/routes/__init__.py
"""API route groups for the backend.

Importing submodules here makes them discoverable by the app.  The
``feedback`` module exposes the ``/ai/log-feedback`` endpoint for
recording user decisions about AI-suggested actions.
"""

try:
    from . import feedback_v2  # noqa: F401  pylint: disable=unused-import
    from . import design_knowledge  # noqa: F401  pylint: disable=unused-import
    from . import components  # noqa: F401  pylint: disable=unused-import
    from . import naming_policy  # noqa: F401  pylint: disable=unused-import
    from . import memory  # noqa: F401  pylint: disable=unused-import
    from . import traces  # noqa: F401  pylint: disable=unused-import
    from . import me  # noqa: F401  pylint: disable=unused-import
    from . import odl  # noqa: F401  pylint: disable=unused-import
    from . import requirements  # noqa: F401  pylint: disable=unused-import
    from . import versioning  # noqa: F401  pylint: disable=unused-import
    from . import compatibility  # noqa: F401  pylint: disable=unused-import
    from . import snapshots  # noqa: F401  pylint: disable=unused-import
    from . import metrics_json  # noqa: F401  pylint: disable=unused-import
    from . import layout  # noqa: F401  pylint: disable=unused-import
    from . import governance  # noqa: F401  pylint: disable=unused-import
    from . import approvals  # noqa: F401  pylint: disable=unused-import
    from . import approvals_v1  # noqa: F401  pylint: disable=unused-import
except Exception:  # pragma: no cover - optional imports
    pass
