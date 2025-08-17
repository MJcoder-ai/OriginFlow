# Troubleshooting Database Errors

## Missing Column Errors

If you see an error like:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: schematic_components.layer
```

this means the database schema is out of sync with the SQLAlchemy models. To resolve:

1. Generate a migration:

```bash
alembic revision --autogenerate -m "add missing columns"
```

2. Apply migrations:

```bash
alembic upgrade head
```

Always run these commands whenever you change fields in `backend/models/`.

## Missing Table Errors

If you see an error like:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: memory
```

this indicates that a new table has been added to the ORM models without
a corresponding Alembic migration.  For example, the `Memory` model in
`backend/models/memory.py` defines a `memory` table for storing
conversation logs, design snapshots and other persisted state:contentReference[oaicite:6]{index=6}.
To resolve missing table errors:

1. Create a migration script that creates the missing table.  See
   `alembic/versions/9123abcd4567_create_memory_table.py` for an example.
2. Apply migrations:

```bash
alembic upgrade head
```

Keeping migrations in sync with your models prevents these errors and
ensures the database structure evolves alongside your code.

## Validation Error: source_id required

If the API returns an error like:

```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for LinkCreate
source_id
  Field required
target_id
  Field required
```

ensure that agents generate link actions using `source_id` and `target_id`.
Components can provide an optional `id` when created so subsequent links may
reference them before they are persisted.

