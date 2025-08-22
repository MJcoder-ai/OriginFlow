# ODL Canvas Debug Guide

## Overview
This guide explains the new ODL-to-canvas bridge system that should resolve the empty canvas issue.

## What's New

### 1. Auto-Layout System (`backend/odl/layout.py`)
- Automatically positions nodes that don't have coordinates
- Uses a grid layout system (220px x 160px spacing)
- Non-destructive - doesn't modify the original ODL data

### 2. Enhanced Error Handling
- `/text` endpoint no longer crashes with 500 errors
- Fallback text synthesis when serializer fails
- Comprehensive logging for debugging

### 3. ODL Bridge Endpoints
- `/api/v1/odl/{session_id}/components` - Converts ODL nodes to canvas components
- `/api/v1/odl/{session_id}/links` - Converts ODL edges to canvas links
- `/api/v1/odl/{session_id}/debug` - Detailed debugging information

## How It Works

### Data Flow
1. ODL data is stored in the backend database
2. Frontend calls `/api/v1/odl/{session_id}/components` instead of `/api/v1/components/`
3. Backend converts ODL nodes to component format with positions
4. Canvas renders the components using the position data

### Auto-Positioning
- If ODL nodes have `pos: {x, y}` or separate `x`, `y` attributes, they're used
- If no positions exist, the layout system creates a grid automatically
- Positions are calculated on-the-fly and don't persist to the database

## Debugging Your Canvas

### 1. Check the Debug Endpoint
```bash
curl "http://localhost:8000/api/v1/odl/YOUR_SESSION_ID/debug?layer=single-line"
```

This returns:
- Total nodes/edges in the graph
- Nodes/edges in the current layer
- Sample positions
- Fallback text synthesis

### 2. Check Backend Logs
The backend now logs detailed information:
```
ODL /view sid=abc layer=single-line nodes=5 edges=3
ODL /components bridge sid=abc layer=single-line nodes=5
```

### 3. Browser Console
The frontend logs component loading:
```
Loaded 5 components and 3 links from ODL
```

### 4. Test Endpoints Directly
```bash
# Check if ODL data exists
curl "http://localhost:8000/api/v1/odl/YOUR_SESSION_ID/view?layer=single-line"

# Check component conversion
curl "http://localhost:8000/api/v1/odl/YOUR_SESSION_ID/components?layer=single-line"

# Check link conversion
curl "http://localhost:8000/api/v1/odl/YOUR_SESSION_ID/links?layer=single-line"
```

## Common Issues & Solutions

### Issue: Canvas Still Empty
**Check:**
1. Does the debug endpoint show nodes in the layer?
2. Are the components being loaded (check browser console)?
3. Do the nodes have positions?

**Solutions:**
1. Verify the session ID is correct
2. Check if nodes have the right layer attribute
3. Use the debug endpoint to see what's happening

### Issue: Nodes Overlapping
The auto-layout uses a 220x160 grid. If you need different spacing, you can:
1. Modify the `ensure_positions` function in `backend/odl/layout.py`
2. Add explicit positions to your ODL nodes

### Issue: Wrong Node Types
The canvas may filter certain node types. Check:
1. What types are in your ODL data (debug endpoint)
2. What types the canvas renderer expects
3. The `_render` hints in the component data

## Testing the System

You can test the system with the provided test script:
```bash
cd backend
python test_odl_endpoints.py
```

## Migration Notes

### For Existing Users
- The system automatically falls back to legacy endpoints if ODL data isn't available
- No changes needed to existing workflows
- Canvas should start working immediately with ODL data

### For Developers
- ODL data is now the primary source of truth
- Legacy components/links endpoints still work for non-ODL data
- Debug endpoints provide detailed troubleshooting information

## Troubleshooting Checklist

1. ✅ Check session ID is valid
2. ✅ Verify ODL data exists (`/debug` endpoint)
3. ✅ Check layer filtering (nodes should have `attrs.layer` matching the view layer)
4. ✅ Verify positions are being generated
5. ✅ Check browser console for loading messages
6. ✅ Verify CORS is working (no more 500 errors)
7. ✅ Check backend logs for detailed information

If the canvas is still empty after checking these, the debug endpoint will show exactly what's happening with your data.
