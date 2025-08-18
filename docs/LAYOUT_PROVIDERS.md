# Layout Providers (ELK / Dagre / Builtin)

This project supports three layout providers for node placement:

- **ELK** (preferred): high-quality layered layout via an external HTTP ELK service.
- **Dagre** (client fallback): in-browser layered layout using dagre.
- **Builtin**: simple, stable layered fallback implemented server-side.

## Configuration
In `backend/config.py` (or via environment):
```
LAYOUT_PROVIDER=elk|dagre|builtin
LAYOUT_HTTP_URL=http://localhost:7777/elk/layout  # required for elk
```

### ELK HTTP Service
Run any ELK HTTP bridge that accepts the standard ELK JSON payload and returns node `x/y`:
```json
{
  "id": "root",
  "layoutOptions": { "elk.algorithm": "layered", "elk.direction": "RIGHT" },
  "children": [{ "id":"c1","width":120,"height":72,"x":100,"y":100,"properties":{"org.eclipse.elk.fixed":true }}, ...],
  "edges": [{ "id":"e_c1_c2","sources":["c1"],"targets":["c2"] }]
}
```
**Locked nodes** include `x/y` and `"org.eclipse.elk.fixed": true` and are not moved.

### Dagre (client)
The frontend uses `elkjs` if available, else `dagre` to compute LR layered positions.
After layout, the client updates UNLOCKED nodes by `PATCH /api/v1/components/{id}` with:
```json
{ "layout": { "<layer>": { "x": 220, "y": 140 } }, "locked_in_layers": { "<layer>": true } }
```

## API
`GET /api/v1/layout/suggest?session_id=...&layer=single_line`
Returns:
```json
{ "layer": "single_line", "positions": { "nodeId": { "x": 220, "y": 140 }, ... } }
```
For `dagre` provider the server replies 501, indicating the client should perform layout locally.

## Notes
- Only **UNLOCKED** nodes are suggested/moved. Locked nodes remain where the user placed them.
- After any topology mutation (add/delete/link), call layout again and persist nodes you want fixed on that layer.
- For high-end orthogonal routing of edges, pair ELK with an orthogonal router (client or server).
