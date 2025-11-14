# Data Directory

This directory should contain the pre-generated climate visualization images.

## Required Structure

After running the preprocessing script (see `../plan.md`), copy the contents of your `web_output` directory here:

```
data/
├── images/
│   ├── 2014/
│   │   ├── 01.png (January 2014)
│   │   ├── 02.png (February 2014)
│   │   └── ... (through 12.png)
│   ├── 2015/
│   │   └── ... (01.png through 12.png)
│   └── ... (through 2023)
├── averages/
│   ├── 01.png (January average across all years)
│   ├── 02.png (February average)
│   └── ... (through 12.png)
├── key.png (Bivariate color legend with white background)
├── key_transparent.png (Bivariate color legend with transparent background)
├── metadata.json (Geographic extent and image metadata)
└── locations.json (UK settlements - already provided)
```

## How to Add Your Data

If you've already run the preprocessing script and have a `web_output` directory:

```bash
# From the project root directory
cp -r web_output/* data/
```

Or manually:

1. Copy `web_output/images/` to `data/images/`
2. Copy `web_output/averages/` to `data/averages/`
3. Copy `web_output/key.png` to `data/key.png`
4. Copy `web_output/key_transparent.png` to `data/key_transparent.png`
5. Copy `web_output/metadata.json` to `data/metadata.json`

## File Size Expectations

- **Each monthly image**: ~300-800 KB (PNG, optimized)
- **Total images**: 120 monthly + 12 averages = 132 images
- **Total size**: ~70 MB

## Metadata Format

The `metadata.json` file should contain:

```json
{
  "extent": {
    "x_min": 0,
    "x_max": 700000,
    "y_min": 0,
    "y_max": 1300000,
    "crs": "EPSG:27700",
    "resolution_meters": 1000
  },
  "image_dimensions": {
    "width": 700,
    "height": 1300
  },
  "years": [2014, 2015, ..., 2023],
  "months": [1, 2, ..., 12],
  "colors": [...],
  "data_source": "CEDA HADUKGrid 1km"
}
```

## Troubleshooting

### Images not showing up?

1. Check that files are named correctly: `01.png`, `02.png`, etc. (with leading zeros)
2. Verify the directory structure matches exactly
3. Ensure `metadata.json` is valid JSON
4. Check browser console for 404 errors

### Need to regenerate images?

See the preprocessing script in `../plan.md` for complete instructions on generating images from CEDA NetCDF data.
