# PNG Alignment Fix - Summary

## The Problem

PNG overlays were misaligned with OpenStreetMap tiles in Leaflet. Isle of Wight appeared over Milton Keynes (~170km north of its actual location).

## Root Cause

**Used Mercator coordinates for pixel calculation, but Leaflet uses WGS84**

The original code:
1. Converted BNG bounds → Web Mercator coordinates
2. Calculated pixel positions using Mercator Y coordinates (non-linear)
3. Saved bounds as WGS84 for Leaflet

The problem: **Leaflet's imageOverlay uses LINEAR WGS84 interpolation**, not Mercator!

### Example Error (Isle of Wight):
- **Expected position**: 50.7632°N, -1.2973°E
- **Actual position in Leaflet**: 50.6482°N (misplaced by 0.115° = 12.8km)

## The Fix

Calculate pixel positions using **WGS84 coordinates directly** (not Mercator):

### Before (WRONG):
```python
# Convert BNG to Mercator
merc_x, merc_y = bng_to_mercator.transform(bng_x, bng_y)

# Calculate pixel using Mercator coords
row = int((merc_y_max - merc_y) / (merc_y_max - merc_y_min) * IMG_HEIGHT)
col = int((merc_x - merc_x_min) / (merc_x_max - merc_x_min) * IMG_WIDTH)
```

### After (CORRECT):
```python
# For each pixel, calculate WGS84 coordinates (what Leaflet uses!)
lat = LAT_MAX - (row / (IMG_HEIGHT - 1)) * (LAT_MAX - LAT_MIN)
lng = LNG_MIN + (col / (IMG_WIDTH - 1)) * (LNG_MAX - LNG_MIN)

# Then convert WGS84 to BNG to look up data
bng_x, bng_y = wgs84_to_bng.transform(lng, lat)
```

## Verification

Test image with colored landmarks shows alignment error <0.006° (< 670m), which is just rounding error:

- **Isle of Wight**: Error 0.0016° lat, 0.0005° lng ✓
- **London**: Error 0.0002° lat, 0.0028° lng ✓
- **Edinburgh**: Error 0.0002° lat, 0.0051° lng ✓
- **Lizard Point**: Error 0.0006° lat, 0.0040° lng ✓

## Key Insight

**Leaflet's imageOverlay bounds are in WGS84 and use LINEAR interpolation in lat/lng space.**

If you need to display data in a projected coordinate system (like BNG or Mercator), you must:
1. Define your image bounds in WGS84
2. For each pixel, calculate its WGS84 lat/lng position
3. Transform that WGS84 position to your data's coordinate system
4. Look up the data value
5. Set the pixel color

Do NOT calculate pixels in the projected space and then hope Leaflet matches it!
