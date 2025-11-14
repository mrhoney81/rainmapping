# UK Climate Interactive Viewer - Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [Data Preprocessing](#data-preprocessing)
4. [Coordinate Mapping System](#coordinate-mapping-system)
5. [Frontend Implementation Plan](#frontend-implementation-plan)
6. [Deployment Guide](#deployment-guide)
7. [Complete Preprocessing Code](#complete-preprocessing-code)

---

## Project Overview

### Goal
Create an interactive web-based viewer for UK climate data (rainfall and sunshine) that allows users to:
- Explore monthly climate patterns from 2014-2023
- View month-by-month changes with a slider
- Compare individual months or view multi-year averages
- See specific locations on the map (with ability to add custom locations)
- Host everything as a static site on GitHub Pages (no server needed!)

### Key Features
- **Time Series Navigation**: Slider to move through years and months
- **Monthly Averages**: Pre-computed averages for each calendar month across all years
- **Location Markers**: Display UK towns/villages with option to add custom coordinates
- **Play/Pause Animation**: Automatically cycle through time periods
- **Static Hosting**: All data pre-rendered as images for fast, free hosting

### Data Source
- **CEDA HADUKGrid 1km dataset**
- Monthly rainfall and sunshine data
- 1km resolution across the UK
- British National Grid (EPSG:27700) coordinate system

---

## Technical Architecture

### Overall Approach

The project uses a **pre-rendering strategy**:
1. **Python preprocessing** generates all visualizations as PNG images
2. **Static HTML/CSS/JavaScript** frontend displays pre-rendered images
3. **No backend required** - everything is static files on GitHub Pages

### Why This Works

✅ **Static hosting**: Free forever on GitHub Pages  
✅ **Fast loading**: Compressed PNGs load in <500ms  
✅ **Scalable**: Can handle 10+ years of data (~70-140 MB)  
✅ **Offline capable**: Can add PWA features  
✅ **Shareable**: Direct URLs to specific views  
✅ **Maintainable**: Just regenerate PNGs when you get new data

### Data Storage Estimates

**Per Image:**
- RGB array: ~1000x1500 pixels at 1km resolution
- Compressed PNG: ~300-800 KB per image

**Total Storage:**
- 120 monthly maps (10 years × 12 months): ~60 MB
- 12 monthly averages: ~6 MB
- **Total: ~70 MB** (well within GitHub's 1GB limit)

### Directory Structure

```
uk-climate-viewer/
├── index.html              # Main application
├── style.css               # Styling
├── app.js                  # JavaScript logic
├── data/
│   ├── images/
│   │   ├── 2014/
│   │   │   ├── 01.png, 02.png, ..., 12.png
│   │   ├── 2015/
│   │   │   ├── 01.png, 02.png, ..., 12.png
│   │   └── ... (through 2023)
│   ├── averages/
│   │   ├── 01.png (Jan average across all years)
│   │   ├── 02.png (Feb average)
│   │   └── ... (12 total)
│   ├── key.png             # Bivariate legend
│   ├── key_transparent.png # Transparent legend
│   ├── metadata.json       # Geographic extent & dimensions
│   └── locations.json      # UK settlements database
└── README.md
```

---

## Data Preprocessing

### Color Scheme: Bivariate Mapping

The visualization uses a **bivariate color scheme** to show both rainfall and sunshine:

```
               More Sun ↑
         │ Low │ Med │ High │
    ─────┼─────┼─────┼─────┤
    High │ 🟨  │ 🟧  │ ⬛  │  More
    ─────┼─────┼─────┼─────┤  Rain
    Med  │ 🟨  │ ⬜  │ 🟦  │  →
    ─────┼─────┼─────┼─────┤
    Low  │ ⬜  │ 🔵  │ 🔵  │
    ─────┴─────┴─────┴─────┘
```

**Color Palette:**
```python
COLORS = [
    "#f3f3f3",  # Low rain, Low sun (very light grey)
    "#b4d3e1",  # Med rain, Low sun (light blue)
    "#509dc2",  # High rain, Low sun (medium blue)
    "#f3e6b3",  # Low rain, Med sun (light yellow)
    "#b3b3b3",  # Med rain, Med sun (grey)
    "#376387",  # High rain, Med sun (dark blue)
    "#f3b300",  # Low rain, High sun (bright yellow/orange)
    "#b36600",  # Med rain, High sun (orange)
    "#000000"   # High rain, High sun (black)
]
```

### Processing Pipeline

1. **Load monthly NetCDF files** for rain and sunshine
2. **Calculate tertiles** for that specific month (divide data into 3 equal groups)
3. **Assign colors** based on tertile combinations (9 possible combinations)
4. **Create RGB array** with vectorized numpy operations
5. **Flip vertically** to match image coordinate system (PIL expects y-down)
6. **Save as optimized PNG** with maximum compression
7. **Calculate monthly averages** across all years for each calendar month
8. **Generate metadata** with geographic extent for coordinate mapping

### Key Preprocessing Decisions

**Tertile Calculation:**
- Calculated **per-month** (not globally) to highlight spatial variation within each time period
- Uses `np.percentile` at 33.3% and 66.6% boundaries

**Image Orientation:**
- British National Grid has **y increasing upward** (north)
- PIL Images have **y increasing downward** (standard image format)
- Solution: `np.flipud()` to flip array before saving

**Compression:**
- PNG with `optimize=True` and `compress_level=9`
- Could use WebP for 50% smaller files if browser support is acceptable

---

## Coordinate Mapping System

### The Challenge

We need to accurately map **British National Grid coordinates** (e.g., Bristol at x=359000, y=173000) to **pixel coordinates** on our PNG images.

### The Solution

#### 1. Store Geographic Extent

When generating images, we record the exact real-world coordinates the image represents:

```python
extent_info = {
    "x_min": float(x_coords.min()),  # e.g., 0
    "x_max": float(x_coords.max()),  # e.g., 700000
    "y_min": float(y_coords.min()),  # e.g., 0
    "y_max": float(y_coords.max()),  # e.g., 1300000
    "crs": "EPSG:27700",
    "resolution_meters": 1000
}
```

This is saved in `metadata.json`.

#### 2. Frontend Coordinate Transformation

JavaScript function to convert BNG to pixel coordinates:

```javascript
function britishGridToPixel(bng_x, bng_y, canvasWidth, canvasHeight) {
    const {x_min, x_max, y_min, y_max} = metadata.extent;
    
    // Linear interpolation for x
    const pixel_x = ((bng_x - x_min) / (x_max - x_min)) * canvasWidth;
    
    // Y is flipped (image origin is top-left, BNG origin is bottom-left)
    const pixel_y = canvasHeight - ((bng_y - y_min) / (y_max - y_min)) * canvasHeight;
    
    return [pixel_x, pixel_y];
}
```

#### 3. Maintaining Aspect Ratio

Canvas must match data aspect ratio:

```javascript
const dataAspect = (metadata.extent.y_max - metadata.extent.y_min) / 
                   (metadata.extent.x_max - metadata.extent.x_min);
canvas.height = canvas.width * dataAspect;
```

### Verification Strategy

**Create test image with known locations:**
```python
test_locations = {
    'Bristol': [359000, 173000],
    'London': [530000, 180000]
}

# Mark locations with red crosses in the image
for name, (x, y) in test_locations.items():
    x_idx = np.argmin(np.abs(x_coords - x))
    y_idx = np.argmin(np.abs(y_coords - y))
    rgb_array[y_idx-2:y_idx+3, x_idx, :] = [1, 0, 0]  # Red vertical
    rgb_array[y_idx, x_idx-2:x_idx+3, :] = [1, 0, 0]  # Red horizontal
```

**Test on frontend:**
- Plot same locations using coordinate transform
- Verify markers align with crosses
- Test edge cases (map corners)

---

## Frontend Implementation Plan

### HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>UK Climate Viewer</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <!-- Controls -->
        <div class="controls">
            <div class="view-toggle">
                <button id="monthlyBtn" class="active">Monthly Data</button>
                <button id="averagesBtn">Monthly Averages</button>
            </div>
            
            <div class="time-controls">
                <label for="yearSlider">Year: <span id="yearValue">2023</span></label>
                <input type="range" id="yearSlider" min="2014" max="2023" value="2023">
                
                <label for="monthSlider">Month: <span id="monthValue">January</span></label>
                <input type="range" id="monthSlider" min="1" max="12" value="1">
                
                <button id="playBtn">▶ Play</button>
            </div>
            
            <div class="location-controls">
                <input type="text" id="locationSearch" placeholder="Search locations...">
                <button id="addCustomBtn">Add Custom Location</button>
            </div>
        </div>
        
        <!-- Map Display -->
        <div class="map-container">
            <canvas id="mapCanvas"></canvas>
            <img src="data/key_transparent.png" class="legend" alt="Color Key">
        </div>
        
        <!-- Location List -->
        <div class="locations-panel">
            <h3>Locations</h3>
            <div id="locationList"></div>
        </div>
    </div>
    
    <script src="app.js"></script>
</body>
</html>
```

### JavaScript Core Features

```javascript
// --- INITIALIZATION ---
let metadata;
let locations = [];
let currentYear = 2023;
let currentMonth = 1;
let viewMode = 'monthly'; // or 'averages'
let isPlaying = false;

// Load metadata and locations
async function init() {
    metadata = await fetch('data/metadata.json').then(r => r.json());
    locations = await fetch('data/locations.json').then(r => r.json());
    
    setupCanvas();
    setupEventListeners();
    updateDisplay();
}

// --- DISPLAY FUNCTIONS ---
function updateDisplay() {
    const imagePath = viewMode === 'monthly' 
        ? `data/images/${currentYear}/${String(currentMonth).padStart(2, '0')}.png`
        : `data/averages/${String(currentMonth).padStart(2, '0')}.png`;
    
    const img = new Image();
    img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        drawLocations();
    };
    img.src = imagePath;
}

function drawLocations() {
    locations.forEach(loc => {
        if (!loc.visible) return;
        
        const [px, py] = britishGridToPixel(
            loc.x, loc.y, 
            canvas.width, canvas.height
        );
        
        // Draw marker
        ctx.beginPath();
        ctx.arc(px, py, 5, 0, 2 * Math.PI);
        ctx.fillStyle = 'red';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();
        
        // Draw label
        ctx.font = 'bold 12px Arial';
        ctx.fillStyle = 'black';
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.strokeText(loc.name, px + 8, py + 4);
        ctx.fillText(loc.name, px + 8, py + 4);
    });
}

// --- COORDINATE CONVERSION ---
function britishGridToPixel(bng_x, bng_y, canvasWidth, canvasHeight) {
    const {x_min, x_max, y_min, y_max} = metadata.extent;
    
    const pixel_x = ((bng_x - x_min) / (x_max - x_min)) * canvasWidth;
    const pixel_y = canvasHeight - ((bng_y - y_min) / (y_max - y_min)) * canvasHeight;
    
    return [pixel_x, pixel_y];
}

function pixelToBritishGrid(pixel_x, pixel_y, canvasWidth, canvasHeight) {
    const {x_min, x_max, y_min, y_max} = metadata.extent;
    
    const bng_x = x_min + (pixel_x / canvasWidth) * (x_max - x_min);
    const bng_y = y_min + ((canvasHeight - pixel_y) / canvasHeight) * (y_max - y_min);
    
    return [bng_x, bng_y];
}

// --- ANIMATION ---
function playAnimation() {
    if (isPlaying) {
        currentMonth++;
        if (currentMonth > 12) {
            currentMonth = 1;
            if (viewMode === 'monthly') {
                currentYear++;
                if (currentYear > metadata.years[metadata.years.length - 1]) {
                    currentYear = metadata.years[0];
                }
            }
        }
        updateDisplay();
        updateUI();
        setTimeout(playAnimation, 500); // 500ms per frame
    }
}

// --- EVENT LISTENERS ---
function setupEventListeners() {
    document.getElementById('yearSlider').addEventListener('input', (e) => {
        currentYear = parseInt(e.target.value);
        updateDisplay();
    });
    
    document.getElementById('monthSlider').addEventListener('input', (e) => {
        currentMonth = parseInt(e.target.value);
        updateDisplay();
    });
    
    document.getElementById('playBtn').addEventListener('click', () => {
        isPlaying = !isPlaying;
        if (isPlaying) playAnimation();
    });
    
    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const px = (e.clientX - rect.left) * (canvas.width / rect.width);
        const py = (e.clientY - rect.top) * (canvas.height / rect.height);
        
        const [bng_x, bng_y] = pixelToBritishGrid(px, py, canvas.width, canvas.height);
        addCustomLocation(bng_x, bng_y);
    });
}

// Initialize on page load
init();
```

### Location Data

**Sources:**
1. **OS Open Names** (free UK places database)
2. Filter to important settlements (cities, large towns)
3. Store ~500-2000 locations in `locations.json`

**Format:**
```json
[
  {
    "name": "London",
    "x": 530000,
    "y": 180000,
    "type": "city"
  },
  {
    "name": "Bristol",
    "x": 359000,
    "y": 173000,
    "type": "city"
  }
]
```

### Advanced Features

- **URL Parameters**: Share specific views (`?year=2022&month=7`)
- **Fuzzy Search**: Use Fuse.js for location search
- **Local Storage**: Save custom locations
- **Keyboard Shortcuts**: Arrow keys for navigation
- **Mobile Responsive**: Touch-friendly controls
- **Export**: Download data for selected location as CSV

---

## Deployment Guide

### GitHub Pages Setup

1. **Create Repository:**
   ```bash
   git init uk-climate-viewer
   cd uk-climate-viewer
   ```

2. **Add Files:**
   ```bash
   # Copy web_output contents to data/
   mkdir data
   cp -r web_output/* data/
   
   # Add frontend files
   # index.html, style.css, app.js
   ```

3. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/username/uk-climate-viewer.git
   git push -u origin main
   ```

4. **Enable GitHub Pages:**
   - Go to repository Settings
   - Pages section
   - Source: Deploy from branch `main`
   - Folder: `/ (root)`
   - Save

5. **Access:**
   - Site will be live at: `https://username.github.io/uk-climate-viewer/`

### Optimization Tips

**Image Loading:**
```javascript
// Lazy load images
const imageCache = new Map();

async function loadImage(path) {
    if (imageCache.has(path)) {
        return imageCache.get(path);
    }
    
    const img = new Image();
    img.src = path;
    await img.decode();
    imageCache.set(path, img);
    return img;
}
```

**Preload Adjacent Months:**
```javascript
// Preload next/previous months for smooth navigation
function preloadAdjacentImages() {
    const nextMonth = currentMonth === 12 ? 1 : currentMonth + 1;
    const prevMonth = currentMonth === 1 ? 12 : currentMonth - 1;
    
    loadImage(`data/images/${currentYear}/${String(nextMonth).padStart(2, '0')}.png`);
    loadImage(`data/images/${currentYear}/${String(prevMonth).padStart(2, '0')}.png`);
}
```

---

## Complete Preprocessing Code

### Main Preprocessing Script

```python
# --- PREPROCESSING SCRIPT: GENERATE ALL IMAGES FOR WEB VIEWER ---
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import xarray as xr
import os
import json
from PIL import Image
from datetime import datetime

print("=" * 60)
print("UK CLIMATE MAP PREPROCESSING SCRIPT")
print("=" * 60)

# --- CONFIGURATION ---
YEARS_TO_PROCESS = list(range(2014, 2024))  # Adjust to your available data
OUTPUT_BASE_DIR = "web_output"
DATA_DIR = "Data/CEDA Data"

# Color scheme
COLORS = [
    "#f3f3f3", "#b4d3e1", "#509dc2",
    "#f3e6b3", "#b3b3b3", "#376387",
    "#f3b300", "#b36600", "#000000"
]
COLOR_TO_RGB = {color: mcolors.to_rgb(color) for color in COLORS}

print(f"\nProcessing years: {YEARS_TO_PROCESS[0]} to {YEARS_TO_PROCESS[-1]}")
print(f"Output directory: {OUTPUT_BASE_DIR}")

# --- 1. CREATE DIRECTORY STRUCTURE ---
print("\n--- Step 1: Creating directory structure ---")

os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_BASE_DIR}/images", exist_ok=True)
os.makedirs(f"{OUTPUT_BASE_DIR}/averages", exist_ok=True)

for year in YEARS_TO_PROCESS:
    os.makedirs(f"{OUTPUT_BASE_DIR}/images/{year}", exist_ok=True)

print("✓ Directories created")

# --- 2. GENERATE BIVARIATE KEY ---
print("\n--- Step 2: Generating bivariate key ---")

color_grid = np.array(COLORS).reshape(3, 3)
rgb_grid = np.array([[mcolors.to_rgb(c) for c in row] for row in color_grid])
rgb_grid = np.flipud(rgb_grid)

# Version 1: With white background
fig, ax = plt.subplots(figsize=(3, 3))
ax.imshow(rgb_grid, interpolation='nearest')
ax.set_xlabel('More rain →', fontsize=12, fontweight='bold')
ax.set_ylabel('More sun →', fontsize=12, fontweight='bold')
ax.set_xticks([])
ax.set_yticks([])
ax.spines[['top', 'right', 'bottom', 'left']].set_visible(True)
ax.spines[['top', 'right', 'bottom', 'left']].set_linewidth(2)
ax.spines[['top', 'right', 'bottom', 'left']].set_color('black')
plt.tight_layout()
plt.savefig(f"{OUTPUT_BASE_DIR}/key.png", dpi=150, bbox_inches='tight', pad_inches=0.1, 
            transparent=False, facecolor='white')
plt.close()

# Version 2: With transparent background
fig, ax = plt.subplots(figsize=(3, 3))
ax.imshow(rgb_grid, interpolation='nearest')
ax.set_xlabel('More rain →', fontsize=12, fontweight='bold')
ax.set_ylabel('More sun →', fontsize=12, fontweight='bold')
ax.set_xticks([])
ax.set_yticks([])
ax.spines[['top', 'right', 'bottom', 'left']].set_visible(True)
ax.spines[['top', 'right', 'bottom', 'left']].set_linewidth(2)
ax.spines[['top', 'right', 'bottom', 'left']].set_color('black')
plt.tight_layout()
plt.savefig(f"{OUTPUT_BASE_DIR}/key_transparent.png", dpi=150, bbox_inches='tight', 
            pad_inches=0.1, transparent=True)
plt.close()

print("✓ Bivariate keys saved (key.png and key_transparent.png)")

# --- 3. HELPER FUNCTION TO CREATE RGB ARRAY ---
def create_rgb_array(rain_values, sun_values, colors, color_to_rgb):
    """
    Vectorized function to create RGB array from rain and sun data.
    """
    n_y, n_x = rain_values.shape
    rgb_array = np.ones((n_y, n_x, 3))
    
    # Remove NaN values for tertile calculation
    rain_flat = rain_values.flatten()
    sun_flat = sun_values.flatten()
    
    rain_valid = rain_flat[~np.isnan(rain_flat)]
    sun_valid = sun_flat[~np.isnan(sun_flat)]
    
    if len(rain_valid) == 0 or len(sun_valid) == 0:
        return rgb_array  # Return white image if no valid data
    
    # Calculate tertile boundaries
    rain_tertile_bounds = np.percentile(rain_valid, [100/3, 200/3])
    sun_tertile_bounds = np.percentile(sun_valid, [100/3, 200/3])
    
    # Assign tertiles to 2D arrays
    rain_tert_2d = np.ones_like(rain_values) * np.nan
    rain_tert_2d[rain_values <= rain_tertile_bounds[0]] = 1
    rain_tert_2d[(rain_values > rain_tertile_bounds[0]) & (rain_values <= rain_tertile_bounds[1])] = 2
    rain_tert_2d[rain_values > rain_tertile_bounds[1]] = 3
    
    sun_tert_2d = np.ones_like(sun_values) * np.nan
    sun_tert_2d[sun_values <= sun_tertile_bounds[0]] = 1
    sun_tert_2d[(sun_values > sun_tertile_bounds[0]) & (sun_values <= sun_tertile_bounds[1])] = 2
    sun_tert_2d[sun_values > sun_tertile_bounds[1]] = 3
    
    # Create color index array
    valid_mask = ~np.isnan(rain_values) & ~np.isnan(sun_values)
    color_idx = np.zeros_like(rain_values)
    color_idx[valid_mask] = (sun_tert_2d[valid_mask] - 1) * 3 + (rain_tert_2d[valid_mask] - 1)
    
    # Apply colors where we have data
    for i in range(9):
        mask = (color_idx == i) & valid_mask
        rgb_array[mask] = color_to_rgb[colors[i]]
    
    # CRITICAL FIX: Flip vertically so PIL Image has correct orientation
    # BNG has y increasing upward, but PIL Image has y increasing downward
    rgb_array = np.flipud(rgb_array)
    
    return rgb_array

# --- 4. PROCESS MONTHLY DATA FOR EACH YEAR ---
print("\n--- Step 3: Processing monthly data ---")

# Storage for calculating averages
monthly_rain_sum = [[] for _ in range(12)]  # 12 months
monthly_sun_sum = [[] for _ in range(12)]

x_coords = None
y_coords = None
extent_info = None

total_images = 0
failed_images = 0

for year in YEARS_TO_PROCESS:
    print(f"\n  Processing {year}...")
    
    # Define file paths
    year_start = f"{year}01"
    year_end = f"{year}12"
    rain_file = f"{DATA_DIR}/rainfall_hadukgrid_uk_1km_mon_{year_start}-{year_end}.nc"
    sun_file = f"{DATA_DIR}/sun_hadukgrid_uk_1km_mon_{year_start}-{year_end}.nc"
    
    # Check if files exist
    if not os.path.exists(rain_file) or not os.path.exists(sun_file):
        print(f"    ⚠ Data files for {year} not found, skipping...")
        failed_images += 12
        continue
    
    try:
        # Load data
        nc_rain = xr.open_dataset(rain_file)
        nc_sun = xr.open_dataset(sun_file)
        
        # Get coordinates (only once)
        if x_coords is None:
            x_coords = nc_rain['projection_x_coordinate'].values
            y_coords = nc_rain['projection_y_coordinate'].values
            
            # Store extent information
            extent_info = {
                "x_min": float(x_coords.min()),
                "x_max": float(x_coords.max()),
                "y_min": float(y_coords.min()),
                "y_max": float(y_coords.max()),
                "crs": "EPSG:27700",
                "resolution_meters": 1000
            }
        
        # Process each month
        for month_idx in range(12):
            month_num = month_idx + 1
            month_str = f"{month_num:02d}"
            
            try:
                # Extract data for this month
                rain_values = nc_rain['rainfall'].isel(time=month_idx).values
                sun_values = nc_sun['sun'].isel(time=month_idx).values
                
                # Store for average calculation
                monthly_rain_sum[month_idx].append(rain_values)
                monthly_sun_sum[month_idx].append(sun_values)
                
                # Create RGB array
                rgb_array = create_rgb_array(rain_values, sun_values, COLORS, COLOR_TO_RGB)
                
                # Convert to PIL Image and save
                img = Image.fromarray((rgb_array * 255).astype('uint8'))
                output_path = f"{OUTPUT_BASE_DIR}/images/{year}/{month_str}.png"
                img.save(output_path, optimize=True, compress_level=9)
                
                total_images += 1
                
            except Exception as e:
                print(f"    ✗ Failed to process {year}-{month_str}: {e}")
                failed_images += 1
        
        print(f"    ✓ {year} complete (12 months)")
        
        # Close datasets
        nc_rain.close()
        nc_sun.close()
        
    except Exception as e:
        print(f"    ✗ Failed to load {year} data: {e}")
        failed_images += 12

print(f"\n✓ Monthly images complete: {total_images} generated, {failed_images} failed")

# --- 5. CALCULATE AND SAVE MONTHLY AVERAGES ---
print("\n--- Step 4: Calculating monthly averages ---")

month_names = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

for month_idx in range(12):
    month_num = month_idx + 1
    month_str = f"{month_num:02d}"
    month_name = month_names[month_idx]
    
    if len(monthly_rain_sum[month_idx]) == 0:
        print(f"  ⚠ No data for {month_name}, skipping...")
        continue
    
    # Calculate mean across all years
    rain_mean = np.mean(np.stack(monthly_rain_sum[month_idx]), axis=0)
    sun_mean = np.mean(np.stack(monthly_sun_sum[month_idx]), axis=0)
    
    # Create RGB array
    rgb_array = create_rgb_array(rain_mean, sun_mean, COLORS, COLOR_TO_RGB)
    
    # Save
    img = Image.fromarray((rgb_array * 255).astype('uint8'))
    output_path = f"{OUTPUT_BASE_DIR}/averages/{month_str}.png"
    img.save(output_path, optimize=True, compress_level=9)
    
    print(f"  ✓ {month_name} average created (based on {len(monthly_rain_sum[month_idx])} years)")

# --- 6. CREATE METADATA.JSON ---
print("\n--- Step 5: Creating metadata.json ---")

if extent_info is None:
    print("  ✗ No data was processed, cannot create metadata!")
else:
    # Get actual image dimensions from one of the saved images
    sample_img = Image.open(f"{OUTPUT_BASE_DIR}/images/{YEARS_TO_PROCESS[0]}/01.png")
    image_width, image_height = sample_img.size
    
    metadata = {
        "extent": extent_info,
        "image_dimensions": {
            "width": image_width,
            "height": image_height
        },
        "years": [y for y in YEARS_TO_PROCESS if os.path.exists(f"{OUTPUT_BASE_DIR}/images/{y}/01.png")],
        "months": list(range(1, 13)),
        "month_names": month_names,
        "colors": COLORS,
        "generated_at": datetime.now().isoformat(),
        "total_images": total_images,
        "data_source": "CEDA HADUKGrid 1km"
    }
    
    with open(f"{OUTPUT_BASE_DIR}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✓ metadata.json created")
    print(f"\nMetadata summary:")
    print(f"  - Image dimensions: {image_width} x {image_height}")
    print(f"  - Extent: X({extent_info['x_min']:.0f} to {extent_info['x_max']:.0f}), "
          f"Y({extent_info['y_min']:.0f} to {extent_info['y_max']:.0f})")
    print(f"  - Years available: {metadata['years']}")

# --- 7. CALCULATE AND DISPLAY FILE SIZES ---
print("\n--- Step 6: Calculating total file sizes ---")

def get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total += os.path.getsize(filepath)
    return total

images_size = get_dir_size(f"{OUTPUT_BASE_DIR}/images") / (1024 * 1024)  # MB
averages_size = get_dir_size(f"{OUTPUT_BASE_DIR}/averages") / (1024 * 1024)  # MB
total_size = images_size + averages_size

print(f"  - Monthly images: {images_size:.1f} MB")
print(f"  - Monthly averages: {averages_size:.1f} MB")
print(f"  - Total: {total_size:.1f} MB")

# --- 8. SUMMARY ---
print("\n" + "=" * 60)
print("PREPROCESSING COMPLETE!")
print("=" * 60)
print(f"\nOutput directory: {OUTPUT_BASE_DIR}/")
print(f"  ├── images/")
print(f"  │   ├── {YEARS_TO_PROCESS[0]}/ ... {YEARS_TO_PROCESS[-1]}/")
print(f"  │       └── 01.png ... 12.png")
print(f"  ├── averages/")
print(f"  │   └── 01.png ... 12.png")
print(f"  ├── key.png")
print(f"  ├── key_transparent.png")
print(f"  └── metadata.json")
print(f"\nReady for web deployment!")
print("=" * 60)
```

### Usage Instructions

1. **Adjust configuration:**
   ```python
   YEARS_TO_PROCESS = list(range(2014, 2024))
   OUTPUT_BASE_DIR = "web_output"
   DATA_DIR = "Data/CEDA Data"
   ```

2. **Ensure data files follow naming pattern:**
   ```
   rainfall_hadukgrid_uk_1km_mon_YYYYMM-YYYYMM.nc
   sun_hadukgrid_uk_1km_mon_YYYYMM-YYYYMM.nc
   ```

3. **Run the script:**
   ```bash
   python preprocess_climate_data.py
   ```

4. **Output:**
   - `web_output/` directory with all images
   - `metadata.json` with geographic extent
   - Bivariate keys (opaque and transparent)

---

## Next Steps

1. ✅ **Run preprocessing** to generate all images
2. ⏳ **Create locations.json** with UK settlements (use OS Open Names)
3. ⏳ **Build frontend** (HTML/CSS/JavaScript)
4. ⏳ **Test coordinate mapping** with known locations
5. ⏳ **Deploy to GitHub Pages**
6. ⏳ **Add advanced features** (animation, search, etc.)

---

## Technical Notes

### Performance Optimizations

- **Vectorized operations**: Using numpy boolean masking instead of loops
- **Image compression**: PNG with optimize=True (could use WebP for 50% reduction)
- **Lazy loading**: Frontend loads images on demand
- **Caching**: Browser caches images automatically

### Browser Compatibility

- **Canvas API**: Widely supported (IE9+)
- **PNG images**: Universal support
- **JavaScript**: ES6+ features (use Babel if targeting older browsers)

### Potential Issues & Solutions

**Problem:** Images too large  
**Solution:** Use WebP format or reduce DPI

**Problem:** Slow loading on mobile  
**Solution:** Create lower-resolution versions for mobile

**Problem:** Coordinates not aligning  
**Solution:** Verify aspect ratio is maintained, check flipud() is applied

**Problem:** GitHub Pages 100 MB file limit  
**Solution:** Split into multiple repositories or use Git LFS

---

## Credits & License

**Data Source:** CEDA HADUKGrid 1km dataset  
**Coordinate System:** British National Grid (EPSG:27700)  
**Color Scheme:** Bivariate mapping (custom palette)

**Author:** [Your Name]  
**Date:** November 2025  
**License:** [Your License]

---

## Contact & Support

For questions or issues:
- GitHub: [Your GitHub]
- Email: [Your Email]

---

*End of Documentation*
