# ODL (OriginFlow Design Language) — Minimal Text Format

This document describes the minimal canonical text format emitted by  
`GET /api/v1/odl/sessions/{sid}/text`.

```
node <id> : <type> [k1=v1 k2=v2 ...]
link <source> -> <target> [k1=v1 k2=v2 ...]
```

Notes
-----
- Attributes in `[...]` are optional and rendered in stable key order.
- The serializer currently includes: `layer`, `placeholder`, `x`, `y`.
- The text is a *projection* of a layer view. Use `/odl/{sid}/view?layer=...` for the full JSON.

Examples
--------
```
node inverter:r1:1 : inverter [layer=single-line placeholder=True x=120 y=120]
node panel:r2:1 : panel [layer=single-line placeholder=True x=300 y=120]
link inverter:r1:1 -> panel:r2:1 [layer=single-line]
```
