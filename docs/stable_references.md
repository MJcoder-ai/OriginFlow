# Stable references in ODL and the canvas

When working with OriginFlow’s Open Design Language (ODL) and the visual
canvas, it is critical to distinguish between **stable identifiers** and
**display names**:

* **Stable identifiers** include the component’s `id` (the primary key of
the schematic component) and its `standard_code` (typically the
manufacturer `part_number` that links the schematic component to the
master parts library). These identifiers are immutable and should be
used for all references in graphs, ODL definitions and client-side
state management. They do not change when the naming policy evolves or a
user edits the component’s name.
* **Display names** (the `name` field on the component model) are
human-friendly strings generated from datasheet metadata or edited by a
user. Names may change when the naming policy is updated or when a user
edits them in the review panel. Do **not** use display names as keys in
design graphs or as part of any persistent identifiers.

## Best practices

1. **Reference components by `id` and `standard_code` in ODL**. When
defining nodes in ODL scripts or when storing canvas state, always use
the component’s `id` and, where appropriate, its `standard_code` to
identify the part. For example:
   ```json
   {
     "node_id": "uuid-1234",
     "component_id": "cmp-5678",  // stable identifier
     "standard_code": "PN-425",    // links to the parts library
     "ports": [...],
     "metadata": { "name": "ACME ABC‑425 – 425 W Panel" }
   }
   ```
   Here, the `component_id` and `standard_code` link the node to the
   stored component and parts library. The `name` is included purely for
   display and should not be used as a lookup key.

2. **Update canvas labels when names change**. Client applications
   should subscribe to component updates (via a WebSocket, polling or a
   state management library) and refresh on-canvas labels when the
   `name` field changes. Because the `id` and `standard_code` remain
   constant, updating the label will not break connections or
   dependencies.

3. **Avoid encoding business logic in names**. Do not rely on the
   component’s name to convey functional information such as ratings or
   categories; instead, use the structured fields stored on the component
   model. Names are for human readability only.

4. **Persist only identifiers**. When saving designs or exporting ODL,
   store the component identifier and any other essential metadata (e.g.,
   part number, manufacturer, rating) separately. Regenerate names on the
   fly from the current naming policy if needed.

By following these guidelines, you ensure that updates to the naming
policy or manual name changes do not disrupt existing designs or
references on the canvas.
