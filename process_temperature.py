#!/usr/bin/env python3
"""
Temperature Data Preprocessing Script
Generates PNG images for UK temperature data visualization
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import xarray as xr
import os
import json
from PIL import Image
from datetime import datetime

print("=" * 60)
print("UK TEMPERATURE MAP PREPROCESSING SCRIPT")
print("=" * 60)

# --- CONFIGURATION ---
YEARS_TO_PROCESS = list(range(2010, 2024))  # 2010-2023
OUTPUT_BASE_DIR = "data"
TEMP_DATA_DIR = "temp_data"

# Temperature color scheme (blue to red)
# Using a diverging colormap from cool to warm
# We'll use matplotlib's coolwarm but create discrete bins
TEMP_COLORS = [
    "#053061",  # Very cold - dark blue
    "#2166ac",  # Cold - blue
    "#4393c3",  # Cool - light blue
    "#92c5de",  # Mild cool - pale blue
    "#d1e5f0",  # Neutral cool - very pale blue
    "#fddbc7",  # Neutral warm - very pale orange
    "#f4a582",  # Mild warm - pale orange
    "#d6604d",  # Warm - orange-red
    "#b2182b",  # Hot - red
    "#67001f"   # Very hot - dark red
]

print(f"\nProcessing years: {YEARS_TO_PROCESS[0]} to {YEARS_TO_PROCESS[-1]}")
print(f"Output directory: {OUTPUT_BASE_DIR}")
print(f"Temperature data directory: {TEMP_DATA_DIR}")

# --- 1. CREATE DIRECTORY STRUCTURE ---
print("\n--- Step 1: Creating directory structure ---")

os.makedirs(f"{OUTPUT_BASE_DIR}/temp_images", exist_ok=True)
os.makedirs(f"{OUTPUT_BASE_DIR}/temp_averages", exist_ok=True)

for year in YEARS_TO_PROCESS:
    os.makedirs(f"{OUTPUT_BASE_DIR}/temp_images/{year}", exist_ok=True)

print("✓ Directories created")

# --- 2. GENERATE TEMPERATURE KEY ---
print("\n--- Step 2: Generating temperature key ---")

# Create a colormap from our colors
cmap = mcolors.LinearSegmentedColormap.from_list("temperature", TEMP_COLORS, N=256)

# Create a colorbar visualization
fig, ax = plt.subplots(figsize=(6, 1.5))
fig.subplots_adjust(bottom=0.5)

# Create a colorbar
norm = mcolors.Normalize(vmin=0, vmax=1)
cb = plt.colorbar(
    plt.cm.ScalarMappable(norm=norm, cmap=cmap),
    cax=ax,
    orientation='horizontal'
)
cb.set_label('Temperature (°C)', fontsize=12, fontweight='bold')
cb.ax.set_xlabel('← Colder                                    Warmer →',
                  fontsize=11, fontweight='bold')
cb.set_ticks([])  # Remove tick marks for cleaner look

plt.savefig(f"{OUTPUT_BASE_DIR}/temp_key.png", dpi=150, bbox_inches='tight',
            pad_inches=0.1, transparent=False, facecolor='white')
plt.close()

# Transparent version
fig, ax = plt.subplots(figsize=(6, 1.5))
fig.subplots_adjust(bottom=0.5)
cb = plt.colorbar(
    plt.cm.ScalarMappable(norm=norm, cmap=cmap),
    cax=ax,
    orientation='horizontal'
)
cb.set_label('Temperature (°C)', fontsize=12, fontweight='bold')
cb.ax.set_xlabel('← Colder                                    Warmer →',
                  fontsize=11, fontweight='bold')
cb.set_ticks([])

plt.savefig(f"{OUTPUT_BASE_DIR}/temp_key_transparent.png", dpi=150,
            bbox_inches='tight', pad_inches=0.1, transparent=True)
plt.close()

print("✓ Temperature keys saved (temp_key.png and temp_key_transparent.png)")

# --- 3. HELPER FUNCTION TO CREATE RGB ARRAY ---
def create_temp_rgb_array(temp_values, colors):
    """
    Create RGB array from temperature data using decile-based coloring.
    Uses 10 color bins (deciles) for the temperature range.
    """
    n_y, n_x = temp_values.shape
    rgb_array = np.ones((n_y, n_x, 3))

    # Remove NaN values for decile calculation
    temp_flat = temp_values.flatten()
    temp_valid = temp_flat[~np.isnan(temp_flat)]

    if len(temp_valid) == 0:
        return rgb_array  # Return white image if no valid data

    # Calculate decile boundaries (10 bins)
    decile_bounds = np.percentile(temp_valid, np.arange(10, 100, 10))

    # Create color mapping
    valid_mask = ~np.isnan(temp_values)

    # Assign colors based on deciles
    color_idx = np.zeros_like(temp_values, dtype=int)
    color_idx[valid_mask] = 0  # Start with coldest color

    for i, bound in enumerate(decile_bounds):
        color_idx[(temp_values > bound) & valid_mask] = i + 1

    # Apply colors
    for i in range(len(colors)):
        mask = (color_idx == i) & valid_mask
        rgb_array[mask] = mcolors.to_rgb(colors[i])

    # Flip vertically for correct orientation (BNG y-up, image y-down)
    rgb_array = np.flipud(rgb_array)

    return rgb_array

# --- 4. PROCESS MONTHLY TEMPERATURE DATA FOR EACH YEAR ---
print("\n--- Step 3: Processing monthly temperature data ---")

# Storage for calculating averages
monthly_temp_sum = [[] for _ in range(12)]  # 12 months

x_coords = None
y_coords = None
extent_info = None

total_images = 0
failed_images = 0

for year in YEARS_TO_PROCESS:
    print(f"\n  Processing {year}...")

    # Define file path
    year_start = f"{year}01"
    year_end = f"{year}12"
    temp_file = f"{TEMP_DATA_DIR}/tasmax_hadukgrid_uk_1km_mon_{year_start}-{year_end}.nc"

    # Check if file exists
    if not os.path.exists(temp_file):
        print(f"    ⚠ Temperature file for {year} not found, skipping...")
        failed_images += 12
        continue

    try:
        # Load data
        nc_temp = xr.open_dataset(temp_file)

        # Get coordinates (only once)
        if x_coords is None:
            x_coords = nc_temp['projection_x_coordinate'].values
            y_coords = nc_temp['projection_y_coordinate'].values

            # Store extent information
            extent_info = {
                "x_min": float(x_coords.min()),
                "x_max": float(x_coords.max()),
                "y_min": float(y_coords.min()),
                "y_max": float(y_coords.max()),
                "crs": "EPSG:27700",
                "resolution_meters": 1000
            }

        # Process each month
        for month_idx in range(12):
            month_num = month_idx + 1
            month_str = f"{month_num:02d}"

            try:
                # Extract data for this month
                temp_values = nc_temp['tasmax'].isel(time=month_idx).values

                # Store for average calculation
                monthly_temp_sum[month_idx].append(temp_values)

                # Create RGB array
                rgb_array = create_temp_rgb_array(temp_values, TEMP_COLORS)

                # Convert to PIL Image and save
                img = Image.fromarray((rgb_array * 255).astype('uint8'))
                output_path = f"{OUTPUT_BASE_DIR}/temp_images/{year}/{month_str}.png"
                img.save(output_path, optimize=True, compress_level=9)

                total_images += 1

            except Exception as e:
                print(f"    ✗ Failed to process {year}-{month_str}: {e}")
                failed_images += 1

        print(f"    ✓ {year} complete (12 months)")

        # Close dataset
        nc_temp.close()

    except Exception as e:
        print(f"    ✗ Failed to load {year} data: {e}")
        failed_images += 12

print(f"\n✓ Monthly temperature images complete: {total_images} generated, {failed_images} failed")

# --- 5. CALCULATE AND SAVE MONTHLY AVERAGES ---
print("\n--- Step 4: Calculating monthly temperature averages ---")

month_names = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

for month_idx in range(12):
    month_num = month_idx + 1
    month_str = f"{month_num:02d}"
    month_name = month_names[month_idx]

    if len(monthly_temp_sum[month_idx]) == 0:
        print(f"  ⚠ No data for {month_name}, skipping...")
        continue

    # Calculate mean across all years
    temp_mean = np.mean(np.stack(monthly_temp_sum[month_idx]), axis=0)

    # Create RGB array
    rgb_array = create_temp_rgb_array(temp_mean, TEMP_COLORS)

    # Save
    img = Image.fromarray((rgb_array * 255).astype('uint8'))
    output_path = f"{OUTPUT_BASE_DIR}/temp_averages/{month_str}.png"
    img.save(output_path, optimize=True, compress_level=9)

    print(f"  ✓ {month_name} average created (based on {len(monthly_temp_sum[month_idx])} years)")

# --- 6. CREATE TEMPERATURE METADATA ---
print("\n--- Step 5: Creating temperature metadata ---")

if extent_info is None:
    print("  ✗ No data was processed, cannot create metadata!")
else:
    # Get actual image dimensions
    sample_img = Image.open(f"{OUTPUT_BASE_DIR}/temp_images/{YEARS_TO_PROCESS[0]}/01.png")
    image_width, image_height = sample_img.size

    temp_metadata = {
        "extent": extent_info,
        "image_dimensions": {
            "width": image_width,
            "height": image_height
        },
        "years": [y for y in YEARS_TO_PROCESS if os.path.exists(f"{OUTPUT_BASE_DIR}/temp_images/{y}/01.png")],
        "months": list(range(1, 13)),
        "month_names": month_names,
        "colors": TEMP_COLORS,
        "generated_at": datetime.now().isoformat(),
        "total_images": total_images,
        "data_source": "CEDA HADUKGrid 1km - Maximum Temperature (tasmax)",
        "variable": "tasmax",
        "units": "degrees_Celsius"
    }

    with open(f"{OUTPUT_BASE_DIR}/temp_metadata.json", 'w') as f:
        json.dump(temp_metadata, f, indent=2)

    print("✓ temp_metadata.json created")
    print(f"\nMetadata summary:")
    print(f"  - Image dimensions: {image_width} x {image_height}")
    print(f"  - Extent: X({extent_info['x_min']:.0f} to {extent_info['x_max']:.0f}), "
          f"Y({extent_info['y_min']:.0f} to {extent_info['y_max']:.0f})")
    print(f"  - Years available: {temp_metadata['years']}")

# --- 7. CALCULATE FILE SIZES ---
print("\n--- Step 6: Calculating total file sizes ---")

def get_dir_size(path):
    total = 0
    if not os.path.exists(path):
        return 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total += os.path.getsize(filepath)
    return total

images_size = get_dir_size(f"{OUTPUT_BASE_DIR}/temp_images") / (1024 * 1024)  # MB
averages_size = get_dir_size(f"{OUTPUT_BASE_DIR}/temp_averages") / (1024 * 1024)  # MB
total_size = images_size + averages_size

print(f"  - Monthly temperature images: {images_size:.1f} MB")
print(f"  - Monthly averages: {averages_size:.1f} MB")
print(f"  - Total: {total_size:.1f} MB")

# --- 8. SUMMARY ---
print("\n" + "=" * 60)
print("TEMPERATURE PREPROCESSING COMPLETE!")
print("=" * 60)
print(f"\nOutput directory: {OUTPUT_BASE_DIR}/")
print(f"  ├── temp_images/")
print(f"  │   ├── {YEARS_TO_PROCESS[0]}/ ... {YEARS_TO_PROCESS[-1]}/")
print(f"  │       └── 01.png ... 12.png")
print(f"  ├── temp_averages/")
print(f"  │   └── 01.png ... 12.png")
print(f"  ├── temp_key.png")
print(f"  ├── temp_key_transparent.png")
print(f"  └── temp_metadata.json")
print(f"\nReady for web integration!")
print("=" * 60)
