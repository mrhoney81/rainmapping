#!/usr/bin/env python3
"""
Generate simple PNG overlays from NetCDF data
Uses Leaflet ImageOverlay for instant, properly aligned display
"""

import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import os
from pathlib import Path
import pyproj

print("=" * 70)
print("GENERATE PNG OVERLAYS FOR LEAFLET")
print("=" * 70)

# Configuration
TEMP_DATA_DIR = "temp_data"
RAIN_SUN_DATA_DIR = "rain_sun_data"
OUTPUT_DIR = "leaflet_overlays"
YEARS_TO_PROCESS = [2021, 2022, 2023]

# Temperature colors
TEMP_COLORS = [
    "#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0",
    "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"
]

# Bivariate colors
BIVARIATE_COLORS = {
    (0, 0): "#f3f3f3", (0, 1): "#f3e6b3", (0, 2): "#f3b300",
    (1, 0): "#b4d3e1", (1, 1): "#b3b3b3", (1, 2): "#b36600",
    (2, 0): "#509dc2", (2, 1): "#376387", (2, 2): "#000000"
}

os.makedirs(f"{OUTPUT_DIR}/temp", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/rain_sun", exist_ok=True)

# Get geographic bounds of the BNG grid
transformer = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
X_MIN, Y_MIN = -199500.0, -199500.0
X_MAX, Y_MAX = 699500.0, 1249500.0

sw_lng, sw_lat = transformer.transform(X_MIN, Y_MIN)
ne_lng, ne_lat = transformer.transform(X_MAX, Y_MAX)
nw_lng, nw_lat = transformer.transform(X_MIN, Y_MAX)
se_lng, se_lat = transformer.transform(X_MAX, Y_MIN)

print(f"\nGeographic bounds:")
print(f"  SW: {sw_lat:.2f}, {sw_lng:.2f}")
print(f"  NE: {ne_lat:.2f}, {ne_lng:.2f}")

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def process_temp(year, month):
    """Generate temperature PNG"""
    nc_files = list(Path(TEMP_DATA_DIR).glob(f"tasmax_*{year}*.nc"))
    if not nc_files:
        return

    ds = xr.open_dataset(nc_files[0])
    temp_data = ds['tasmax'][month-1].values
    ds.close()

    rows, cols = temp_data.shape
    img_data = np.zeros((rows, cols, 4), dtype=np.uint8)

    for i in range(rows):
        for j in range(cols):
            if not np.isnan(temp_data[i, j]):
                # Map to color
                normalized = (temp_data[i, j] - (-10)) / (32 - (-10))
                clamped = max(0, min(1, normalized))
                color_idx = min(int(clamped * len(TEMP_COLORS)), len(TEMP_COLORS) - 1)
                r, g, b = hex_to_rgb(TEMP_COLORS[color_idx])
                img_data[i, j] = [r, g, b, 255]

    # Save with matplotlib for proper rendering
    fig, ax = plt.subplots(figsize=(cols/100, rows/100), dpi=100)
    ax.imshow(img_data, aspect='auto', interpolation='nearest')
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0,0)
    plt.savefig(f"{OUTPUT_DIR}/temp/{year}_{month:02d}.png",
                dpi=100, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()

def process_rain_sun(year, month):
    """Generate rain/sun bivariate PNG"""
    rain_files = list(Path(RAIN_SUN_DATA_DIR).glob(f"rainfall_*{year}*.nc"))
    sun_files = list(Path(RAIN_SUN_DATA_DIR).glob(f"sun_*{year}*.nc"))

    if not rain_files or not sun_files:
        return

    ds_rain = xr.open_dataset(rain_files[0])
    ds_sun = xr.open_dataset(sun_files[0])

    rain_data = ds_rain['rainfall'][month-1].values
    sun_data = ds_sun['sun'][month-1].values

    ds_rain.close()
    ds_sun.close()

    # Calculate percentiles
    rain_vals = rain_data[~np.isnan(rain_data)]
    sun_vals = sun_data[~np.isnan(sun_data)]

    rain_33, rain_66 = np.percentile(rain_vals, [33, 66])
    sun_33, sun_66 = np.percentile(sun_vals, [33, 66])

    rows, cols = rain_data.shape
    img_data = np.zeros((rows, cols, 4), dtype=np.uint8)

    for i in range(rows):
        for j in range(cols):
            if not np.isnan(rain_data[i, j]) and not np.isnan(sun_data[i, j]):
                rain_level = 0 if rain_data[i, j] < rain_33 else (1 if rain_data[i, j] < rain_66 else 2)
                sun_level = 0 if sun_data[i, j] < sun_33 else (1 if sun_data[i, j] < sun_66 else 2)

                r, g, b = hex_to_rgb(BIVARIATE_COLORS[(rain_level, sun_level)])
                img_data[i, j] = [r, g, b, 255]

    # Save
    fig, ax = plt.subplots(figsize=(cols/100, rows/100), dpi=100)
    ax.imshow(img_data, aspect='auto', interpolation='nearest')
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0,0)
    plt.savefig(f"{OUTPUT_DIR}/rain_sun/{year}_{month:02d}.png",
                dpi=100, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()

# Process all data
for year in YEARS_TO_PROCESS:
    print(f"\nYear {year}:")
    for month in range(1, 13):
        print(f"  Month {month:02d}... ", end='')
        process_temp(year, month)
        process_rain_sun(year, month)
        print("✓")

print("\n" + "=" * 70)
print("COMPLETE")
print(f"Bounds for Leaflet: [[{sw_lat}, {sw_lng}], [{ne_lat}, {ne_lng}]]")
print("=" * 70)
