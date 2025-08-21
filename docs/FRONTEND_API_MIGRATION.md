# Frontend → OriginFlow API Migration (Phase 2)

## Endpoints
| Capability | OriginFlow API | Notes |
|---|---|---|
| Create session | `POST /api/v1/odl/sessions?session_id={sid}` | no body |
| Get plan | `GET /api/v1/odl/sessions/{sid}/plan?command=...` | server planner (Phase 3) |
| Execute task | `POST /api/v1/ai/act` | body includes `session_id`, `task`, `args` |
| Get ODL text | `GET /api/v1/odl/sessions/{sid}/text` | optional; may be absent |
| Get ODL view | `GET /api/v1/odl/{sid}/view?layer=electrical` | fallback when `/text` is missing |

## Behavior changes
* `createOdlSession(id)` now uses the query-parameter form (no JSON body).
* `getPlanForSession()` prefers the server planner if present; otherwise emits a small client-side plan.
* `getOdlText()` falls back to `/view` and formats a minimal textual representation.
* `planAndRun(sessionId, command)` fetches a plan and executes each task via `POST /api/v1/ai/act`, refreshing the graph version after every step.

## Rationale
Keeps the UI responsive while the backend transitions, eliminates 422/404s on legacy routes,
and preserves export signatures so other modules compile without changes.
