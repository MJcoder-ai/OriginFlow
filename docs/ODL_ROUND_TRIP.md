# ODL Round-Trip (Single Source of Truth)

OriginFlow maintains a textual **Origin Design Language (ODL)** representation
alongside the interactive canvas.  The round-trip flow ensures both remain
aligned so that either can act as the authoritative source.

## Flow

1. **Canvas → ODL**: the existing `odl_compiler` emits layer, component
   coordinates and routed link paths.
2. **ODL → Canvas**: `parse_odl_text` reads ODL back into a
   `DesignSnapshot` structure.
3. **Authoritative update**: `/api/v1/odl/set` applies an ODL text snippet to
   a session.  Positions and routes are updated for matching IDs and new links
   are created.  In `replace` mode, missing components are also created.
4. After applying changes, the canonical ODL is rebuilt to avoid drift.

## Grammar subset

```
# Layer: single_line
panel P1 at(layer="single_line", x=220, y=140)
inverter I1 at(layer="single_line", x=420, y=140)
link P1 -> I1 route[(220,140) -> (420,140)]
```

Positions set via ODL lock the corresponding layer in the component's
`locked_in_layers` mapping to prevent automatic layout engines from moving
them unexpectedly.

