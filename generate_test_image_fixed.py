#!/usr/bin/env python3
"""
Generate test PNG with colored dots - FIXED VERSION
Uses WGS84 coordinates for pixel calculation
"""
import numpy as np
from PIL import Image
import pyproj
import json

# Setup transformers
bng_to_wgs84 = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

# PNG bounds
bng_x_min, bng_y_min = 0, 0
bng_x_max, bng_y_max = 700000, 1250000

# Convert to WGS84
sw_lng, sw_lat = bng_to_wgs84.transform(bng_x_min, bng_y_min)
ne_lng, ne_lat = bng_to_wgs84.transform(bng_x_max, bng_y_max)

LAT_MIN = sw_lat
LAT_MAX = ne_lat
LNG_MIN = sw_lng
LNG_MAX = ne_lng

IMG_WIDTH = 2000
IMG_HEIGHT = 3000

# Test landmarks
test_points = [
    {'name': 'Isle of Wight', 'lat': 50.7632, 'lng': -1.2973, 'color': (255, 0, 0)},
    {'name': 'London', 'lat': 51.5074, 'lng': -0.1276, 'color': (255, 255, 0)},
    {'name': 'Edinburgh', 'lat': 55.9533, 'lng': -3.1883, 'color': (0, 255, 0)},
    {'name': 'Lizard Point', 'lat': 49.9575, 'lng': -5.2017, 'color': (0, 0, 255)},
]

print("=" * 70)
print("GENERATING TEST IMAGE (FIXED - Using WGS84)")
print("=" * 70)
print(f"Bounds: [[{LAT_MIN:.4f}, {LNG_MIN:.4f}], [{LAT_MAX:.4f}, {LNG_MAX:.4f}]]")
print()

# Create blank image
img_array = np.zeros((IMG_HEIGHT, IMG_WIDTH, 4), dtype=np.uint8)

# For each landmark, draw a colored circle
for point in test_points:
    lat, lng = point['lat'], point['lng']
    name = point['name']
    color = point['color']

    # Check if within bounds
    if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
        print(f"  {name}: OUTSIDE BOUNDS")
        continue

    # Calculate pixel position using WGS84 (same as Leaflet!)
    row = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (IMG_HEIGHT - 1))
    col = int((lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * (IMG_WIDTH - 1))

    row = max(0, min(IMG_HEIGHT - 1, row))
    col = max(0, min(IMG_WIDTH - 1, col))

    print(f"  {name}:")
    print(f"    WGS84: ({lat:.4f}°, {lng:.4f}°)")
    print(f"    Pixel: ({row}, {col})")
    print(f"    Color: rgb{color}")

    # Verify: convert pixel back to WGS84
    verify_lat = LAT_MAX - (row / (IMG_HEIGHT - 1)) * (LAT_MAX - LAT_MIN)
    verify_lng = LNG_MIN + (col / (IMG_WIDTH - 1)) * (LNG_MAX - LNG_MIN)
    print(f"    Verify: ({verify_lat:.4f}°, {verify_lng:.4f}°)")
    print(f"    Error: {abs(verify_lat - lat):.6f}° lat, {abs(verify_lng - lng):.6f}° lng")
    print()

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
        "bounds": [[LAT_MIN, LNG_MIN], [LAT_MAX, LNG_MAX]],
        "test_points": [
            {
                "name": p['name'],
                "lat": p['lat'],
                "lng": p['lng'],
                "color": f"rgb{p['color']}"
            }
            for p in test_points
        ]
    }, f, indent=2)

print("=" * 70)
print("✓ Test image saved: leaflet_pngs/test_landmarks.png")
print("✓ Bounds saved: leaflet_pngs/test_bounds.json")
print("=" * 70)
