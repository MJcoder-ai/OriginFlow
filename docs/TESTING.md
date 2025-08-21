# Testing & CI

## Local tests
Install dependencies and run pytest:
```bash
poetry install
export DATABASE_URL="sqlite+aiosqlite:///$PWD/.localdb/local.db"
mkdir -p .localdb
poetry run pytest -q
```

### Smoke test (end-to-end)
Boot the API and exercise the MVP loop (plan → act → view):
```bash
chmod +x scripts/smoke.sh
./scripts/smoke.sh
```
The script will:
1. Start the API on port 8001
2. Create a session
3. Get a plan for “design a 5kW solar PV system”
4. Execute inverter, panels, and wiring tasks
5. Verify the view has at least 2 nodes and 1 edge

## Continuous Integration
The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:
- Installs deps with Poetry
- Runs unit tests (`pytest`)
- Executes the smoke test (`scripts/smoke.sh`)

CI uses a file-backed SQLite database under `.localdb/ci.db` so the API
works consistently under multi-connection scenarios.
