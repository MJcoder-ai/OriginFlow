# OriginFlow Frontend Notes (Phase 2)

This UI is aligned to the OriginFlow backend API:

- Create sessions: `POST /api/v1/odl/sessions?session_id={sid}`
- Build plan (server): `GET /api/v1/odl/sessions/{sid}/plan?command=...`
- Execute tasks: `POST /api/v1/ai/act` (body includes `session_id`, `task`, `args`)
- ODL text: `GET /api/v1/odl/sessions/{sid}/text` (optional)
- ODL view: `GET /api/v1/odl/{sid}/view?layer=electrical` (fallback for text)

### Planner fallback
If the server planner returns 404/410 (or network error), the client synthesizes
a tiny plan for prompts like “design a 5kW solar PV system”:
1) `make_placeholders` (inverter)
2) `make_placeholders` (N panels)
3) `generate_wiring`

### Concurrency
Send `If-Match: <version>` with `act()` when you have it. The server enforces
optimistic concurrency; on 409, refetch the head/version and retry.
