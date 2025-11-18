#!/usr/bin/env python3
"""
Generate PNGs for Leaflet - CORRECT VERSION
Uses WGS84 coordinates for pixel calculation (not Mercator!)
"""

import numpy as np
from PIL import Image
import pyproj
import json
import gzip
from pathlib import Path
import os

print("=" * 70)
print("GENERATE PNGS FOR LEAFLET (FIXED)")
print("=" * 70)

# Configuration
DATA_DIR = "leaflet_data"
OUTPUT_DIR = "leaflet_pngs"
YEARS = [2021, 2022, 2023]

# Output image size
IMG_WIDTH = 2000
IMG_HEIGHT = 3000

# Temperature colors
TEMP_COLORS = [
    (5, 48, 97), (33, 102, 172), (67, 147, 195), (146, 197, 222), (209, 229, 240),
    (253, 219, 199), (244, 165, 130), (214, 96, 77), (178, 24, 43), (103, 0, 31)
]

# Bivariate colors
BIVARIATE_COLORS = {
    (0,0): (243, 243, 243), (0,1): (243, 230, 179), (0,2): (243, 179, 0),
    (1,0): (180, 211, 225), (1,1): (179, 179, 179), (1,2): (179, 102, 0),
    (2,0): (80, 157, 194), (2,1): (55, 99, 135), (2,2): (0, 0, 0)
}

