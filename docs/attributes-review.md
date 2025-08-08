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
- Remove **Save** button; edits are auto-saved through `PATCH /attributes`.
- **Confirm & Close** posts to `POST /confirm-close` and closes the datasheet without triggering a re-parse.
- **Re-Analyse** is available from the toolbar and retains manually uploaded images.
- Images show star and trash icons with a clear **Primary** label.
- PDF and review panes hide scrollbars until hovered using the `.scroll-container` CSS helper and include zoom controls near page navigation.
- `ChatInputArea` recognises "confirm and close" or "confirm & close" to trigger the same confirmation flow.
- The toolbar features a subtly styled **Analyze** button, context-aware **Undo/Redo**, an **Export** button that downloads a CSV of current attributes, and a **Filter** placeholder.

## Data model highlights
- Canonical **Attribute Catalog** (labels, keys, units, types, synonyms, applicability).
- Versioned **ComponentAttributeValue** with provenance (`source_id`, `confidence`).
- `Confirm & Close` verifies the latest values and sets `is_human_verified=true` (no re-parse).

## Next steps
- Implement real repo/DB wiring inside services and route handlers.
- Populate the catalog from existing labels and synonyms.
- Feed the view endpoint with current value, candidates, and history count.
