#!/usr/bin/env python3
"""
Generate PNGs in Web Mercator projection for Leaflet
Creates images that perfectly align with OSM tiles
"""

import numpy as np
from PIL import Image
import pyproj
import json
import gzip
from pathlib import Path
import os

print("=" * 70)
print("GENERATE WEB MERCATOR PNGS FOR LEAFLET")
print("=" * 70)

# Configuration
DATA_DIR = "leaflet_data"
OUTPUT_DIR = "leaflet_pngs"
YEARS = [2021, 2022, 2023]

# Output image size (larger = better quality, but bigger files)
IMG_WIDTH = 2000
IMG_HEIGHT = 3000  # UK is tall

# Geographic bounds (lat/lng) - cover UK
LAT_MIN = 49.5
LAT_MAX = 61.0
LNG_MIN = -8.5
LNG_MAX = 2.0

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
wgs84_to_bng = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

print(f"\nImage size: {IMG_WIDTH}x{IMG_HEIGHT}")
print(f"Geographic bounds: ({LAT_MIN}, {LNG_MIN}) to ({LAT_MAX}, {LNG_MAX})")

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
    """Generate temperature PNG"""
    print(f"  Temp {year}-{month:02d}...", end=' ', flush=True)

    temp_data = load_data(year, month, 'temp')
    if not temp_data:
        print("SKIP")
        return

    # Create image array
    img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

    # For each pixel, determine what data it represents
    for row in range(IMG_HEIGHT):
        for col in range(IMG_WIDTH):
            # Convert pixel to lat/lng
            # Row 0 should be at LAT_MAX (north/top), row IMG_HEIGHT at LAT_MIN (south/bottom)
            lat = LAT_MAX - (row / IMG_HEIGHT) * (LAT_MAX - LAT_MIN)
            lng = LNG_MIN + (col / IMG_WIDTH) * (LNG_MAX - LNG_MIN)

            # Convert lat/lng to BNG
            try:
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
                pass  # Outside BNG bounds

    # Save PNG
    img = Image.fromarray(img_array, 'RGBA')
    img.save(f"{OUTPUT_DIR}/temp/{year}_{month:02d}.png", optimize=True)
    print("✓")

def generate_rain_sun_image(year, month):
    """Generate rain/sun bivariate PNG"""
    print(f"  Rain/Sun {year}-{month:02d}...", end=' ', flush=True)

    rain_data = load_data(year, month, 'rain')
    sun_data = load_data(year, month, 'sun')

    if not rain_data or not sun_data:
        print("SKIP")
        return

    # Calculate percentiles
    rain_vals = []
    sun_vals = []
    for x_data in rain_data.values():
        rain_vals.extend(x_data.values())
    for x_data in sun_data.values():
        sun_vals.extend(x_data.values())

    rain_vals.sort()
    sun_vals.sort()

    rain33 = rain_vals[int(len(rain_vals) * 0.33)]
    rain66 = rain_vals[int(len(rain_vals) * 0.66)]
    sun33 = sun_vals[int(len(sun_vals) * 0.33)]
    sun66 = sun_vals[int(len(sun_vals) * 0.66)]

    # Create image array
    img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

    for row in range(IMG_HEIGHT):
        for col in range(IMG_WIDTH):
            # Row 0 should be at LAT_MAX (north/top), row IMG_HEIGHT at LAT_MIN (south/bottom)
            lat = LAT_MAX - (row / IMG_HEIGHT) * (LAT_MAX - LAT_MIN)
            lng = LNG_MIN + (col / IMG_WIDTH) * (LNG_MAX - LNG_MIN)

            try:
                bng_x, bng_y = wgs84_to_bng.transform(lng, lat)
                x_key = str(int(round(bng_x / 1000) * 1000))
                y_key = str(int(round(bng_y / 1000) * 1000))

                if (x_key in rain_data and y_key in rain_data[x_key] and
                    x_key in sun_data and y_key in sun_data[x_key]):

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

# Save bounds metadata
bounds_meta = {
    "bounds": [[LAT_MIN, LNG_MIN], [LAT_MAX, LNG_MAX]],
    "projection": "EPSG:4326 (WGS84) - native to Leaflet"
}

with open(f"{OUTPUT_DIR}/bounds.json", 'w') as f:
    json.dump(bounds_meta, f, indent=2)

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
print(f"Generated {len(YEARS) * 12 * 2} PNG files")
print(f"Bounds: [[{LAT_MIN}, {LNG_MIN}], [{LAT_MAX}, {LNG_MAX}]]")
