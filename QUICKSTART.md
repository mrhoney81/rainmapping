# Quick Start Guide - Leaflet Version

## Current Status

✅ **Working Features:**
- Leaflet map with OSM tiles
- Dynamic 1x1km grid overlay rendering
- Temperature visualization (-10°C to +32°C absolute scale)
- Rain/Sun bivariate visualization
- Opacity controls
- Year/month selection (2021-2023)
- Data cached and compressed (78MB total)

## How to Use

### 1. Start Local Server

```bash
python3 -m http.server 8000
```

### 2. Open in Browser

Navigate to: `http://localhost:8000/leaflet.html`

### 3. Controls

- **Data Type**: Toggle between Rain/Sun and Temperature
- **Year/Month**: Use sliders to select time period
- **Opacity**: Adjust overlay transparency
- **Map**: Drag to pan, scroll to zoom

## Extending to Full Dataset (2010-2023)

Currently configured for 2021-2023 (3 years). To process full dataset:

### Step 1: Edit extract_data.py

Change line 23:
```python
YEARS_TO_PROCESS = list(range(2010, 2024))  # Full dataset
```

### Step 2: Ensure Source Data Available

You'll need NetCDF files in:
- `temp_data/` for temperature (2010-2023)
- `rain_sun_data/` for rainfall and sunshine (2010-2023)

### Step 3: Run Extraction

```bash
python3 extract_data.py
```

This will:
- Process 13 years × 12 months × 3 variables = 468 files
- Generate ~2.5GB of compressed data
- Take approximately 10-15 minutes

### Step 4: Update Leaflet HTML

Edit `leaflet.html` line with year slider:
```html
<input type="range" id="yearSlider" min="2010" max="2023" value="2023">
```

Also update `leaflet-app.js` line 52:
```javascript
let currentYear = 2023;
```

## Performance Notes

### Current (2021-2023):
- 108 data files
- 78MB total
- ~530KB per month
- Loads in <500ms per month

### Full Dataset (2010-2023):
- 468 data files
- ~2.5GB total
- Same per-month size
- Similar load times (caching helps)

### Rendering Performance:
- 245,077 cells per dataset
- Rendered as Leaflet rectangles
- Zoom limited to 5-11 for performance
- Layer group management for efficiency

## Technical Details

### Data Format
Sparse coordinate-based JSON (gzipped):
```json
{
  "x_easting": {
    "y_northing": value
  }
}
```

### Coordinate Systems
- **Source**: British National Grid (EPSG:27700)
- **Display**: WGS84 → Web Mercator via proj4.js
- **Cell Size**: 1km × 1km squares

### Color Schemes

**Temperature**: 10-color gradient
- Range: -10°C (dark blue) to +32°C (dark red)
- Linear interpolation

**Rain/Sun**: 3×3 bivariate matrix
- Percentile-based classification
- Rain: vertical axis (blue tones)
- Sun: horizontal axis (yellow tones)

## Troubleshooting

### Map Not Loading
- Check browser console (F12)
- Ensure server is running
- Check data files exist in `leaflet_data/`

### Missing Data
- Verify NetCDF files in source directories
- Re-run `extract_data.py`
- Check file permissions

### Performance Issues
- Reduce zoom level
- Clear browser cache
- Check system memory (245k cells is intensive)

### Coordinate Errors
- Ensure proj4.js loaded
- Check console for projection errors
- Verify EPSG:27700 definition

## Files Structure

```
├── leaflet.html              # Main interface
├── leaflet-app.js            # Application logic
├── extract_data.py           # Data extraction script
├── LEAFLET_VERSION.md        # Detailed documentation
├── QUICKSTART.md            # This file
└── leaflet_data/            # Generated data (gitignored)
    ├── metadata.json        # Dataset info
    ├── temp/               # Temperature files
    ├── rain/               # Rainfall files
    └── sun/                # Sunshine files
```

## Next Steps

1. ✅ Basic implementation complete
2. ⏳ Test with more years
3. ⏳ Add location markers
4. ⏳ Implement playback/animation
5. ⏳ Mobile optimization
6. ⏳ Add export functionality

## Comparison with Original

| Feature | Original | Leaflet Version |
|---------|----------|-----------------|
| Base Map | None | OSM tiles |
| Data Format | PNG images | JSON overlays |
| File Size | 45-75KB/image | 530KB/month |
| Rendering | Canvas | Leaflet vectors |
| Projection | BNG canvas | True geographic |
| Opacity | Fixed | Adjustable |
| Zoom | Pan/zoom | True map zoom |
| Performance | Fast | Good (245k cells) |

## Support

For issues or questions:
- Check LEAFLET_VERSION.md for technical details
- Review browser console for errors
- Verify data extraction completed successfully
