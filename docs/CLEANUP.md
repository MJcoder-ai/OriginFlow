# Phase 6 – Clean-up Notes

This phase removes brittle legacy references and unifies imports to reduce surprises in production:

## Backend
1. **DB sessions unified**
   - `backend/database/session.py` exposes `async_engine` (and keeps `engine` as a compatibility alias).
   - `backend/db/session.py`:
     - keeps the **sync** `engine` for utility code,
     - **re-exports** `async_engine` and `get_session` from `backend.database.session`.
   - Prefer importing from `backend.database.session` going forward.

2. **Deps module**
   - `backend/api/deps.py` no longer imports or references legacy `AiOrchestrator`/`ai_service`. This prevents `ModuleNotFoundError` seen earlier.

3. **Legacy 410 router**
   - The compatibility router has been **removed**. Unknown legacy paths now return 404.
   - Keep clients on the vNext surface documented in `docs/API_ENDPOINTS.md`.

4. **Health checks**
   - `/api/v1/system/readyz` imports the async engine from the canonical module.

## Frontend
1. **Deprecation hint**
   - `analyzeDesign()` now logs a single deprecation warning and returns a no-op result. Prefer `getPlanForSession()` + `act()`.

## Rollout guidance
- Keep clients on the OriginFlow API surface documented in `docs/API_ENDPOINTS.md`.
- Set `ENABLE_LEGACY_410_ROUTES=1` in non-prod environments to catch any stale client calls to removed endpoints.
- After a full sprint with clean logs, remove the env var and optionally delete `compat_legacy.py`.

