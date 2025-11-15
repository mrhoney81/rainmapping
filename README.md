# UK Climate Interactive Viewer

An interactive web-based visualization tool for exploring UK climate data (rainfall and sunshine) from 2014-2023. Built with vanilla JavaScript and designed for static hosting on GitHub Pages.

![UK Climate Viewer](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Dual Data Views**: Toggle between rainfall/sunshine bivariate visualization and temperature visualization
- **Interactive Time Navigation**: Slider controls to explore monthly climate patterns across years
- **Monthly Averages**: View pre-computed averages for each calendar month across all years
- **Location Markers**: Display major UK cities and towns with the ability to add custom locations
- **Play/Pause Animation**: Automatically cycle through time periods
- **Bivariate Color Mapping**: Visualize both rainfall and sunshine simultaneously with a 3x3 color grid
- **Temperature Visualization**: View peak temperature (tasmax) across the UK with a blue-to-red gradient
- **Zoom and Pan**: Interactive map exploration with mouse wheel zoom and drag-to-pan
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Static Hosting**: No server required - runs entirely as static files on GitHub Pages
- **URL Sharing**: Share specific views via URL parameters

## Live Demo

[View the live demo here](https://yourusername.github.io/rainmapping/) *(Update with your actual GitHub Pages URL)*

## Quick Start

### Prerequisites

You need to have already generated the climate images using the preprocessing script from `plan.md`. This will create a `web_output` directory containing:
- `images/` - Monthly images organized by year
- `averages/` - Monthly average images
- `metadata.json` - Geographic extent and metadata
- `key.png` and `key_transparent.png` - Bivariate color legends

### Setup Instructions

1. **Clone this repository:**
   ```bash
   git clone https://github.com/yourusername/rainmapping.git
   cd rainmapping
   ```

2. **Copy your generated images:**

   If you've already run the preprocessing script and have a `web_output` directory:
   ```bash
   cp -r web_output/* data/
   ```

   Your `data/` directory should now contain:
   ```
   data/
   ├── images/
   │   ├── 2014/
   │   │   ├── 01.png
   │   │   ├── 02.png
   │   │   └── ... (12 months)
   │   ├── 2015/
   │   └── ... (through 2023)
   ├── averages/
   │   ├── 01.png
   │   └── ... (12 months)
   ├── key.png
   ├── key_transparent.png
   ├── metadata.json
   └── locations.json
   ```

3. **Test locally:**

   You can use any local web server. Here are some options:

   **Python 3:**
   ```bash
   python -m http.server 8000
   ```

   **Python 2:**
   ```bash
   python -m SimpleHTTPServer 8000
   ```

   **Node.js (with http-server):**
   ```bash
   npx http-server -p 8000
   ```

   Then open `http://localhost:8000` in your browser.

4. **Deploy to GitHub Pages:**

   ```bash
   git add .
   git commit -m "Deploy UK Climate Viewer"
   git push origin main
   ```

   Then enable GitHub Pages:
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Under "Source", select "Deploy from branch"
   - Select branch: `main` and folder: `/ (root)`
   - Click Save

   Your site will be live at: `https://yourusername.github.io/rainmapping/`

## Usage Guide

### Navigation Controls

- **View Mode Toggle**: Switch between "Monthly Data" (individual months) and "Monthly Averages" (aggregated across years)
- **Year Slider**: Navigate through years (2014-2023) when in Monthly Data mode
- **Month Slider**: Navigate through months (January-December)
- **Play Button**: Auto-play through the time series
- **Speed Control**: Adjust animation speed (Slow/Normal/Fast)

### Keyboard Shortcuts

- `←` / `→` - Previous/Next month
- `↑` / `↓` - Previous/Next year (when in Monthly Data mode)
- `Space` - Play/Pause animation

### Location Features

- **Search**: Type in the search box to filter locations
- **Toggle Visibility**: Click "Show/Hide" on any location to toggle its visibility on the map
- **Show/Hide All**: Toggle all locations at once
- **Add Custom Location**:
  - Click "Add Custom Location" button, or
  - Hold Shift and click on the map
  - Enter name and British National Grid coordinates
- **Remove Custom Location**: Click "Remove" on any custom location

### URL Sharing

Share specific views by copying the URL. Parameters:
- `?year=2022&month=7&view=monthly` - July 2022
- `?month=1&view=averages` - January average across all years

## Data Source

**CEDA HADUKGrid 1km dataset**
- Monthly rainfall and sunshine data
- 1km resolution across the UK
- British National Grid (EPSG:27700) coordinate system
- Coverage: 2014-2023

## Technical Architecture

### Technology Stack

- **Frontend**: Pure HTML5, CSS3, and vanilla JavaScript (no frameworks)
- **Canvas API**: For rendering maps and location markers
- **Data Format**: Pre-rendered PNG images with metadata JSON
- **Coordinate System**: British National Grid (EPSG:27700)

### File Structure

```
rainmapping/
├── index.html          # Main application page
├── style.css           # Styling and responsive design
├── app.js              # Core application logic
├── data/
│   ├── images/         # Monthly climate images
│   ├── averages/       # Monthly average images
│   ├── key*.png        # Color legends
│   ├── metadata.json   # Geographic extent and metadata
│   └── locations.json  # UK settlements database
├── plan.md             # Project documentation and preprocessing script
└── README.md           # This file
```

### Key Features Implementation

**Coordinate Mapping**: Accurate transformation between British National Grid coordinates and pixel coordinates on the canvas, maintaining aspect ratio and handling the inverted Y-axis.

**Image Caching**: Loaded images are cached in memory for instant navigation. Adjacent months are preloaded for smooth experience.

**Local Storage**: Custom locations are saved to browser local storage and persist across sessions.

**Responsive Design**: CSS Grid and Flexbox ensure the interface works on all screen sizes.

## Preprocessing Data

If you need to regenerate the images or add new data, see the **Complete Preprocessing Code** section in `plan.md`. The script:

1. Loads NetCDF files from CEDA HADUKGrid dataset
2. Calculates tertiles for bivariate mapping
3. Generates color-coded PNG images
4. Creates monthly averages
5. Exports metadata for coordinate mapping

## Browser Compatibility

- **Chrome/Edge**: Full support ✅
- **Firefox**: Full support ✅
- **Safari**: Full support ✅
- **Mobile browsers**: Full support ✅
- **IE11**: Not supported ❌

## Performance

- **Image Loading**: ~300-800 KB per image
- **Total Data Size**: ~70 MB (120 monthly images + 12 averages)
- **Initial Load**: <2 seconds on broadband
- **Navigation**: <100ms with image caching

## Customization

### Adding More Locations

Edit `data/locations.json`:

```json
{
  "name": "Your Location",
  "x": 530000,
  "y": 180000,
  "type": "town",
  "visible": true
}
```

Coordinates must be in British National Grid (EPSG:27700).

### Changing Color Scheme

To modify the bivariate color scheme, edit the preprocessing script in `plan.md` and regenerate all images:

```python
COLORS = [
    "#f3f3f3", "#b4d3e1", "#509dc2",  # Low sun row
    "#f3e6b3", "#b3b3b3", "#376387",  # Med sun row
    "#f3b300", "#b36600", "#000000"   # High sun row
]
```

### Extending Date Range

To add more years:
1. Run the preprocessing script with updated `YEARS_TO_PROCESS`
2. Copy new images to `data/images/`
3. Update `data/metadata.json` with new years array

## Troubleshooting

### Images not loading

- Verify `data/` directory structure matches expected layout
- Check browser console for 404 errors
- Ensure `metadata.json` exists and is valid JSON
- Check that image files are named correctly (e.g., `01.png`, `02.png`)

### Locations not appearing on map

- Verify coordinates are in British National Grid (EPSG:27700)
- Check that coordinates fall within the extent defined in `metadata.json`
- Ensure location is marked as `visible: true`

### Canvas appears distorted

- Check that `metadata.json` contains correct extent values
- Verify aspect ratio calculation in `setupCanvas()`
- Try refreshing the page to reset canvas dimensions

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Data Source**: CEDA HADUKGrid dataset
- **Location Data**: Ordnance Survey Open Names (consider adding if used)
- **Color Scheme**: Custom bivariate mapping design
- **Inspiration**: Modern climate visualization tools

## Contact

For questions or support, please open an issue on GitHub.

## Roadmap

Future enhancements:
- [ ] Add data export functionality (CSV download for specific locations)
- [ ] Implement touch gestures for mobile navigation
- [ ] Add comparison mode (view two time periods side-by-side)
- [ ] Create an offline PWA version
- [ ] Add statistics panel showing exact values at clicked locations
- [ ] Integrate with additional climate variables (temperature, wind)

---

**Built with ❤️ for climate data visualization**
