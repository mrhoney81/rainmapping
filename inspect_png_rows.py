#!/usr/bin/env python3
"""
Directly inspect PNG to see what's in the first and last rows
"""
from PIL import Image
import json

# Load labeled test image
img = Image.open('leaflet_pngs/test_labeled.png')
width, height = img.size
pixels = img.load()

print("=" * 70)
print("INSPECTING PNG ROW CONTENT")
print("=" * 70)
print(f"Image size: {width} x {height}")
print(f"Testing what's in row 0 (top) vs row {height-1} (bottom)")

# Check row 0 (top of PNG file)
print(f"\nRow 0 (TOP of PNG file):")
has_blue = False
has_red = False
for x in range(100, width-100, 100):  # Sample pixels
    r, g, b, a = pixels[x, 0]
    if b > 200 and r < 100 and g < 100:
        has_blue = True
    if r > 200 and g < 100 and b < 100:
        has_red = True

if has_blue:
    print("  Contains BLUE pixels → Should be 'NORTH' label")
elif has_red:
    print("  Contains RED pixels → Should be 'SOUTH' label")
else:
    # Check a few more rows near the top
    for y in range(0, 300, 10):
        for x in range(width//2-200, width//2+200, 50):
            r, g, b, a = pixels[x, y]
            if b > 200 and r < 100 and g < 100:
                has_blue = True
                print(f"  Found BLUE at row {y} → 'NORTH' label near top")
                break
            if r > 200 and g < 100 and b < 100:
                has_red = True
                print(f"  Found RED at row {y} → 'SOUTH' label near top")
                break
        if has_blue or has_red:
            break

# Check row height-1 (bottom of PNG file)
print(f"\nRow {height-1} (BOTTOM of PNG file):")
has_blue_bottom = False
has_red_bottom = False
for x in range(100, width-100, 100):
    r, g, b, a = pixels[x, height-1]
    if b > 200 and r < 100 and g < 100:
        has_blue_bottom = True
    if r > 200 and g < 100 and b < 100:
        has_red_bottom = True

if has_red_bottom:
    print("  Contains RED pixels → Should be 'SOUTH' label")
elif has_blue_bottom:
    print("  Contains BLUE pixels → Should be 'NORTH' label")
else:
    # Check a few more rows near the bottom
    for y in range(height-300, height, 10):
        for x in range(width//2-200, width//2+200, 50):
            r, g, b, a = pixels[x, y]
            if b > 200 and r < 100 and g < 100:
                has_blue_bottom = True
                print(f"  Found BLUE at row {y} → 'NORTH' label near bottom")
                break
            if r > 200 and g < 100 and b < 100:
                has_red_bottom = True
                print(f"  Found RED at row {y} → 'SOUTH' label near bottom")
                break
        if has_blue_bottom or has_red_bottom:
            break

print("\n" + "=" * 70)
print("LEAFLET INTERPRETATION")
print("=" * 70)
with open('leaflet_pngs/test_labeled_bounds.json') as f:
    bounds = json.load(f)['bounds']
    lat_min, lng_min = bounds[0]
    lat_max, lng_max = bounds[1]

print(f"Leaflet bounds: [[{lat_min:.4f}, {lng_min:.4f}], [{lat_max:.4f}, {lng_max:.4f}]]")
print(f"\nLeaflet interprets imageOverlay as:")
print(f"  Row 0 (top of PNG) → displays at lat={lat_max:.4f} (NORTH)")
print(f"  Row {height-1} (bottom of PNG) → displays at lat={lat_min:.4f} (SOUTH)")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

if has_blue and not has_blue_bottom:
    print("✓ CORRECT: NORTH (blue) is at top of PNG")
    print("  Leaflet will display this at the north (top of map)")
    print("  → Image orientation is CORRECT")
elif has_red and not has_red_bottom:
    print("✗ WRONG: SOUTH (red) is at top of PNG")
    print("  Leaflet will display this at the north (top of map)")
    print("  → Image is UPSIDE DOWN in the file!")
elif has_blue_bottom and not has_blue:
    print("✗ WRONG: NORTH (blue) is at bottom of PNG")
    print("  Leaflet will display this at the south (bottom of map)")
    print("  → Image is UPSIDE DOWN in the file!")
elif has_red_bottom and not has_red:
    print("✓ CORRECT: SOUTH (red) is at bottom of PNG")
    print("  Leaflet will display this at the south (bottom of map)")
    print("  → Image orientation is CORRECT")
else:
    print("? UNCLEAR - could not determine orientation from pixel colors")
