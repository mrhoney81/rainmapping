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
bng_to_mercator = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:3857", always_xy=True)
mercator_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
mercator_to_bng = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:27700", always_xy=True)

print("\n" + "=" * 70)
print("STEP 1: FINDING BNG DATA EXTENT")
print("=" * 70)

# Load one file to determine BNG extent
with gzip.open(f'{DATA_DIR}/temp/2021_01.json.gz', 'rt') as f:
    sample_data = json.load(f)

eastings = []
northings = []
for x_key, y_dict in sample_data.items():
    eastings.append(int(x_key))
    for y_key in y_dict.keys():
        northings.append(int(y_key))

# Use proper UK bounds instead of data extremes
# Data has outliers (remote islands) that distort the map
# UK mainland + nearby islands: roughly 0-700km E, 0-1250km N

# Get rough data extent
data_e_min, data_e_max = min(eastings), max(eastings)
data_n_min, data_n_max = min(northings), max(northings)

# Use sensible UK bounds
# South: Isles of Scilly (~0 northing)
# North: Shetland (~1,220,000 northing)
# West: Western Isles (~0 easting)
# East: East Anglia (~660,000 easting)
bng_x_min = 0
bng_x_max = 700000
bng_y_min = 0
bng_y_max = 1250000

print(f"Data extent (with outliers):")
print(f"  Easting:  {data_e_min:,} to {data_e_max:,}")
print(f"  Northing: {data_n_min:,} to {data_n_max:,}")
print(f"Using UK standard bounds:")
print(f"  Easting:  {bng_x_min:,} to {bng_x_max:,}")
print(f"  Northing: {bng_y_min:,} to {bng_y_max:,}")

# Convert BNG extent to Web Mercator
merc_x_min, merc_y_min = bng_to_mercator.transform(bng_x_min, bng_y_min)
merc_x_max, merc_y_max = bng_to_mercator.transform(bng_x_max, bng_y_max)

print(f"\nWeb Mercator extent:")
print(f"  X: {merc_x_min:,.0f} to {merc_x_max:,.0f}")
print(f"  Y: {merc_y_min:,.0f} to {merc_y_max:,.0f}")

# Convert to lat/lng for Leaflet bounds
sw_lng, sw_lat = mercator_to_wgs84.transform(merc_x_min, merc_y_min)
ne_lng, ne_lat = mercator_to_wgs84.transform(merc_x_max, merc_y_max)

LAT_MIN = sw_lat
LAT_MAX = ne_lat
LNG_MIN = sw_lng
LNG_MAX = ne_lng

print(f"\nLeaflet bounds (lat/lng):")
print(f"  Latitude:  {LAT_MIN:.4f}° to {LAT_MAX:.4f}°")
print(f"  Longitude: {LNG_MIN:.4f}° to {LNG_MAX:.4f}°")

print("\n" + "=" * 70)
print("STEP 2: GENERATING IMAGES IN WEB MERCATOR SPACE")
print("=" * 70)
print(f"Image size: {IMG_WIDTH}x{IMG_HEIGHT}")

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
    """Generate temperature PNG in Web Mercator space"""
    print(f"  Temp {year}-{month:02d}...", end=' ', flush=True)

    temp_data = load_data(year, month, 'temp')
    if not temp_data:
        print("SKIP")
        return

    # Create image array
    img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

    # For each pixel, map to Web Mercator coordinates
    for row in range(IMG_HEIGHT):
        for col in range(IMG_WIDTH):
            # Row 0 = top = north = merc_y_max
            # Last row = bottom = south = merc_y_min
            merc_y = merc_y_max - (row / IMG_HEIGHT) * (merc_y_max - merc_y_min)
            merc_x = merc_x_min + (col / IMG_WIDTH) * (merc_x_max - merc_x_min)

            try:
                # Convert Web Mercator → BNG
                bng_x, bng_y = mercator_to_bng.transform(merc_x, merc_y)

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

    # No flip - row 0 = north (merc_y_max), which is correct for Leaflet imageOverlay

    # Save PNG
    img = Image.fromarray(img_array, 'RGBA')
    img.save(f"{OUTPUT_DIR}/temp/{year}_{month:02d}.png", optimize=True)
    print("✓")

def generate_rain_sun_image(year, month):
    """Generate rain/sun bivariate PNG in Web Mercator space"""
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

    # For each pixel, map to Web Mercator coordinates
    for row in range(IMG_HEIGHT):
        for col in range(IMG_WIDTH):
            # Row 0 = top = north = merc_y_max
            # Last row = bottom = south = merc_y_min
            merc_y = merc_y_max - (row / IMG_HEIGHT) * (merc_y_max - merc_y_min)
            merc_x = merc_x_min + (col / IMG_WIDTH) * (merc_x_max - merc_x_min)

            try:
                # Convert Web Mercator → BNG
                bng_x, bng_y = mercator_to_bng.transform(merc_x, merc_y)

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

    # Flip vertically (row 0 in array should be at top of displayed image)
    img_array = np.flipud(img_array)

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
    "projection": "Web Mercator (EPSG:3857) → WGS84 bounds",
    "bng_extent": {
        "easting": [bng_x_min, bng_x_max],
        "northing": [bng_y_min, bng_y_max]
    }
}

with open(f"{OUTPUT_DIR}/bounds.json", 'w') as f:
    json.dump(bounds_meta, f, indent=2)

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
print(f"Generated {len(YEARS) * 12 * 2} PNG files")
print(f"Bounds: [[{LAT_MIN:.4f}, {LNG_MIN:.4f}], [{LAT_MAX:.4f}, {LNG_MAX:.4f}]]")
print("=" * 70)
