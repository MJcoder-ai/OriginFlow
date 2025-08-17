# Naming policy management

OriginFlow uses a **naming policy** to generate human‑friendly names for
components based on metadata extracted from datasheets. The policy
consists of a **template string** and a **version number**. The template
defines how fields such as `manufacturer`, `part_number`, `rating` and
`category` are combined to form the component’s name, and the version
allows teams to track changes in naming conventions over time.

## API endpoints

Administrators can view and update the naming policy via the following
RESTful endpoints, introduced in `backend/api/routes/naming_policy.py`.

### Retrieve the current policy

`GET /naming-policy`

Returns the active naming policy as a JSON object with `template` and
`version` fields. Use this endpoint to display the current policy in
administrative UIs or verify that a newly updated policy has taken
effect.

Example response:

```json
{
  "template": "{manufacturer} {part_number} – {rating} {category}",
  "version": 1
}
```

### Update the naming policy

`PUT /naming-policy`

Allows administrators to change the format string and version used to
construct component names. The request body must contain a `template`
and `version` and may include `apply_to_existing`. When
`apply_to_existing` is `true`, OriginFlow will iterate through all
existing components and regenerate their `name` fields using the new
policy. This operation can be time‑consuming on large datasets.

Example request:

```json
{
  "template": "{manufacturer} {part_number} – {rating} {series_name} {category}",
  "version": 2,
  "apply_to_existing": true
}
```

Example response:

```json
{
  "template": "{manufacturer} {part_number} – {rating} {series_name} {category}",
  "version": 2
}
```

### Notes

- Changing the naming policy does **not** affect the stable identifiers
  (`id` and `standard_code`/`part_number`) used by OriginFlow’s ODL
  graph and canvas. Only the human‑friendly display name is updated.
- If you plan to update the naming policy frequently, consider using
  `apply_to_existing=false` and running the migration script separately
  to avoid blocking API responses. See below for details.
- Authentication and authorisation are not implemented in the example
  code; in a production deployment, protect these endpoints so only
  authorised users can modify the naming policy.

### Stable references

Changing the naming policy affects only the **display name** of a
component. The underlying identifiers (`id` and `standard_code` or
manufacturer `part_number`) do not change. When working with ODL or the
canvas, always use these stable identifiers for references and keys.
Display names can change when the naming policy is updated or when a
user edits the name, but the identifiers remain constant. For guidelines
on using stable identifiers and updating labels when names change, see
`docs/stable_references.md`.

## Running the migration script manually

For deployments with large numbers of components or restricted
maintenance windows, you can regenerate component names outside of
the HTTP request cycle by running the provided script:

```
python -m backend.scripts.update_component_names
```

This script opens a database session and calls
`update_existing_component_names` to recalculate the `name` field for
every component using the current naming policy. Run this script after
updating the policy if you did not specify `apply_to_existing=true` in
the API call.

## Related modules

- `backend/config.py`: Stores the naming policy defaults (`component_name_template` and
  `component_naming_version`), which can be overridden via environment
  variables or updated through the API.
- `backend/services/component_naming_policy.py`: Provides a helper to
  retrieve the active naming policy.
- `backend/services/component_naming_service.py`: Applies the naming
  policy to datasheet metadata during parsing and variant splitting.
- `backend/services/component_name_migration.py`: Contains the
  `update_existing_component_names` function used to reapply the naming
  policy to existing component records.
