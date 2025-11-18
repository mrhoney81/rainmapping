# Test Harness Example Images

This directory contains example PNG overlay images for testing the test harness (`test-harness.html`).

## How to Use These Examples

1. Open `test-harness.html` in your web browser
2. Click "Upload PNG Overlay" and select one of the example images below
3. Enter the suggested bounds for that image (provided below)
4. Click "Update Overlay Position"
5. Click on the map to place measurement points
6. Take a screenshot to capture the result

---

## Example Images

### 1. Grid Pattern (`1_grid_pattern.png`)

**Description:** A coordinate grid with corner markers and a center crosshair. Useful for alignment testing.

**Features:**
- Blue grid lines every 100 pixels
- Red corner markers labeled NW, NE, SW, SE
- Center crosshair with red marker
- Green reference box (200px wide)

**Suggested Bounds:**
- North: `59.0`
- South: `50.0`
- West: `-7.0`
- East: `2.0`

**Test Ideas:**
- Place points on the corner markers to measure diagonal distance
- Place points on the green reference box (should measure ~200px)
- Use the center crosshair as a reference point

---

### 2. Heat Map (`2_heat_map.png`)

**Description:** A vertical temperature-style gradient with hot spots. Simulates temperature or intensity data.

**Features:**
- Blue (cold) to red (hot) vertical gradient
- Circular "hot spot" regions
- Color scale legend on the left

**Suggested Bounds:**
- North: `58.5`
- South: `49.5`
- West: `-6.5`
- East: `1.5`

**Test Ideas:**
- Measure distances between hot spots
- Test overlay opacity to see the map through the gradient
- Place points on different temperature zones

---

### 3. Precipitation Map (`3_precipitation.png`)

**Description:** Radar/precipitation style overlay with varying intensity regions.

**Features:**
- Green (light rain) to red (extreme rain) zones
- Overlapping precipitation cells
- Intensity legend on the right

**Suggested Bounds:**
- North: `59.0`
- South: `49.0`
- West: `-7.5`
- East: `2.5`

**Test Ideas:**
- Measure distances between precipitation cells
- Test different opacity levels for realistic radar appearance
- Compare geographic vs pixel distances for cell sizes

---

### 4. Calibration Pattern (`4_calibration.png`)

**Description:** Precision calibration pattern with rulers and measurement references.

**Features:**
- Pixel rulers along top and left edges (50px increments)
- Red diagonal line with marked endpoints at (100, 200) and (700, 1000)
- Expected pixel distance displayed: **1000 pixels**
- Reference boxes of 100x100, 200x200, and 300x300 pixels

**Suggested Bounds:**
- North: `60.0`
- South: `49.0`
- West: `-8.0`
- East: `2.0`

**Test Ideas:**
- Place points on the red line endpoints - should measure ~1000 pixels
- Measure the reference boxes to verify pixel accuracy
- Use the rulers to validate coordinate transformations

**Expected Measurements:**
- Red line endpoints: **1000 pixels** (diagonal)
- Small blue box: **100 pixels** (side length)
- Medium blue box: **200 pixels** (side length)
- Large blue box: **300 pixels** (side length)

---

### 5. Simple Overlay (`5_simple_overlay.png`)

**Description:** Clean three-region overlay with labeled markers.

**Features:**
- Three horizontal zones (blue north, green center, yellow south)
- Three labeled marker points
- Semi-transparent design

**Suggested Bounds:**
- North: `58.0`
- South: `50.0`
- West: `-6.0`
- East: `1.0`

**Test Ideas:**
- Measure distances between the three marked points
- Test how the semi-transparent regions appear over different map features
- Use for basic alignment verification

---

## Tips for Testing

### Adjusting Overlay Position

If the overlay doesn't align perfectly:

1. Adjust the North/South/East/West bounds incrementally
2. Use the opacity slider to see the map through the overlay
3. Look for recognizable geographic features to align with
4. Click "Update Overlay Position" after each adjustment

### Measurement Accuracy

- Zoom level affects pixel measurements - they update automatically
- Take screenshots at different zoom levels to compare
- The calibration pattern (#4) is best for verifying pixel accuracy
- Geographic distance is provided for reference but doesn't change with zoom

### Screenshot Quality

- Higher zoom = larger features in screenshot
- Lower opacity = more map visible through overlay
- Screenshots capture the exact view including markers and lines
- Download screenshots to keep a record of your tests

---

## Creating Your Own Test Images

Use the included `generate_examples.py` script as a template:

```bash
python3 generate_examples.py
```

You can modify the script to create custom test patterns for your specific needs.

---

## Recommended Testing Workflow

1. **Start with the Calibration Pattern (#4)**
   - Verify pixel measurements are accurate
   - Place points on the red line endpoints
   - Confirm you get ~1000 pixels distance

2. **Try the Simple Overlay (#5)**
   - Practice placing points
   - Get familiar with the controls
   - Test screenshot functionality

3. **Experiment with Realistic Data (#2 or #3)**
   - Test with heat map or precipitation patterns
   - Adjust opacity for best visibility
   - Measure features of interest

4. **Test Alignment with Grid Pattern (#1)**
   - Verify overlay positioning
   - Check corner alignment
   - Measure known distances

---

## Questions?

If you encounter issues or have questions about the test harness, refer to the instructions panel in `test-harness.html` or check the source code comments.

Happy testing! 🗺️
