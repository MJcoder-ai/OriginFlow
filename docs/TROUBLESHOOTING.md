# OriginFlow Troubleshooting: Canvas empty / ODL 500 / CORS

**Symptoms**
- Browser console shows 500 on `/api/v1/odl/.../text` or `/view`.
- “No 'Access-Control-Allow-Origin' header” appears (this is secondary to 500s).
- ODL panel blank and canvas empty.

**Checklist**
1. Backend with permissive CORS (dev only):
   ```bash
   export ORIGINFLOW_CORS_ORIGINS="*"
   poetry run uvicorn backend.main:app --reload --host 0.0.0.0
   ```
2. Create a session:
   ```bash
   curl -s -X POST 'http://localhost:8000/api/v1/odl/sessions?session_id=demo'
   ```
3. Apply a simple action (If-Match must be current version):
   ```bash
   curl -s -X POST 'http://localhost:8000/api/v1/ai/act' \
     -H 'Content-Type: application/json' -H 'If-Match: 1' \
     -d '{"session_id":"demo","task":"make_placeholders","request_id":"r1",\
          "args":{"component_type":"panel","count":12,"layer":"single-line"}}'
   ```
4. Verify `/view` has nodes and positions:
   ```bash
   curl -s 'http://localhost:8000/api/v1/odl/demo/view?layer=single-line' | jq '.nodes[0]'
   ```
5. Verify `/text` never 500s (canonical or fallback text is fine):
   ```bash
   curl -s -i 'http://localhost:8000/api/v1/odl/sessions/demo/text?layer=single-line'
   ```

If you still get an empty canvas but `/view` returns nodes, check layer labels:
```
curl -s 'http://localhost:8000/api/v1/odl/demo/view?layer=single-line' \
| jq '.nodes[].attrs.layer' | sort | uniq -c
```
If everything is `"electrical"`, either switch the UI layer or update the planner to
write to `"single-line"`. This repo defaults the `attrs.layer` to the requested layer
when missing, purely for rendering.
