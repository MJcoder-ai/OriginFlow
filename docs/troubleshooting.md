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
