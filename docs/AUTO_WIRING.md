# Auto-Wiring (Professional)

The auto-wiring module analyses the current design snapshot, determines which
electrical links are missing and creates them deterministically.  Existing
links are never duplicated, making the operation safe to repeat.

## Behaviour

- Panels and batteries are connected to their nearest inverter.
- Generated links are routed using the orthogonal edge router and persisted.
- The ODL representation is rebuilt after wiring to keep the textual model in
  sync with the canvas.

## API

```
POST /api/v1/layout/wire?session_id=...
```

The endpoint returns the number of links created and routed:

```json
{"layer": "single_line", "created_links": 2, "routed": 2}
```

## Extending rules

The allowable connections are defined by `ALLOWED_EDGES` in
`backend/services/wiring.py`.  Additional domain-specific rules can be added
by extending this set or replacing the pairing logic in
`plan_missing_wiring`.

