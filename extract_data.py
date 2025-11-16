#!/usr/bin/env python3
"""
Data Extraction Script for Leaflet Overlay
Extracts temperature, rainfall, and sunshine data from NetCDF files to JSON format
optimized for efficient loading and rendering in the browser.
"""

import numpy as np
import xarray as xr
import json
import os
import gzip
from pathlib import Path

print("=" * 70)
print("DATA EXTRACTION FOR LEAFLET OVERLAY")
print("=" * 70)

# Configuration
TEMP_DATA_DIR = "temp_data"
RAIN_SUN_DATA_DIR = "rain_sun_data"
OUTPUT_DIR = "leaflet_data"
YEARS_TO_PROCESS = [2021, 2022, 2023]  # Years with all data available
WOOLHAMPTON_X = 457000  # British National Grid coordinates
WOOLHAMPTON_Y = 166000

# Grid extent from metadata
X_MIN = -199500.0
X_MAX = 699500.0
Y_MIN = -199500.0
Y_MAX = 1249500.0
RESOLUTION = 1000  # 1km

print(f"\nProcessing years: {YEARS_TO_PROCESS}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Woolhampton coordinates: ({WOOLHAMPTON_X}, {WOOLHAMPTON_Y})")

# Create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/temp", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/rain", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/sun", exist_ok=True)

def coord_to_index(x, y):
    """Convert British National Grid coordinates to grid indices"""
    col = int((x - X_MIN) / RESOLUTION)
    row = int((Y_MAX - y) / RESOLUTION)  # Y is flipped
    return row, col

def index_to_coord(row, col):
    """Convert grid indices to British National Grid coordinates (center of cell)"""
    x = X_MIN + (col + 0.5) * RESOLUTION
    y = Y_MAX - (row + 0.5) * RESOLUTION
    return x, y

# Find Woolhampton grid cell
woolhampton_row, woolhampton_col = coord_to_index(WOOLHAMPTON_X, WOOLHAMPTON_Y)
print(f"\nWoolhampton grid cell: row={woolhampton_row}, col={woolhampton_col}")

# For data storage, we use center coordinates
woolhampton_center_x, woolhampton_center_y = index_to_coord(woolhampton_row, woolhampton_col)
print(f"Woolhampton center coords: ({int(woolhampton_center_x)}, {int(woolhampton_center_y)})")

def process_variable(data_dir, var_pattern, var_name, output_subdir, woolhampton_tracking=False):
    """Process a climate variable from NetCDF files"""
    print(f"\n--- Processing {var_name} Data ---")

    woolhampton_values = []

    for year in YEARS_TO_PROCESS:
        print(f"\nProcessing year {year}...")

        # Find the NetCDF file for this year
        nc_pattern = var_pattern.format(year=year)
        nc_files = list(Path(data_dir).glob(nc_pattern))

        if not nc_files:
            print(f"  Warning: No NetCDF file found for {year}")
            continue

        nc_file = nc_files[0]
        print(f"  Reading: {nc_file}")

        # Open the NetCDF file
        ds = xr.open_dataset(nc_file)

        # Determine the variable name (it varies by data type)
        if 'tasmax' in ds.variables:
            data_var = ds['tasmax']
        elif 'rainfall' in ds.variables:
            data_var = ds['rainfall']
        elif 'sun' in ds.variables:
            data_var = ds['sun']
        else:
            # Try to find the main data variable
            possible_vars = [v for v in ds.variables if len(ds[v].dims) == 3]
            if possible_vars:
                data_var = ds[possible_vars[0]]
                print(f"  Using variable: {possible_vars[0]}")
            else:
                print(f"  Error: Could not find data variable")
                ds.close()
                continue

        print(f"  Shape: {data_var.shape}")

        # Process each month
        for month_idx in range(12):
            month = month_idx + 1
            print(f"  Processing month {month:02d}...", end=' ')

            # Get data for this month
            month_data_array = data_var[month_idx].values

            # Track Woolhampton values if requested
            if woolhampton_tracking:
                woolhampton_val = month_data_array[woolhampton_row, woolhampton_col]
                if not np.isnan(woolhampton_val):
                    woolhampton_values.append(woolhampton_val)

            # Create sparse representation (only store non-NaN values)
            # Format: {x: {y: value}} for efficient lookup
            month_data = {}

            non_nan_count = 0
            rows, cols = np.where(~np.isnan(month_data_array))

            for row, col in zip(rows, cols):
                x, y = index_to_coord(row, col)
                x_key = str(int(x))
                y_key = str(int(y))

                if x_key not in month_data:
                    month_data[x_key] = {}

                # Store value rounded to 1 decimal place
                month_data[x_key][y_key] = round(float(month_data_array[row, col]), 1)
                non_nan_count += 1

            print(f"{non_nan_count} cells")

            # Save month data as compressed JSON
            output_file = f"{OUTPUT_DIR}/{output_subdir}/{year}_{month:02d}.json.gz"
            with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                json.dump(month_data, f, separators=(',', ':'))

        ds.close()

    return woolhampton_values

