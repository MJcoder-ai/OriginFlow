# Attributes Review Panel & API

This document explains the new **Attributes Review** feature that replaces JSON-style metadata editing with a clean, one-row-per-attribute form backed by a canonical Attribute Catalog and versioned values.

## Backend additions
- `backend/schemas/attributes.py` — shared Pydantic schemas for view + patch + errors
- `backend/services/attribute_catalog_service.py` — normalization + catalog lookup (skeleton)
- `backend/routes/components_attributes.py` — new endpoints:
  - `GET /api/v1/components/{id}/attributes/view`
  - `PATCH /api/v1/components/{id}/attributes`
  - `POST /api/v1/components/{id}/confirm-close`
  - `POST /api/v1/components/{id}/reanalyze`

Add middleware for request IDs (optional but recommended):
- `backend/middleware/request_id.py` and wire in `backend/main.py`:

```python
from backend.middleware.request_id import request_id_middleware
app.middleware('http')(request_id_middleware)
```

## Frontend additions
- `frontend/src/services/attributesApi.ts` — API client
- `frontend/src/utils/debounce.ts` — small utility
- `frontend/src/components/AttributesReviewPanel.tsx` — UI panel

### Integration points
The review UI has changed to provide a cleaner, minimal experience:

- **Save** is removed; edits auto-save via `PATCH /attributes` with debounce.
- **Confirm & Close** is now located in the top toolbar.  It calls `POST /confirm-close` and is disabled until there are unsaved changes (including image changes).  Once confirmed, it clears the dirty flag and closes the datasheet without re-triggering parsing.
- **Re-Analyse** is removed from the datasheet footer.  The top **Analyze** button re-parses the current datasheet when a datasheet is open; otherwise it runs the usual design validation on the project canvas.  Reanalysis no longer closes the datasheet.
- The attributes panel hides vertical/horizontal scrollbars by default; they appear when the user hovers over the pane.  Containers use `overflow-auto scroll-container` with `min-h-0` so scrollbars render correctly.
- When the attributes API returns no rows (e.g. the catalog is not populated), an **editable raw data** fallback appears.  Each key/value from the original `parsed_payload` is editable; changes auto-save back to `/files/{id}` and mark the datasheet dirty.
- `ChatInputArea` recognises “confirm and close” or “confirm & close” to trigger the confirmation flow from chat.

Additional layout and styling notes:

- Labels now sit above each input, with lighter text for a cleaner look.
- Scrollbars reveal on hover with a slim 6px track and thumb.

## Data model highlights
- Canonical **Attribute Catalog** (labels, keys, units, types, synonyms, applicability).
- Versioned **ComponentAttributeValue** with provenance (`source_id`, `confidence`).
- `Confirm & Close` verifies the latest values and sets `is_human_verified=true` (no re-parse).

## Next steps
- Implement real repo/DB wiring inside services and route handlers.
- Populate the catalog from existing labels and synonyms.
- Feed the view endpoint with current value, candidates, and history count.
