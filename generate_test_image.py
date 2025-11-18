#!/usr/bin/env python3
"""
Generate a test PNG with colored dots at known UK landmarks
"""
import numpy as np
from PIL import Image, ImageDraw
import pyproj
import json

# Setup transformers
bng_to_mercator = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:3857", always_xy=True)
mercator_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
wgs84_to_bng = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

# PNG bounds (same as generate_pngs.py)
bng_x_min = 0
bng_x_max = 700000
bng_y_min = 0
bng_y_max = 1250000

# Convert to Web Mercator
merc_x_min, merc_y_min = bng_to_mercator.transform(bng_x_min, bng_y_min)
merc_x_max, merc_y_max = bng_to_mercator.transform(bng_x_max, bng_y_max)

# Get Leaflet bounds
sw_lng, sw_lat = mercator_to_wgs84.transform(merc_x_min, merc_y_min)
ne_lng, ne_lat = mercator_to_wgs84.transform(merc_x_max, merc_y_max)

# Image dimensions
IMG_WIDTH = 2000
IMG_HEIGHT = 3000

# Test landmarks with colors
test_points = [
    {'name': 'Isle of Wight', 'wgs84': (-1.2973, 50.7632), 'color': (255, 0, 0)},      # RED
    {'name': 'London', 'wgs84': (-0.1276, 51.5074), 'color': (255, 255, 0)},            # YELLOW
    {'name': 'Edinburgh', 'wgs84': (-3.1883, 55.9533), 'color': (0, 255, 0)},           # GREEN
    {'name': 'Lizard Point', 'wgs84': (-5.2017, 49.9575), 'color': (0, 0, 255)},        # BLUE
]

print("Generating test image with landmark markers...")
print(f"Bounds: [[{sw_lat:.4f}, {sw_lng:.4f}], [{ne_lat:.4f}, {ne_lng:.4f}]]")

# Create blank image
img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

# For each landmark, draw a colored circle
for point in test_points:
    lng, lat = point['wgs84']
    name = point['name']
    color = point['color']

    # Convert to BNG
    bng_x, bng_y = wgs84_to_bng.transform(lng, lat)

    # Check if within bounds
    if not (bng_x_min <= bng_x <= bng_x_max and bng_y_min <= bng_y <= bng_y_max):
        print(f"  {name}: OUTSIDE BOUNDS")
        continue

    # Convert to Mercator
    merc_x, merc_y = bng_to_mercator.transform(bng_x, bng_y)

    # Calculate pixel position
    # row 0 should be at north (merc_y_max) for Leaflet
    row = int((merc_y_max - merc_y) / (merc_y_max - merc_y_min) * IMG_HEIGHT)
    col = int((merc_x - merc_x_min) / (merc_x_max - merc_x_min) * IMG_WIDTH)

    row = max(0, min(IMG_HEIGHT - 1, row))
    col = max(0, min(IMG_WIDTH - 1, col))

    print(f"  {name}: WGS84({lat:.4f}, {lng:.4f}) -> BNG({bng_x:.0f}, {bng_y:.0f}) -> Pixel({row}, {col}) -> Color{color}")

    # Draw a circle (50 pixel radius)
    for dr in range(-50, 51):
        for dc in range(-50, 51):
            if dr*dr + dc*dc <= 50*50:
                r = row + dr
                c = col + dc
                if 0 <= r < IMG_HEIGHT and 0 <= c < IMG_WIDTH:
                    img_array[r, c] = list(color) + [255]

# Save PNG
img = Image.fromarray(img_array, 'RGBA')
img.save("leaflet_pngs/test_landmarks.png", optimize=True)

# Save bounds JSON
with open("leaflet_pngs/test_bounds.json", 'w') as f:
    json.dump({
        "bounds": [[sw_lat, sw_lng], [ne_lat, ne_lng]],
        "test_points": [
            {
                "name": p['name'],
                "lat": p['wgs84'][1],
                "lng": p['wgs84'][0],
                "color": f"rgb{p['color']}"
            }
            for p in test_points
        ]
    }, f, indent=2)

print("\n✓ Test image saved to: leaflet_pngs/test_landmarks.png")
print("✓ Bounds saved to: leaflet_pngs/test_bounds.json")
