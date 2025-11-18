#!/usr/bin/env python3
"""
Check if the actual climate data in the PNG is right-side-up
by looking at where Scotland (north) and England (south) data appears
"""
import json
from PIL import Image
import pyproj

# Load bounds
with open('leaflet_pngs/bounds.json', 'r') as f:
    data = json.load(f)
    bounds = data['bounds']

LAT_MIN, LNG_MIN = bounds[0]  # South-West
LAT_MAX, LNG_MAX = bounds[1]  # North-East

# Load an actual climate PNG
img = Image.open('leaflet_pngs/temp/2021_01.png')
IMG_WIDTH, IMG_HEIGHT = img.size
pixels = img.load()

print("=" * 70)
print("CHECKING DATA ORIENTATION IN ACTUAL PNG")
print("=" * 70)
print(f"Image: leaflet_pngs/temp/2021_01.png")
print(f"Size: {IMG_WIDTH} x {IMG_HEIGHT}")
print(f"Bounds: [[{LAT_MIN:.4f}, {LNG_MIN:.4f}], [{LAT_MAX:.4f}, {LNG_MAX:.4f}]]")

# Known locations to test:
test_locations = [
    {
        'name': 'Northern Scotland (Thurso)',
        'lat': 58.5936,
        'lng': -3.5269,
        'expected': 'top of image (low row number)'
    },
    {
        'name': 'Southern England (Brighton)',
        'lat': 50.8225,
        'lng': -0.1372,
        'expected': 'bottom of image (high row number)'
    },
    {
        'name': 'Edinburgh',
        'lat': 55.9533,
        'lng': -3.1883,
        'expected': 'middle-upper part of image'
    }
]

print("\n" + "=" * 70)
print("WHERE DOES DATA APPEAR?")
print("=" * 70)

for loc in test_locations:
    lat, lng = loc['lat'], loc['lng']
    name = loc['name']
    expected = loc['expected']

    # Calculate pixel position
    row = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (IMG_HEIGHT - 1))
    col = int((lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * (IMG_WIDTH - 1))

    # Check pixel color
    if 0 <= row < IMG_HEIGHT and 0 <= col < IMG_WIDTH:
        r, g, b, a = pixels[col, row]
        has_data = (a > 0)

        print(f"\n{name}:")
        print(f"  WGS84: ({lat:.4f}°, {lng:.4f}°)")
        print(f"  Pixel: row={row}, col={col}")
        print(f"  Expected: {expected}")
        print(f"  Actual location in image:")
        if row < IMG_HEIGHT / 3:
            actual_pos = f"TOP third (row {row}/{IMG_HEIGHT})"
        elif row < 2 * IMG_HEIGHT / 3:
            actual_pos = f"MIDDLE third (row {row}/{IMG_HEIGHT})"
        else:
            actual_pos = f"BOTTOM third (row {row}/{IMG_HEIGHT})"
        print(f"    {actual_pos}")
        print(f"  Has data: {'YES' if has_data else 'NO'} (alpha={a}, color=({r},{g},{b}))")

        if name == 'Northern Scotland (Thurso)':
            if row < IMG_HEIGHT / 2:
                print(f"  ✓ Scotland is in TOP half - CORRECT")
            else:
                print(f"  ✗ Scotland is in BOTTOM half - UPSIDE DOWN!")

        if name == 'Southern England (Brighton)':
            if row > IMG_HEIGHT / 2:
                print(f"  ✓ Southern England is in BOTTOM half - CORRECT")
            else:
                print(f"  ✗ Southern England is in TOP half - UPSIDE DOWN!")

# Visual check: scan the image to see where most colored pixels are
print("\n" + "=" * 70)
print("DATA DISTRIBUTION CHECK")
print("=" * 70)

top_third_pixels = 0
middle_third_pixels = 0
bottom_third_pixels = 0

for y in range(IMG_HEIGHT):
    for x in range(IMG_WIDTH):
        r, g, b, a = pixels[x, y]
        if a > 0:  # Has data
            if y < IMG_HEIGHT / 3:
                top_third_pixels += 1
            elif y < 2 * IMG_HEIGHT / 3:
                middle_third_pixels += 1
            else:
                bottom_third_pixels += 1

total = top_third_pixels + middle_third_pixels + bottom_third_pixels
print(f"Colored pixels by region:")
print(f"  Top third:    {top_third_pixels:,} ({100*top_third_pixels/total:.1f}%)")
print(f"  Middle third: {middle_third_pixels:,} ({100*middle_third_pixels/total:.1f}%)")
print(f"  Bottom third: {bottom_third_pixels:,} ({100*bottom_third_pixels/total:.1f}%)")

print("\nExpected pattern for UK:")
print("  - Most data should be in middle third (where England/Wales are)")
print("  - Some data in top third (Scotland)")
print("  - Less data in bottom third (southern England)")
