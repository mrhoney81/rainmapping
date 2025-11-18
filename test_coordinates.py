#!/usr/bin/env python3
"""
Test coordinate transformations to verify PNG alignment
"""
import pyproj
import json

# Setup transformers
bng_to_mercator = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:3857", always_xy=True)
mercator_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
wgs84_to_bng = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
bng_to_wgs84 = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

# Known UK landmarks with WGS84 coordinates
landmarks = {
    'Isle of Wight (Cowes)': {'wgs84': (-1.2973, 50.7632)},
    'London (center)': {'wgs84': (-0.1276, 51.5074)},
    'Edinburgh': {'wgs84': (-3.1883, 55.9533)},
    'Lizard Point (south)': {'wgs84': (-5.2017, 49.9575)},
}

# Our PNG bounds (from generate_pngs.py)
bng_x_min = 0
bng_x_max = 700000
bng_y_min = 0
bng_y_max = 1250000

# Convert to Web Mercator
merc_x_min, merc_y_min = bng_to_mercator.transform(bng_x_min, bng_y_min)
merc_x_max, merc_y_max = bng_to_mercator.transform(bng_x_max, bng_y_max)

# Image dimensions
IMG_WIDTH = 2000
IMG_HEIGHT = 3000

print("=" * 70)
print("COORDINATE TRANSFORMATION TEST")
print("=" * 70)

print("\nPNG Bounds:")
print(f"  BNG: ({bng_x_min}, {bng_y_min}) to ({bng_x_max}, {bng_y_max})")
print(f"  Mercator: ({merc_x_min:.0f}, {merc_y_min:.0f}) to ({merc_x_max:.0f}, {merc_y_max:.0f})")

# Get Leaflet bounds
sw_lng, sw_lat = mercator_to_wgs84.transform(merc_x_min, merc_y_min)
ne_lng, ne_lat = mercator_to_wgs84.transform(merc_x_max, merc_y_max)
print(f"  Leaflet WGS84: [[{sw_lat:.4f}, {sw_lng:.4f}], [{ne_lat:.4f}, {ne_lng:.4f}]]")

print("\n" + "=" * 70)
print("LANDMARK POSITION TESTS")
print("=" * 70)

for name, data in landmarks.items():
    lng, lat = data['wgs84']

    print(f"\n{name}:")
    print(f"  WGS84: ({lat:.4f}°N, {lng:.4f}°E)")

    # Convert to BNG
    bng_x, bng_y = wgs84_to_bng.transform(lng, lat)
    print(f"  BNG: ({bng_x:.0f}, {bng_y:.0f})")

    # Check if within our bounds
    in_bounds = (bng_x_min <= bng_x <= bng_x_max and bng_y_min <= bng_y <= bng_y_max)
    print(f"  Within BNG bounds: {in_bounds}")

    if in_bounds:
        # Convert to Web Mercator
        merc_x, merc_y = bng_to_mercator.transform(bng_x, bng_y)
        print(f"  Mercator: ({merc_x:.0f}, {merc_y:.0f})")

        # Calculate pixel position in our PNG
        # IMPORTANT: In the PNG generation loop, row 0 = north (merc_y_max)
        # But then we flip with flipud(), so after flip: row 0 = south (merc_y_min)

        # BEFORE flipud:
        row_before_flip = int((merc_y_max - merc_y) / (merc_y_max - merc_y_min) * IMG_HEIGHT)
        col = int((merc_x - merc_x_min) / (merc_x_max - merc_x_min) * IMG_WIDTH)

        # AFTER flipud (what's actually in the PNG file):
        row_after_flip = IMG_HEIGHT - 1 - row_before_flip

        print(f"  Pixel (before flipud): row={row_before_flip}, col={col}")
        print(f"  Pixel (after flipud, in saved PNG): row={row_after_flip}, col={col}")

        # For Leaflet imageOverlay, the bounds are [[south, west], [north, east]]
        # and the image row 0 corresponds to NORTH (top of image)
        # So after flipud, row 0 should be at the SOUTH bound

        # What Leaflet will expect:
        # - Image row 0 = SOUTH latitude (sw_lat)
        # - Image row IMG_HEIGHT-1 = NORTH latitude (ne_lat)

        print(f"\n  Leaflet interpretation:")
        print(f"    Image row 0 should be at lat={sw_lat:.4f} (south)")
        print(f"    Image row {IMG_HEIGHT-1} should be at lat={ne_lat:.4f} (north)")
        print(f"    This landmark at lat={lat:.4f} should be at row={row_after_flip}")

print("\n" + "=" * 70)
print("EXPECTED LEAFLET BEHAVIOR")
print("=" * 70)
print(f"""
Leaflet's L.imageOverlay expects:
  - bounds: [[south_lat, west_lng], [north_lat, east_lng]]
  - Image top-left pixel (0,0) corresponds to [north_lat, west_lng]
  - Image bottom-right pixel corresponds to [south_lat, east_lng]

Our setup:
  - bounds: [[{sw_lat:.4f}, {sw_lng:.4f}], [{ne_lat:.4f}, {ne_lng:.4f}]]
  - PNG row 0 (after flipud) should be at lat={sw_lat:.4f} (SOUTH)
  - PNG row {IMG_HEIGHT-1} should be at lat={ne_lat:.4f} (NORTH)

PROBLEM CHECK:
  We generate the image with row 0 = north (merc_y_max)
  Then we flipud(), making row 0 = south (merc_y_min)

  BUT Leaflet expects row 0 to be NORTH!

  So flipud() is WRONG! We should NOT flip!
""")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)
print("""
The flipud() is causing the problem!

In the image generation loop:
  - row 0 maps to merc_y_max (north) - CORRECT for Leaflet
  - row 2999 maps to merc_y_min (south) - CORRECT for Leaflet

Then flipud() reverses this:
  - row 0 maps to merc_y_min (south) - WRONG!
  - row 2999 maps to merc_y_max (north) - WRONG!

SOLUTION: Remove the flipud() calls!
""")
