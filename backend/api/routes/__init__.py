# backend/api/routes/__init__.py
"""API route groups for the backend.

Importing submodules here makes them discoverable by the app.  The
``feedback`` module exposes the ``/ai/log-feedback`` endpoint for
recording user decisions about AI-suggested actions.
"""

from . import feedback  # noqa: F401  pylint: disable=unused-import
from . import feedback_v2  # noqa: F401  pylint: disable=unused-import
from . import design_knowledge  # noqa: F401  pylint: disable=unused-import
from . import component_library  # noqa: F401  pylint: disable=unused-import
from . import components  # noqa: F401  pylint: disable=unused-import
from . import memory  # noqa: F401  pylint: disable=unused-import
from . import traces  # noqa: F401  pylint: disable=unused-import
from . import me  # noqa: F401  pylint: disable=unused-import
from . import odl  # noqa: F401  pylint: disable=unused-import
