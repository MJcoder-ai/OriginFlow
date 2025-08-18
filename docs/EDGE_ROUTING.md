# Orthogonal Edge Routing

This module routes wires orthogonally **after** node layout (ELK/Dagre/builtin).
It respects per-layer locks and persists waypoints so the ODL stays aligned.

## Providers
- **elk**: Uses an ELK HTTP service with `elk.edgeRouting=ORTHOGONAL`. Parses edge sections.
- **builtin**: Grid-based Manhattan router (Lee/BFS) with obstacle padding. Fast, stable.
- **client**: Frontend uses `elkjs` to produce sections; results are PATCHed to the server.

Configure in `backend/config.py` (or env):

```
EDGE_ROUTER_PROVIDER=elk|builtin|client
LAYOUT_HTTP_URL=http://localhost:7777/elk/layout   # required for elk
```

## Persistence
Each link stores waypoints per layer:

```json
path_by_layer: {
  "single_line": [ {"x":220,"y":140}, {"x":420,"y":140} ]
},
locked_in_layers: { "single_line": false }
```

## API
`POST /api/v1/layout/route?session_id=...&layer=single_line`

- Routes **unlocked** links on the given layer.
- Persists waypoints and triggers an ODL rebuild.
- Returns **501** if provider is `client` (frontend should route locally).

## ODL
When waypoints exist, ODL emits:

```
link P1 -> I1 route[(220,140) -> (420,140)]
```

## Recommended Flow
1. Run node layout (ELK/Dagre/builtin).
2. Persist positions and lock nodes as needed.
3. Run edge routing and persist waypoints.
4. ODL is rebuilt automatically on each mutation.

## Notes
- Only unlocked links are re-routed. Set `locked_in_layers[layer]=true` on a link to freeze its path.
- The builtin router uses a coarse grid; increase `GRID` or `PADDING` in `edge_router.py` for denser diagrams.

