#!/usr/bin/env python3
"""
Generate example PNG overlay images for testing the test harness
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create examples directory
os.makedirs('examples', exist_ok=True)

# Image dimensions
WIDTH = 800
HEIGHT = 1200  # Taller for UK aspect ratio

# ============================================================================
# Example 1: Grid Pattern with Coordinates
# ============================================================================

def create_grid_pattern():
    """Create a grid pattern with coordinate labels"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw grid lines
    grid_spacing = 100
    for x in range(0, WIDTH, grid_spacing):
        # Vertical lines
        draw.line([(x, 0), (x, HEIGHT)], fill=(100, 100, 255, 180), width=2)

    for y in range(0, HEIGHT, grid_spacing):
        # Horizontal lines
        draw.line([(0, y), (WIDTH, y)], fill=(100, 100, 255, 180), width=2)

    # Draw corner markers
    corner_size = 50
    corners = [
        (0, 0, "NW"),
        (WIDTH - corner_size, 0, "NE"),
        (0, HEIGHT - corner_size, "SW"),
        (WIDTH - corner_size, HEIGHT - corner_size, "SE")
    ]

    for x, y, label in corners:
        draw.rectangle([x, y, x + corner_size, y + corner_size],
                      fill=(255, 0, 0, 200), outline=(0, 0, 0, 255), width=3)
        draw.text((x + 10, y + 15), label, fill=(255, 255, 255, 255))

    # Draw center crosshair
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    draw.line([(center_x - 100, center_y), (center_x + 100, center_y)],
             fill=(255, 0, 0, 255), width=4)
    draw.line([(center_x, center_y - 100), (center_x, center_y + 100)],
             fill=(255, 0, 0, 255), width=4)
    draw.ellipse([center_x - 10, center_y - 10, center_x + 10, center_y + 10],
                fill=(255, 0, 0, 255))

    # Add distance markers
    draw.rectangle([100, HEIGHT // 2 - 50, 300, HEIGHT // 2 + 50],
                  fill=(0, 255, 0, 150), outline=(0, 0, 0, 255), width=3)
    draw.text((110, HEIGHT // 2 - 10), "200px", fill=(0, 0, 0, 255))

    img.save('examples/1_grid_pattern.png')
    print("Created: examples/1_grid_pattern.png")

# ============================================================================
# Example 2: Heat Map Gradient
# ============================================================================

def create_heat_map():
    """Create a colorful heat map gradient"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Create vertical gradient (temperature style)
    for y in range(HEIGHT):
        # Calculate color based on position
        ratio = y / HEIGHT

        if ratio < 0.25:  # Blue (cold)
            r = int(0 + ratio * 4 * 100)
            g = int(0 + ratio * 4 * 100)
            b = 255
        elif ratio < 0.5:  # Cyan to Green
            r = 0
            g = int((ratio - 0.25) * 4 * 255)
            b = int(255 - (ratio - 0.25) * 4 * 255)
        elif ratio < 0.75:  # Green to Yellow
            r = int((ratio - 0.5) * 4 * 255)
            g = 255
            b = 0
        else:  # Yellow to Red
            r = 255
            g = int(255 - (ratio - 0.75) * 4 * 255)
            b = 0

        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 180))

    # Add some circular "hot spots"
    hot_spots = [
        (200, 300, 80, (255, 0, 0)),
        (600, 600, 100, (255, 165, 0)),
        (400, 900, 90, (255, 255, 0)),
    ]

    for x, y, radius, color in hot_spots:
        # Draw concentric circles for gradient effect
        for r in range(radius, 0, -5):
            alpha = int(150 * (r / radius))
            draw.ellipse([x - r, y - r, x + r, y + r],
                        fill=(*color, alpha))

    # Add legend
    legend_x, legend_y = 20, 20
    legend_height = 200
    for i in range(legend_height):
        ratio = i / legend_height
        if ratio < 0.33:
            color = (0, 0, 255)
        elif ratio < 0.67:
            color = (0, 255, 0)
        else:
            color = (255, 0, 0)
        draw.line([(legend_x, legend_y + i), (legend_x + 30, legend_y + i)],
                 fill=(*color, 200))

    draw.rectangle([legend_x, legend_y, legend_x + 30, legend_y + legend_height],
                  outline=(0, 0, 0, 255), width=2)

    img.save('examples/2_heat_map.png')
    print("Created: examples/2_heat_map.png")

# ============================================================================
# Example 3: Precipitation/Radar Style
# ============================================================================

def create_precipitation_map():
    """Create a precipitation/radar style overlay"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Create "rain bands" with varying intensity
    import random
    random.seed(42)  # Reproducible

    # Light rain (green)
    for _ in range(30):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        r = random.randint(40, 100)
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=(0, 255, 0, 80))

    # Moderate rain (yellow)
    for _ in range(20):
        x = random.randint(0, WIDTH)
        y = random.randint(HEIGHT // 4, HEIGHT * 3 // 4)
        r = random.randint(30, 80)
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=(255, 255, 0, 120))

    # Heavy rain (orange)
    for _ in range(10):
        x = random.randint(WIDTH // 4, WIDTH * 3 // 4)
        y = random.randint(HEIGHT // 3, HEIGHT * 2 // 3)
        r = random.randint(20, 60)
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=(255, 165, 0, 150))

    # Extreme rain (red)
    for _ in range(5):
        x = random.randint(WIDTH // 3, WIDTH * 2 // 3)
        y = random.randint(HEIGHT // 2, HEIGHT * 3 // 4)
        r = random.randint(15, 40)
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=(255, 0, 0, 180))

    # Add color scale legend
    legend_data = [
        ("Light", (0, 255, 0, 150)),
        ("Moderate", (255, 255, 0, 150)),
        ("Heavy", (255, 165, 0, 150)),
        ("Extreme", (255, 0, 0, 180))
    ]

    legend_x = WIDTH - 120
    legend_y = 20
    for i, (label, color) in enumerate(legend_data):
        y_pos = legend_y + i * 30
        draw.rectangle([legend_x, y_pos, legend_x + 100, y_pos + 25],
                      fill=color, outline=(0, 0, 0, 255), width=1)
        draw.text((legend_x + 5, y_pos + 5), label, fill=(0, 0, 0, 255))

    img.save('examples/3_precipitation.png')
    print("Created: examples/3_precipitation.png")

# ============================================================================
# Example 4: Calibration Pattern
# ============================================================================

def create_calibration_pattern():
    """Create a calibration pattern with measurement markers"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw background with semi-transparent fill
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(240, 240, 240, 100))

    # Draw measurement rulers
    # Top ruler
    for i in range(0, WIDTH, 50):
        height = 20 if i % 100 == 0 else 10
        draw.line([(i, 0), (i, height)], fill=(0, 0, 0, 255), width=2)
        if i % 100 == 0:
            draw.text((i + 5, 5), str(i), fill=(0, 0, 0, 255))

    # Left ruler
    for i in range(0, HEIGHT, 50):
        width = 20 if i % 100 == 0 else 10
        draw.line([(0, i), (width, i)], fill=(0, 0, 0, 255), width=2)
        if i % 100 == 0:
            draw.text((5, i + 5), str(i), fill=(0, 0, 0, 255))

    # Draw diagonal line for measurement testing
    draw.line([(100, 200), (700, 1000)], fill=(255, 0, 0, 255), width=5)

    # Add endpoint markers
    endpoints = [(100, 200), (700, 1000)]
    for x, y in endpoints:
        draw.ellipse([x - 15, y - 15, x + 15, y + 15],
                    fill=(255, 0, 0, 200), outline=(0, 0, 0, 255), width=3)
        draw.text((x + 20, y - 10), f"({x},{y})", fill=(0, 0, 0, 255))

    # Calculate and display expected distance
    dx = 700 - 100
    dy = 1000 - 200
    distance = (dx**2 + dy**2)**0.5

    mid_x, mid_y = (100 + 700) // 2, (200 + 1000) // 2
    draw.rectangle([mid_x - 100, mid_y - 30, mid_x + 100, mid_y + 30],
                  fill=(255, 255, 255, 230), outline=(0, 0, 0, 255), width=2)
    draw.text((mid_x - 90, mid_y - 20), f"Expected:", fill=(0, 0, 0, 255))
    draw.text((mid_x - 90, mid_y), f"{distance:.2f} px", fill=(255, 0, 0, 255))

    # Draw scale reference boxes
    box_sizes = [100, 200, 300]
    start_y = 100
    for size in box_sizes:
        x = WIDTH - size - 50
        draw.rectangle([x, start_y, x + size, start_y + size],
                      outline=(0, 0, 255, 255), width=3)
        draw.text((x + 5, start_y + 5), f"{size}x{size}px",
                 fill=(0, 0, 255, 255))
        start_y += size + 50

    img.save('examples/4_calibration.png')
    print("Created: examples/4_calibration.png")

# ============================================================================
# Example 5: Simple Semi-Transparent Overlay
# ============================================================================

def create_simple_overlay():
    """Create a simple semi-transparent overlay with shapes"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw large semi-transparent regions
    # North region (blue)
    draw.rectangle([0, 0, WIDTH, HEIGHT // 3],
                  fill=(100, 150, 255, 120))

    # Central region (green)
    draw.rectangle([0, HEIGHT // 3, WIDTH, HEIGHT * 2 // 3],
                  fill=(100, 255, 100, 120))

    # South region (yellow)
    draw.rectangle([0, HEIGHT * 2 // 3, WIDTH, HEIGHT],
                  fill=(255, 255, 100, 120))

    # Add some markers
    marker_positions = [
        (WIDTH // 4, HEIGHT // 6, "North Point"),
        (WIDTH // 2, HEIGHT // 2, "Center Point"),
        (WIDTH * 3 // 4, HEIGHT * 5 // 6, "South Point"),
    ]

    for x, y, label in marker_positions:
        # Draw marker
        draw.ellipse([x - 20, y - 20, x + 20, y + 20],
                    fill=(255, 0, 0, 200), outline=(255, 255, 255, 255), width=3)
        # Draw label background
        draw.rectangle([x - 60, y + 30, x + 60, y + 55],
                      fill=(255, 255, 255, 230), outline=(0, 0, 0, 255), width=2)
        draw.text((x - 55, y + 35), label, fill=(0, 0, 0, 255))

    img.save('examples/5_simple_overlay.png')
    print("Created: examples/5_simple_overlay.png")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("Generating example PNG overlay images...")
    print()

    create_grid_pattern()
    create_heat_map()
    create_precipitation_map()
    create_calibration_pattern()
    create_simple_overlay()

    print()
    print("All example images created successfully!")
    print("Check the 'examples' directory for the PNG files.")
