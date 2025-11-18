#!/usr/bin/env python3
"""
Verify coordinate transformation math step by step
"""
import pyproj
import json

# Setup transformers
bng_to_mercator = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:3857", always_xy=True)
mercator_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
wgs84_to_mercator = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

# PNG bounds
bng_x_min, bng_y_min = 0, 0
bng_x_max, bng_y_max = 700000, 1250000

# Convert BNG bounds to Mercator
merc_x_min, merc_y_min = bng_to_mercator.transform(bng_x_min, bng_y_min)
merc_x_max, merc_y_max = bng_to_mercator.transform(bng_x_max, bng_y_max)

# Convert Mercator to WGS84 (Leaflet bounds)
sw_lng, sw_lat = mercator_to_wgs84.transform(merc_x_min, merc_y_min)
ne_lng, ne_lat = mercator_to_wgs84.transform(merc_x_max, merc_y_max)

IMG_WIDTH = 2000
IMG_HEIGHT = 3000

print("=" * 70)
print("STEP-BY-STEP VERIFICATION")
print("=" * 70)

print("\n1. BNG BOUNDS:")
print(f"   SW corner (min): BNG({bng_x_min}, {bng_y_min})")
print(f"   NE corner (max): BNG({bng_x_max}, {bng_y_max})")

print("\n2. MERCATOR BOUNDS:")
print(f"   SW corner (min): Mercator({merc_x_min:.0f}, {merc_y_min:.0f})")
print(f"   NE corner (max): Mercator({merc_x_max:.0f}, {merc_y_max:.0f})")

print("\n3. WGS84 BOUNDS (for Leaflet):")
print(f"   SW corner: WGS84({sw_lat:.4f}°, {sw_lng:.4f}°)")
print(f"   NE corner: WGS84({ne_lat:.4f}°, {ne_lng:.4f}°)")
print(f"   Leaflet bounds: [[{sw_lat:.4f}, {sw_lng:.4f}], [{ne_lat:.4f}, {ne_lng:.4f}]]")

print("\n4. IMAGE DIMENSIONS:")
print(f"   Width: {IMG_WIDTH} pixels")
print(f"   Height: {IMG_HEIGHT} pixels")

print("\n5. LEAFLET IMAGEOVERLAY EXPECTATIONS:")
print(f"   Pixel (0, 0) [top-left] should map to [{ne_lat:.4f}, {sw_lng:.4f}] (north-west)")
print(f"   Pixel ({IMG_HEIGHT-1}, {IMG_WIDTH-1}) [bottom-right] should map to [{sw_lat:.4f}, {ne_lng:.4f}] (south-east)")

print("\n" + "=" * 70)
print("TEST: Isle of Wight")
print("=" * 70)

# Test point: Isle of Wight
iow_lat, iow_lng = 50.7632, -1.2973
print(f"Known WGS84 coordinates: ({iow_lat}, {iow_lng})")

# Convert to Mercator
iow_merc_x, iow_merc_y = wgs84_to_mercator.transform(iow_lng, iow_lat)
print(f"Mercator coordinates: ({iow_merc_x:.0f}, {iow_merc_y:.0f})")

# Calculate pixel position using the formula from generate_test_image.py
row = (merc_y_max - iow_merc_y) / (merc_y_max - merc_y_min) * IMG_HEIGHT
col = (iow_merc_x - merc_x_min) / (merc_x_max - merc_x_min) * IMG_WIDTH

print(f"\nPixel calculation:")
print(f"  row = (merc_y_max - iow_merc_y) / (merc_y_max - merc_y_min) * IMG_HEIGHT")
print(f"      = ({merc_y_max:.0f} - {iow_merc_y:.0f}) / ({merc_y_max:.0f} - {merc_y_min:.0f}) * {IMG_HEIGHT}")
print(f"      = {(merc_y_max - iow_merc_y):.0f} / {(merc_y_max - merc_y_min):.0f} * {IMG_HEIGHT}")
print(f"      = {row:.2f}")
print(f"")
print(f"  col = (iow_merc_x - merc_x_min) / (merc_x_max - merc_x_min) * IMG_WIDTH")
print(f"      = ({iow_merc_x:.0f} - {merc_x_min:.0f}) / ({merc_x_max:.0f} - {merc_x_min:.0f}) * {IMG_WIDTH}")
print(f"      = {(iow_merc_x - merc_x_min):.0f} / {(merc_x_max - merc_x_min):.0f} * {IMG_WIDTH}")
print(f"      = {col:.2f}")

print(f"\nPixel position in PNG: ({int(row)}, {int(col)})")

# Verify: convert pixel back to WGS84
verify_row, verify_col = int(row), int(col)
verify_merc_y = merc_y_max - (verify_row / IMG_HEIGHT) * (merc_y_max - merc_y_min)
verify_merc_x = merc_x_min + (verify_col / IMG_WIDTH) * (merc_x_max - merc_x_min)
verify_lng, verify_lat = mercator_to_wgs84.transform(verify_merc_x, verify_merc_y)

print(f"\nVerification (pixel → WGS84):")
print(f"  Pixel ({verify_row}, {verify_col}) → Mercator({verify_merc_x:.0f}, {verify_merc_y:.0f}) → WGS84({verify_lat:.4f}, {verify_lng:.4f})")
print(f"  Expected WGS84: ({iow_lat}, {iow_lng})")
print(f"  Error: lat={abs(verify_lat - iow_lat):.6f}°, lng={abs(verify_lng - iow_lng):.6f}°")

print("\n" + "=" * 70)
print("LEAFLET IMAGEOVERLAY CHECK")
print("=" * 70)

# When Leaflet displays imageOverlay with bounds [[sw_lat, sw_lng], [ne_lat, ne_lng]]:
# - It places image pixel (0, 0) at map coordinates [ne_lat, sw_lng]
# - It places image pixel (height-1, width-1) at [sw_lat, ne_lng]

# So for our Isle of Wight pixel to appear at the correct lat/lng in Leaflet:
# We need to check if the pixel/bounds relationship is correct

print(f"\nLeaflet will display:")
print(f"  Image pixel (0, 0) at map WGS84 [{ne_lat:.4f}, {sw_lng:.4f}]")
print(f"  Image pixel ({IMG_HEIGHT-1}, {IMG_WIDTH-1}) at map WGS84 [{sw_lat:.4f}, {ne_lng:.4f}]")

print(f"\nOur Isle of Wight pixel ({verify_row}, {verify_col}) should appear at:")

# Calculate what WGS84 Leaflet will place this pixel at
leaflet_lat = ne_lat - (verify_row / IMG_HEIGHT) * (ne_lat - sw_lat)
leaflet_lng = sw_lng + (verify_col / IMG_WIDTH) * (ne_lng - sw_lng)

print(f"  Leaflet will place pixel ({verify_row}, {verify_col}) at WGS84 [{leaflet_lat:.4f}, {leaflet_lng:.4f}]")
print(f"  We want it at: [{iow_lat}, {iow_lng}]")
print(f"  Error: lat={abs(leaflet_lat - iow_lat):.6f}°, lng={abs(leaflet_lng - iow_lng):.6f}°")

if abs(leaflet_lat - iow_lat) < 0.01 and abs(leaflet_lng - iow_lng) < 0.01:
    print("\n✓ ALIGNMENT LOOKS CORRECT!")
else:
    print("\n✗ ALIGNMENT IS WRONG!")
    print("   The coordinate transformation has an error.")
