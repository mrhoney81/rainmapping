#!/usr/bin/env python3
"""
Test: Read the actual pixel from the test PNG and verify where Leaflet will place it
"""
import json
from PIL import Image
import pyproj

# Load bounds
with open('leaflet_pngs/test_bounds.json', 'r') as f:
    data = json.load(f)
    bounds = data['bounds']  # [[south, west], [north, east]]

LAT_MIN, LNG_MIN = bounds[0]  # South-West
LAT_MAX, LNG_MAX = bounds[1]  # North-East

# Load test image
img = Image.open('leaflet_pngs/test_landmarks.png')
IMG_WIDTH, IMG_HEIGHT = img.size

print("=" * 70)
print("PIXEL LOCATION VERIFICATION")
print("=" * 70)
print(f"\nImage size: {IMG_WIDTH} x {IMG_HEIGHT}")
print(f"Leaflet bounds: [[{LAT_MIN}, {LNG_MIN}], [{LAT_MAX}, {LNG_MAX}]]")
print(f"  South-West: ({LAT_MIN}°, {LNG_MIN}°)")
print(f"  North-East: ({LAT_MAX}°, {LNG_MAX}°)")

print("\n" + "=" * 70)
print("LEAFLET'S COORDINATE MAPPING")
print("=" * 70)
print(f"Leaflet imageOverlay interprets the image as:")
print(f"  Pixel (0, 0) [top-left] → [{LAT_MAX}°, {LNG_MIN}°] (North-West)")
print(f"  Pixel (0, {IMG_WIDTH-1}) [top-right] → [{LAT_MAX}°, {LNG_MAX}°] (North-East)")
print(f"  Pixel ({IMG_HEIGHT-1}, 0) [bottom-left] → [{LAT_MIN}°, {LNG_MIN}°] (South-West)")
print(f"  Pixel ({IMG_HEIGHT-1}, {IMG_WIDTH-1}) [bottom-right] → [{LAT_MIN}°, {LNG_MAX}°] (South-East)")

# Test point: Isle of Wight
iow_lat, iow_lng = 50.7632, -1.2973

print("\n" + "=" * 70)
print("TEST: ISLE OF WIGHT")
print("=" * 70)
print(f"True location: ({iow_lat}°, {iow_lng}°)")

# Where SHOULD the red dot be in the PNG according to my generation code?
print("\n1. My generation code calculates pixel as:")
row_generated = int((LAT_MAX - iow_lat) / (LAT_MAX - LAT_MIN) * (IMG_HEIGHT - 1))
col_generated = int((iow_lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * (IMG_WIDTH - 1))
print(f"   row = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (HEIGHT - 1))")
print(f"       = int(({LAT_MAX} - {iow_lat}) / ({LAT_MAX} - {LAT_MIN}) * {IMG_HEIGHT - 1})")
print(f"       = {row_generated}")
print(f"   col = int((lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * (WIDTH - 1))")
print(f"       = int(({iow_lng} - {LNG_MIN}) / ({LNG_MAX} - {LNG_MIN}) * {IMG_WIDTH - 1})")
print(f"       = {col_generated}")
print(f"   → Pixel ({row_generated}, {col_generated})")

# Check if there's actually a red pixel there
pixels = img.load()
pixel_color = pixels[col_generated, row_generated]
print(f"   → Actual color at ({row_generated}, {col_generated}): {pixel_color}")
if pixel_color[0] > 200 and pixel_color[1] < 50 and pixel_color[2] < 50:
    print(f"   ✓ RED pixel found!")
else:
    print(f"   ✗ NOT red! Something is wrong.")

# Where WILL Leaflet place this pixel?
print("\n2. Leaflet will interpret pixel ({}, {}) as:".format(row_generated, col_generated))
leaflet_lat = LAT_MAX - (row_generated / (IMG_HEIGHT - 1)) * (LAT_MAX - LAT_MIN)
leaflet_lng = LNG_MIN + (col_generated / (IMG_WIDTH - 1)) * (LNG_MAX - LNG_MIN)
print(f"   lat = LAT_MAX - (row / (HEIGHT - 1)) * (LAT_MAX - LAT_MIN)")
print(f"       = {LAT_MAX} - ({row_generated} / {IMG_HEIGHT - 1}) * ({LAT_MAX} - {LAT_MIN})")
print(f"       = {leaflet_lat:.6f}°")
print(f"   lng = LNG_MIN + (col / (WIDTH - 1)) * (LNG_MAX - LNG_MIN)")
print(f"       = {LNG_MIN} + ({col_generated} / {IMG_WIDTH - 1}) * ({LNG_MAX} - {LNG_MIN})")
print(f"       = {leaflet_lng:.6f}°")
print(f"   → Location: ({leaflet_lat:.6f}°, {leaflet_lng:.6f}°)")

# Compare
print("\n3. Comparison:")
print(f"   Target location:  ({iow_lat}°, {iow_lng}°)")
print(f"   Leaflet will show: ({leaflet_lat:.6f}°, {leaflet_lng:.6f}°)")
print(f"   Error: {abs(leaflet_lat - iow_lat):.6f}° lat, {abs(leaflet_lng - iow_lng):.6f}° lng")

if abs(leaflet_lat - iow_lat) < 0.01 and abs(leaflet_lng - iow_lng) < 0.01:
    print(f"\n✓ ALIGNMENT CORRECT! Error < 0.01° (~1km)")
else:
    print(f"\n✗ ALIGNMENT WRONG! Error > 0.01°")
    lat_km = abs(leaflet_lat - iow_lat) * 111  # rough conversion to km
    lng_km = abs(leaflet_lng - iow_lng) * 111 * 0.64  # adjust for latitude
    print(f"   Approximate error: {lat_km:.1f}km north/south, {lng_km:.1f}km east/west")

# Scan the image to find all red pixels and see where they actually are
print("\n" + "=" * 70)
print("SCANNING FOR RED PIXELS IN IMAGE")
print("=" * 70)
red_pixels = []
for y in range(IMG_HEIGHT):
    for x in range(IMG_WIDTH):
        r, g, b, a = pixels[x, y]
        if r > 200 and g < 50 and b < 50 and a > 200:  # Red
            red_pixels.append((y, x))

if red_pixels:
    # Find center of red region
    avg_row = sum(p[0] for p in red_pixels) / len(red_pixels)
    avg_col = sum(p[1] for p in red_pixels) / len(red_pixels)
    print(f"Found {len(red_pixels)} red pixels")
    print(f"Center of red region: pixel ({avg_row:.0f}, {avg_col:.0f})")

    # Where will Leaflet show this?
    actual_lat = LAT_MAX - (avg_row / (IMG_HEIGHT - 1)) * (LAT_MAX - LAT_MIN)
    actual_lng = LNG_MIN + (avg_col / (IMG_WIDTH - 1)) * (LNG_MAX - LNG_MIN)
    print(f"Leaflet will show red dot at: ({actual_lat:.6f}°, {actual_lng:.6f}°)")
    print(f"Expected (Isle of Wight):     ({iow_lat}°, {iow_lng}°)")

    lat_diff = actual_lat - iow_lat
    lng_diff = actual_lng - iow_lng
    print(f"\nDifference: {lat_diff:.6f}° lat, {lng_diff:.6f}° lng")

    if lat_diff > 0:
        print(f"  Red dot is {abs(lat_diff):.6f}° NORTH of where it should be")
    else:
        print(f"  Red dot is {abs(lat_diff):.6f}° SOUTH of where it should be")
