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

## Checklist Panel Missing

If running `design a 5 kW solar PV system` causes components to appear without
any checklist items, the frontend is likely bypassing the `pendingActions`
queue. Update `executeAiActions` in `frontend/src/appStore.ts` so that design
modifications are queued and only informational actions (like `validation` or
`report`) execute immediately. Once queued, the `ChecklistPanel` will display the
pending actions for approval.