os.makedirs(f"{OUTPUT_DIR}/temp", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/rain_sun", exist_ok=True)

# Setup projection transformers
bng_to_wgs84 = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
wgs84_to_bng = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

print("\n" + "=" * 70)
print("STEP 1: DETERMINE BOUNDS")
print("=" * 70)

# Use standard UK bounds in BNG
bng_x_min, bng_y_min = 0, 0
bng_x_max, bng_y_max = 700000, 1250000

# Convert to WGS84 for Leaflet
sw_lng, sw_lat = bng_to_wgs84.transform(bng_x_min, bng_y_min)
ne_lng, ne_lat = bng_to_wgs84.transform(bng_x_max, bng_y_max)

LAT_MIN = sw_lat
LAT_MAX = ne_lat
LNG_MIN = sw_lng
LNG_MAX = ne_lng

print(f"BNG bounds: ({bng_x_min}, {bng_y_min}) to ({bng_x_max}, {bng_y_max})")
print(f"WGS84 bounds: [[{LAT_MIN:.4f}, {LNG_MIN:.4f}], [{LAT_MAX:.4f}, {LNG_MAX:.4f}]]")

print("\n" + "=" * 70)
print("STEP 2: GENERATING IMAGES")
print("=" * 70)
print(f"Image size: {IMG_WIDTH}x{IMG_HEIGHT}")
print("\nKEY CHANGE: Using WGS84 for pixel calculation (not Mercator)!")
print("  - Leaflet's imageOverlay uses LINEAR WGS84 interpolation")
print("  - So we must calculate pixels using WGS84 coordinates\n")

def load_data(year, month, data_type):
    """Load gzipped JSON data"""
    filename = f"{DATA_DIR}/{data_type}/{year}_{month:02d}.json.gz"
    try:
        with gzip.open(filename, 'rt') as f:
            return json.load(f)
    except:
        return None

def get_color_for_temp(temp, min_t=-10, max_t=32):
    """Get RGB color for temperature"""
    normalized = (temp - min_t) / (max_t - min_t)
    clamped = max(0, min(1, normalized))
    idx = min(int(clamped * (len(TEMP_COLORS) - 1)), len(TEMP_COLORS) - 1)
    return TEMP_COLORS[idx]

def get_color_for_rain_sun(rain, sun, rain33, rain66, sun33, sun66):
    """Get RGB color for rain/sun bivariate"""
    rain_level = 0 if rain < rain33 else (1 if rain < rain66 else 2)
    sun_level = 0 if sun < sun33 else (1 if sun < sun66 else 2)
    return BIVARIATE_COLORS[(rain_level, sun_level)]

def generate_temp_image(year, month):
    """Generate temperature PNG using WGS84 coordinates"""
    print(f"  Temp {year}-{month:02d}...", end=' ', flush=True)

    temp_data = load_data(year, month, 'temp')
    if not temp_data:
        print("SKIP")
        return

    # Create image array
    img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

    # For each pixel, map to WGS84 coordinates (what Leaflet uses!)
    for row in range(IMG_HEIGHT):
        for col in range(IMG_WIDTH):
            # Leaflet imageOverlay uses LINEAR WGS84 interpolation:
            #   row 0 → LAT_MAX (north)
            #   row IMG_HEIGHT-1 → LAT_MIN (south)
            #   col 0 → LNG_MIN (west)
            #   col IMG_WIDTH-1 → LNG_MAX (east)

            lat = LAT_MAX - (row / (IMG_HEIGHT - 1)) * (LAT_MAX - LAT_MIN)
            lng = LNG_MIN + (col / (IMG_WIDTH - 1)) * (LNG_MAX - LNG_MIN)

            try:
                # Convert WGS84 → BNG
                bng_x, bng_y = wgs84_to_bng.transform(lng, lat)

                # Round to nearest km (our data resolution)
                x_key = str(int(round(bng_x / 1000) * 1000))
                y_key = str(int(round(bng_y / 1000) * 1000))

                # Look up data
                if x_key in temp_data and y_key in temp_data[x_key]:
                    temp = temp_data[x_key][y_key]
                    r, g, b = get_color_for_temp(temp)
                    img_array[row, col] = [r, g, b, 255]
            except:
                pass  # Outside bounds

    # Save PNG (no flip needed!)
    img = Image.fromarray(img_array, 'RGBA')
    img.save(f"{OUTPUT_DIR}/temp/{year}_{month:02d}.png", optimize=True)
    print("✓")

def generate_rain_sun_image(year, month):
    """Generate rain/sun bivariate PNG using WGS84 coordinates"""
    print(f"  Rain/Sun {year}-{month:02d}...", end=' ', flush=True)

    rain_data = load_data(year, month, 'rain')
    sun_data = load_data(year, month, 'sun')

    if not rain_data or not sun_data:
        print("SKIP")
        return

    # Calculate percentiles for binning
    rain_values = [v for x in rain_data.values() for v in x.values()]
    sun_values = [v for x in sun_data.values() for v in x.values()]
    rain_values.sort()
    sun_values.sort()

    n = len(rain_values)
    rain33 = rain_values[n // 3] if n > 0 else 0
    rain66 = rain_values[(2 * n) // 3] if n > 0 else 0

    n = len(sun_values)
    sun33 = sun_values[n // 3] if n > 0 else 0
    sun66 = sun_values[(2 * n) // 3] if n > 0 else 0

    # Create image array
    img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

    # For each pixel, map to WGS84 coordinates
    for row in range(IMG_HEIGHT):
        for col in range(IMG_WIDTH):
            lat = LAT_MAX - (row / (IMG_HEIGHT - 1)) * (LAT_MAX - LAT_MIN)
            lng = LNG_MIN + (col / (IMG_WIDTH - 1)) * (LNG_MAX - LNG_MIN)

            try:
                # Convert WGS84 → BNG
                bng_x, bng_y = wgs84_to_bng.transform(lng, lat)

                # Round to nearest km
                x_key = str(int(round(bng_x / 1000) * 1000))
                y_key = str(int(round(bng_y / 1000) * 1000))

                # Look up data
                if x_key in rain_data and y_key in rain_data[x_key]:
                    if x_key in sun_data and y_key in sun_data[x_key]:
                        rain = rain_data[x_key][y_key]
                        sun = sun_data[x_key][y_key]
                        r, g, b = get_color_for_rain_sun(rain, sun, rain33, rain66, sun33, sun66)
                        img_array[row, col] = [r, g, b, 255]
            except:
                pass

    # Save PNG
    img = Image.fromarray(img_array, 'RGBA')
    img.save(f"{OUTPUT_DIR}/rain_sun/{year}_{month:02d}.png", optimize=True)
    print("✓")

# Generate all images
for year in YEARS:
    print(f"\nYear {year}:")
    for month in range(1, 13):
        generate_temp_image(year, month)
        generate_rain_sun_image(year, month)

# Save bounds
with open(f"{OUTPUT_DIR}/bounds.json", 'w') as f:
    json.dump({
        "bounds": [[LAT_MIN, LNG_MIN], [LAT_MAX, LNG_MAX]],
        "projection": "WGS84 (EPSG:4326) - Leaflet native",
        "bng_extent": {
            "easting": [bng_x_min, bng_x_max],
            "northing": [bng_y_min, bng_y_max]
        }
    }, f, indent=2)

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
print(f"Generated 72 PNG files")
print(f"Bounds: [[{LAT_MIN:.4f}, {LNG_MIN:.4f}], [{LAT_MAX:.4f}, {LNG_MAX:.4f}]]")
print("=" * 70)
