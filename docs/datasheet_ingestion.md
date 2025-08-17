# Datasheet Ingestion

When a PDF datasheet is parsed successfully, OriginFlow now performs two actions:

1. **Update ComponentMaster** – The parsed metadata (part number, manufacturer, 
   category, ratings, etc.) is inserted or updated in the `component_master` 
   table.
2. **Populate AI Component Library** – The same component is ingested through
   `ComponentDBService`, making it immediately available to AI agents. This
   allows gather steps to detect newly uploaded components and continue without
   manual refresh.

Errors during ingestion are logged but do not interrupt the parsing workflow.

## Naming policy for new components

To make parsed components easy to search and filter, OriginFlow automatically
generates a human-friendly name for each component using a configurable naming
policy. The naming policy is defined in `backend/config.py` via the
`component_name_template` and `component_naming_version` settings. The template
is a Python format string containing placeholders (e.g. `{manufacturer}`,
`{part_number}`, `{rating}`, `{category}`, `{series_name}`) that are filled with
metadata extracted from the datasheet. You can change this template through
environment variables or a future API without modifying code, allowing the
naming convention to evolve over time. See
`backend/services/component_naming_policy.py` for a helper that returns the
current naming policy.