# Process temperature data
woolhampton_temps = process_variable(
    TEMP_DATA_DIR,
    "tasmax_hadukgrid_uk_1km_mon_{year}*.nc",
    "Temperature",
    "temp",
    woolhampton_tracking=True
)

# Process rainfall data
process_variable(
    RAIN_SUN_DATA_DIR,
    "rainfall_hadukgrid_uk_1km_mon_{year}*.nc",
    "Rainfall",
    "rain",
    woolhampton_tracking=False
)

# Process sunshine data
process_variable(
    RAIN_SUN_DATA_DIR,
    "sun_hadukgrid_uk_1km_mon_{year}*.nc",
    "Sunshine",
    "sun",
    woolhampton_tracking=False
)

# Calculate Woolhampton temperature range
if woolhampton_temps:
    woolhampton_min = min(woolhampton_temps)
    woolhampton_max = max(woolhampton_temps)
    woolhampton_avg = sum(woolhampton_temps) / len(woolhampton_temps)
    print(f"\n--- Woolhampton Temperature Statistics ---")
    print(f"Samples: {len(woolhampton_temps)}")
    print(f"Min: {woolhampton_min:.1f}°C")
    print(f"Max: {woolhampton_max:.1f}°C")
    print(f"Average: {woolhampton_avg:.1f}°C")

    # Use absolute scale with sensible bounds for UK climate
    # Based on Woolhampton but rounded to reasonable values
    scale_min = -10  # Reasonable minimum for UK
    scale_max = 32   # Reasonable maximum for UK
    print(f"\n--- Using Absolute Temperature Scale ---")
    print(f"Scale: {scale_min}°C to {scale_max}°C")
else:
    print("\nWarning: No Woolhampton temperatures found - using default UK range")
    woolhampton_min = 0
    woolhampton_max = 25
    scale_min = -10
    scale_max = 32

# Create metadata file
metadata = {
    "extent": {
        "x_min": X_MIN,
        "x_max": X_MAX,
        "y_min": Y_MIN,
        "y_max": Y_MAX,
        "crs": "EPSG:27700",
        "resolution_meters": RESOLUTION
    },
    "years": YEARS_TO_PROCESS,
    "months": list(range(1, 13)),
    "temperature": {
        "woolhampton_coords": {
            "x": WOOLHAMPTON_X,
            "y": WOOLHAMPTON_Y
        },
        "woolhampton_observed": {
            "min": round(woolhampton_min, 1) if woolhampton_temps else None,
            "max": round(woolhampton_max, 1) if woolhampton_temps else None
        },
        "scale_range": {
            "min": scale_min,
            "max": scale_max
        },
        "unit": "°C",
        "variable": "tasmax",
        "description": "Maximum temperature (absolute scale)"
    },
    "rainfall": {
        "unit": "mm",
        "description": "Monthly rainfall"
    },
    "sunshine": {
        "unit": "hours",
        "description": "Monthly sunshine hours"
    },
    "data_format": "sparse",
    "compression": "gzip",
    "coordinate_system": "British National Grid (EPSG:27700)"
}

with open(f"{OUTPUT_DIR}/metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n✓ Metadata saved to {OUTPUT_DIR}/metadata.json")
print("\n" + "=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)
print(f"\nGenerated {len(YEARS_TO_PROCESS) * 12 * 3} data files")
print(f"  - Temperature: {len(YEARS_TO_PROCESS) * 12} files")
print(f"  - Rainfall: {len(YEARS_TO_PROCESS) * 12} files")
print(f"  - Sunshine: {len(YEARS_TO_PROCESS) * 12} files")
print("\nFiles are gzip-compressed JSON for efficient loading")
print("\nNext steps:")
print("1. Implement Leaflet map with OSM tiles")
print("2. Create canvas overlay renderer")
print("3. Load and display data with opacity controls")
