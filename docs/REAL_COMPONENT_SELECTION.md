# Real-vs-Placeholder Selection

The `LibrarySelector` service chooses between real library components and
generic placeholders when adding components to a design.  It provides a
deterministic, requirement-aware mechanism that favours real parts when they
fit the current design context.

## How it works

- For **panels** the selector scores candidates based on their `pmax_w` value
  and the remaining power gap of the design.
- For **inverters** it evaluates the AC rating against the total DC capacity
  and prefers models with more MPPTs.
- For other classes any model with attributes receives a mild preference.

The selector returns a tuple `(component_model_id, reason)`.  If
`component_model_id` is `None` the caller should create a `generic_<class>`
placeholder.

## Library integration

`LibrarySelector` expects a repository exposing
`list_models_by_class(component_class)` which returns dictionaries of the
form:

```python
{"id": "SKU123", "class": "panel", "attrs": {"pmax_w": 410}}
```

If the repository cannot be imported (e.g. during testing) the selector simply
falls back to placeholders.

## Telemetry

Callers are encouraged to attach the selector's decision and rationale to
their payloads under the `_selector` key for analytics and debugging.

