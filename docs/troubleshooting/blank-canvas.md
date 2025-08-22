## Canvas renders nothing, ODL tab shows nodes

**Symptom**: ODL Code tab shows nodes/versions increasing, but the Single-Line canvas is empty.

**Checklist**
1. Confirm the frontend is requesting the view: look for `GET /api/v1/odl/{sid}/view?layer=...` in backend logs.
2. If only `/text` is hit, wire the UI to call `/view` when the active layer or `graphVersion` changes.
3. Ensure nodes have positions: backend should include `position` (and `pos`) for each node.
4. If you’ve added new node types, verify the canvas registers them or falls back to a default node.
5. Use `curl` to sanity-check:
   ```bash
   curl -s "http://localhost:8000/api/v1/odl/<sid>/view?layer=single-line" | jq '.nodes | length'
   ```
   A non-zero value means data exists; focus on the frontend.

