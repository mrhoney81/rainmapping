# Leaflet Version - Dynamic Overlay Map

This is a new version of the UK Climate Viewer using Leaflet with OpenStreetMap tiles and dynamic data overlays instead of pre-rendered raster images.

## Key Features

### Dynamic Rendering
- Uses Leaflet.js with OSM tiles (no account required)
- Renders 1x1km grid cells as dynamic overlays
- Supports British National Grid (EPSG:27700) coordinate system
- Efficient gzip-compressed JSON data format

### Data Visualization
- **Temperature**: Absolute scale from -10°C to +32°C (reasonable UK range)
  - Uses 10-color gradient from cold (blue) to hot (red)
  - Scale based on Woolhampton as reference location

- **Rain/Sun**: Bivariate color scheme
  - 3x3 color matrix showing rainfall vs sunshine
  - Classifies data into low/medium/high categories using percentiles

### Controls
- **Opacity Slider**: Adjust overlay transparency (0-100%)
- **Time Navigation**: Select year (2021-2023) and month
- **Data Type Toggle**: Switch between Rain/Sun and Temperature views
- **Zoom Limits**: Constrained to appropriate levels for 1km resolution

## File Structure

```
leaflet.html          - Main HTML file with UI
leaflet-app.js        - JavaScript application
extract_data.py       - Data extraction script
leaflet_data/         - Extracted data (gitignored)
  ├── metadata.json   - Dataset metadata
  ├── temp/           - Temperature data (gzipped JSON)
  ├── rain/           - Rainfall data (gzipped JSON)
  └── sun/            - Sunshine data (gzipped JSON)
```

## Data Format

Data is stored in a sparse format as gzipped JSON:
```json
{
  "x_coord": {
    "y_coord": value
  }
}
```

Where coordinates are British National Grid easting/northing in meters, representing cell centers.

## Performance Optimizations

1. **Sparse Data Structure**: Only non-null cells are stored
2. **Gzip Compression**: ~530KB per month compressed
3. **Data Caching**: Recently loaded months cached in memory
4. **Coordinate Conversion**: Efficient BNG→WGS84 using proj4.js
5. **Zoom Limits**: Prevents excessive rendering at inappropriate scales

## Usage

### Development Server

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/leaflet.html`

### Extract Full Dataset

To process the full dataset from 2010-2023, edit `extract_data.py`:

```python
YEARS_TO_PROCESS = list(range(2010, 2024))
```

Then run:

```bash
python3 extract_data.py
```

This will generate approximately 2.5GB of compressed data.

## Technical Details

### Coordinate Systems

- **Source Data**: British National Grid (EPSG:27700)
- **Map Display**: WGS84 (EPSG:4326) → Web Mercator (EPSG:3857)
- **Conversion**: proj4.js handles accurate transformation

### Rendering Approach

Each 1km cell is rendered as a Leaflet Rectangle:
- Cell center coordinates converted from BNG to lat/lng
- ±500m offset creates 1km square
- Rectangles grouped in LayerGroup for efficient management

### Color Mapping

**Temperature**: Linear interpolation across 10-color gradient
```
-10°C (dark blue) → +32°C (dark red)
```

**Rain/Sun**: 3x3 bivariate matrix
```
           Less Sun    Medium Sun    More Sun
More Rain   #509dc2    #376387       #000000
Med Rain    #b4d3e1    #b3b3b3       #b36600
Less Rain   #f3f3f3    #f3e6b3       #f3b300
```

## Differences from Original Version

### Original (Raster Images)
- Pre-rendered PNG images (900x1450 pixels)
- Fixed color mapping
- Static zoom and pan on canvas
- ~45-75KB per image
- All years pre-generated

### New (Leaflet Overlays)
- Dynamic vector overlays
- Adjustable opacity
- True geographic map with OSM tiles
- ~530KB per month (compressed)
- Generate only years needed
- Better projection handling
- Zoom constraints appropriate for data resolution

## Future Enhancements

- [ ] Add location markers and labels
- [ ] Implement monthly averages
- [ ] Add playback/animation mode
- [ ] Support for additional data layers
- [ ] Mobile touch optimization
- [ ] Export/share functionality
- [ ] Performance profiling and optimization

## Data Source

CEDA HADUKGrid 1km dataset
- Temperature: tasmax (maximum temperature)
- Rainfall: monthly totals (mm)
- Sunshine: monthly totals (hours)

## Notes

- Zoom is limited (5-11) to prevent performance issues with 245k+ cells
- Data is gitignored to keep repository size manageable
- Requires modern browser with ES6 support
- proj4.js and proj4leaflet handle coordinate transformations
