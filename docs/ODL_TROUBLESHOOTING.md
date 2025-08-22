# Troubleshooting ODL Canvas and CORS Errors

When the canvas renders blank nodes or the browser shows CORS or 500 errors
for `/api/v1/odl/.../text` or `/view`, use this checklist to debug.

1. **CORS configuration (development)**
   Make sure the backend allows the frontend origin:
   ```bash
   export ORIGINFLOW_CORS_ORIGINS="http://localhost:8082,http://127.0.0.1:8082,*"
   poetry run uvicorn backend.main:app --reload --host 0.0.0.0
   ```
2. **Create a session**
   ```bash
   curl -s -X POST 'http://localhost:8000/api/v1/odl/sessions?session_id=demo'
   ```
3. **Plan and apply nodes**
   ```bash
   curl -s -X POST 'http://localhost:8000/api/v1/ai/act' \
     -H 'Content-Type: application/json' -H 'If-Match: 1' \
     -d '{"session_id":"demo","task":"make_placeholders","request_id":"r1",
          "args":{"component_type":"inverter","count":1,"layer":"single-line"}}'
   ```
4. **Verify view positions**
   ```bash
   curl -s 'http://localhost:8000/api/v1/odl/demo/view?layer=single-line' | jq '.nodes[0]'
   ```
   Each node should include a `pos: {x,y}` block, which the backend computes on
   the fly if missing.
5. **ODL text endpoint**
   ```bash
   curl -s -i 'http://localhost:8000/api/v1/odl/sessions/demo/text?layer=single-line'
   ```
   The response should be `200` and contain either canonical or fallback text.

If any step fails, tail the backend logs. The serializer and layout helpers are
resilient, so persistent errors usually point to deeper store or data issues.
