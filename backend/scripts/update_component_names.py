"""Utility script to regenerate component names after a policy change.

This script can be run from the command line to update the `name` field
for all components using the current naming policy. It is functionally
equivalent to calling the naming policy API with
``apply_to_existing=true`` but allows administrators to perform the
migration offline or schedule it during maintenance windows.

Usage:

```
python -m backend.scripts.update_component_names
```

Ensure that the application’s configuration and database settings are
correctly initialised before running this script. See
``docs/naming_policy.md`` for more information on naming policy management.
"""

from __future__ import annotations

import asyncio

from backend.database.session import SessionMaker
from backend.services.component_name_migration import update_existing_component_names


async def main() -> None:
    """Entry point for the update script.

    Opens a new database session and invokes the migration function to
    regenerate names using the current naming policy.
    """
    async with SessionMaker() as session:
        await update_existing_component_names(session)


if __name__ == "__main__":
    asyncio.run(main())
