#!/usr/bin/env python3
"""
Generate a test PNG with clear NORTH/SOUTH labels
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyproj
import json

# Setup
bng_to_wgs84 = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

bng_x_min, bng_y_min = 0, 0
bng_x_max, bng_y_max = 700000, 1250000

sw_lng, sw_lat = bng_to_wgs84.transform(bng_x_min, bng_y_min)
ne_lng, ne_lat = bng_to_wgs84.transform(bng_x_max, bng_y_max)

LAT_MIN, LNG_MIN = sw_lat, sw_lng
LAT_MAX, LNG_MAX = ne_lat, ne_lng

IMG_WIDTH, IMG_HEIGHT = 2000, 3000

print(f"Generating labeled test image...")
print(f"Bounds: [[{LAT_MIN:.4f}, {LNG_MIN:.4f}], [{LAT_MAX:.4f}, {LNG_MAX:.4f}]]")

# Create image
img = Image.new('RGBA', (IMG_WIDTH, IMG_HEIGHT), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# Draw big labels
try:
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 200)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# NORTH label (should be at top of image when displayed correctly)
draw.text((IMG_WIDTH//2, 200), "NORTH", fill=(0, 0, 255, 255), font=font_large, anchor="mm")
draw.text((IMG_WIDTH//2, 400), "(Scotland)", fill=(0, 0, 255, 255), font=font_small, anchor="mm")
draw.text((IMG_WIDTH//2, 500), f"Lat: {LAT_MAX:.2f}°", fill=(0, 0, 255, 255), font=font_small, anchor="mm")

# SOUTH label (should be at bottom of image when displayed correctly)
draw.text((IMG_WIDTH//2, IMG_HEIGHT-200), "SOUTH", fill=(255, 0, 0, 255), font=font_large, anchor="mm")
draw.text((IMG_HEIGHT//2, IMG_HEIGHT-400), "(Southern England)", fill=(255, 0, 0, 255), font=font_small, anchor="mm")
draw.text((IMG_WIDTH//2, IMG_HEIGHT-500), f"Lat: {LAT_MIN:.2f}°", fill=(255, 0, 0, 255), font=font_small, anchor="mm")

# Draw arrows
# Arrow pointing UP at top (should point north in correct orientation)
arrow_top_y = 100
draw.polygon([
    (IMG_WIDTH//2, arrow_top_y - 50),
    (IMG_WIDTH//2 - 50, arrow_top_y + 50),
    (IMG_WIDTH//2 + 50, arrow_top_y + 50)
], fill=(0, 0, 255, 255))

# Arrow pointing DOWN at bottom (should point south in correct orientation)
arrow_bottom_y = IMG_HEIGHT - 100
draw.polygon([
    (IMG_WIDTH//2, arrow_bottom_y + 50),
    (IMG_WIDTH//2 - 50, arrow_bottom_y - 50),
    (IMG_WIDTH//2 + 50, arrow_bottom_y - 50)
], fill=(255, 0, 0, 255))

# Add specific location markers
locations = [
    {'name': 'Isle of Wight', 'lat': 50.7632, 'lng': -1.2973, 'color': (255, 165, 0)},  # Orange
    {'name': 'Edinburgh', 'lat': 55.9533, 'lng': -3.1883, 'color': (0, 255, 0)},  # Green
]

for loc in locations:
    lat, lng = loc['lat'], loc['lng']
    row = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (IMG_HEIGHT - 1))
    col = int((lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * (IMG_WIDTH - 1))

    if 0 <= row < IMG_HEIGHT and 0 <= col < IMG_WIDTH:
        # Draw circle
        radius = 30
        draw.ellipse([col-radius, row-radius, col+radius, row+radius],
                     fill=loc['color'] + (255,), outline=(0, 0, 0, 255), width=3)
        # Draw label
        draw.text((col, row-50), loc['name'], fill=(0, 0, 0, 255), font=font_small, anchor="mm")
        print(f"  {loc['name']}: pixel ({row}, {col})")

# Save
img.save("leaflet_pngs/test_labeled.png", optimize=True)

# Save bounds
with open("leaflet_pngs/test_labeled_bounds.json", 'w') as f:
    json.dump({
        "bounds": [[LAT_MIN, LNG_MIN], [LAT_MAX, LNG_MAX]],
        "description": "Test image with NORTH/SOUTH labels",
        "instructions": "When displayed correctly in Leaflet: NORTH (blue) should be at top, SOUTH (red) should be at bottom"
    }, f, indent=2)

print(f"\n✓ Saved: leaflet_pngs/test_labeled.png")
print(f"✓ Saved: leaflet_pngs/test_labeled_bounds.json")
print(f"\nWhen viewed in Leaflet:")
print(f"  - NORTH (blue) should appear at the TOP")
print(f"  - SOUTH (red) should appear at the BOTTOM")
print(f"  - If reversed, the image is upside down!")
