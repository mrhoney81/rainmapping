// ============================================================================
// UK CLIMATE LEAFLET VIEWER
// Dynamic overlay rendering with OSM tiles
// ============================================================================

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

// Temperature color scheme (blue to red) - matching Woolhampton absolute scale
const TEMP_COLORS = [
    "#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0",
    "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"
];

// Bivariate color scheme for rain/sun (from original app)
const BIVARIATE_COLORS = {
    // Format: [rain_level][sun_level] where 0=low, 1=medium, 2=high
    // Rain increases vertically (more blue), Sun increases horizontally (more yellow)
    0: { 0: "#f3f3f3", 1: "#f3e6b3", 2: "#f3b300" }, // Low rain
    1: { 0: "#b4d3e1", 1: "#b3b3b3", 2: "#b36600" }, // Medium rain
    2: { 0: "#509dc2", 1: "#376387", 2: "#000000" }  // High rain
};

// Application state
let map;
let dataOverlay;
let metadata;
let currentYear = 2023;
let currentMonth = 1;
let dataType = 'rainsun'; // 'rainsun' or 'temp'
let opacity = 0.7;
let currentData = { rain: null, sun: null, temp: null };
let dataCache = new Map();

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
    console.log('Initializing Leaflet Climate Viewer...');

    try {
        // Load metadata
        const response = await fetch('leaflet_data/metadata.json');
        metadata = await response.json();
        console.log('Metadata loaded:', metadata);

        // Initialize map
        initMap();

        // Set up event listeners
        setupEventListeners();

        // Load initial data
        await loadAndDisplayData();

        console.log('Initialization complete!');

    } catch (error) {
        console.error('Initialization error:', error);
        alert('Failed to initialize. Check console for details.');
    }
}

// ============================================================================
// MAP INITIALIZATION
// ============================================================================

function initMap() {
    // Initialize Leaflet map with OSM tiles
    // Note: OSM uses Web Mercator (EPSG:3857), we'll handle BNG->LatLng conversion
    map = L.map('map', {
        center: [54.5, -3.0], // Center of UK
        zoom: 6,
        minZoom: 5,
        maxZoom: 11, // Limit zoom for 1km tiles
        zoomControl: true
    });

    // Add OSM tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // Create custom overlay for climate data
    dataOverlay = L.layerGroup().addTo(map);

    console.log('Map initialized');
}

// ============================================================================
// DATA LOADING
// ============================================================================

async function loadData(year, month, type) {
    const cacheKey = `${type}_${year}_${month}`;

    // Check cache
    if (dataCache.has(cacheKey)) {
        return dataCache.get(cacheKey);
    }

    const filename = `leaflet_data/${type}/${year}_${String(month).padStart(2, '0')}.json.gz`;

    try {
        const response = await fetch(filename);
        if (!response.ok) throw new Error(`Failed to load ${filename}`);

        const arrayBuffer = await response.arrayBuffer();
        const decompressed = pako.ungzip(new Uint8Array(arrayBuffer), { to: 'string' });
        const data = JSON.parse(decompressed);

        // Cache the data
        dataCache.set(cacheKey, data);

        // Limit cache size
        if (dataCache.size > 20) {
            const firstKey = dataCache.keys().next().value;
            dataCache.delete(firstKey);
        }

        return data;

    } catch (error) {
        console.error(`Error loading ${filename}:`, error);
        return null;
    }
}

async function loadAndDisplayData() {
    showLoading(true);

    try {
        if (dataType === 'rainsun') {
            // Load both rain and sun data
            const [rain, sun] = await Promise.all([
                loadData(currentYear, currentMonth, 'rain'),
                loadData(currentYear, currentMonth, 'sun')
            ]);
            currentData.rain = rain;
            currentData.sun = sun;
        } else {
            // Load temperature data
            const temp = await loadData(currentYear, currentMonth, 'temp');
            currentData.temp = temp;
        }

        renderOverlay();
        updateInfoBox();

    } catch (error) {
        console.error('Error loading data:', error);
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// RENDERING
// ============================================================================

function renderOverlay() {
    // Clear existing overlay
    dataOverlay.clearLayers();

    if (dataType === 'rainsun') {
        renderRainSunOverlay();
    } else {
        renderTempOverlay();
    }
}

function renderTempOverlay() {
    if (!currentData.temp) return;

    const data = currentData.temp;
    const tempScale = metadata.temperature.scale_range || metadata.temperature.woolhampton_range;

    // Find actual data range for this month
    let minTemp = Infinity;
    let maxTemp = -Infinity;

    Object.values(data).forEach(yData => {
        Object.values(yData).forEach(temp => {
            if (temp < minTemp) minTemp = temp;
            if (temp > maxTemp) maxTemp = temp;
        });
    });

    console.log(`Temperature range for ${MONTH_NAMES[currentMonth-1]} ${currentYear}: ${minTemp}°C to ${maxTemp}°C`);
    console.log(`Absolute scale: ${tempScale.min}°C to ${tempScale.max}°C`);

    // Render cells using absolute scale
    Object.entries(data).forEach(([x, yData]) => {
        Object.entries(yData).forEach(([y, temp]) => {
            const color = getTempColor(temp, tempScale.min, tempScale.max);
            renderCell(parseFloat(x), parseFloat(y), color);
        });
    });
}

function renderRainSunOverlay() {
    if (!currentData.rain || !currentData.sun) return;

    const rainData = currentData.rain;
    const sunData = currentData.sun;

    // Calculate percentiles for classification
    const rainValues = [];
    const sunValues = [];

    Object.values(rainData).forEach(yData => {
        Object.values(yData).forEach(val => rainValues.push(val));
    });

    Object.values(sunData).forEach(yData => {
        Object.values(yData).forEach(val => sunValues.push(val));
    });

    rainValues.sort((a, b) => a - b);
    sunValues.sort((a, b) => a - b);

    const rain33 = rainValues[Math.floor(rainValues.length * 0.33)];
    const rain66 = rainValues[Math.floor(rainValues.length * 0.66)];
    const sun33 = sunValues[Math.floor(sunValues.length * 0.33)];
    const sun66 = sunValues[Math.floor(sunValues.length * 0.66)];

    console.log(`Rain thresholds: ${rain33}, ${rain66}`);
    console.log(`Sun thresholds: ${sun33}, ${sun66}`);

    // Render cells
    Object.entries(rainData).forEach(([x, yData]) => {
        Object.entries(yData).forEach(([y, rainVal]) => {
            const sunVal = sunData[x]?.[y];
            if (sunVal !== undefined) {
                const color = getBivariateColor(rainVal, sunVal, rain33, rain66, sun33, sun66);
                renderCell(parseFloat(x), parseFloat(y), color);
            }
        });
    });
}

function renderCell(bngX, bngY, color) {
    // Convert BNG coordinates to lat/lng
    // BNG coordinates are in meters, representing the center of 1km cells

    // Cell boundaries (1km square)
    const halfCell = 500; // 500m from center to edge

    const sw = bngToLatLng(bngX - halfCell, bngY - halfCell);
    const ne = bngToLatLng(bngX + halfCell, bngY + halfCell);

    if (!sw || !ne) return;

    // Create rectangle
    const rect = L.rectangle([sw, ne], {
        color: color,
        fillColor: color,
        fillOpacity: opacity,
        weight: 0,
        interactive: false
    });

    dataOverlay.addLayer(rect);
}

// ============================================================================
// COORDINATE CONVERSION
// ============================================================================

function bngToLatLng(easting, northing) {
    // Convert British National Grid (OSGB36, EPSG:27700) to WGS84 (EPSG:4326)
    // Using proj4 for accurate conversion

    try {
        // Define EPSG:27700 (British National Grid)
        if (!proj4.defs['EPSG:27700']) {
            proj4.defs('EPSG:27700',
                '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 ' +
                '+ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 ' +
                '+units=m +no_defs'
            );
        }

        // Convert BNG to WGS84
        const [lng, lat] = proj4('EPSG:27700', 'EPSG:4326', [easting, northing]);

        return [lat, lng];

    } catch (error) {
        console.error('Coordinate conversion error:', error);
        return null;
    }
}

// ============================================================================
// COLOR MAPPING
// ============================================================================

function getTempColor(temp, minTemp, maxTemp) {
    // Use Woolhampton absolute scale
    const normalized = (temp - minTemp) / (maxTemp - minTemp);
    const clamped = Math.max(0, Math.min(1, normalized));

    const colorIndex = Math.floor(clamped * (TEMP_COLORS.length - 1));
    return TEMP_COLORS[colorIndex];
}

function getBivariateColor(rain, sun, rain33, rain66, sun33, sun66) {
    // Classify rain into 3 levels
    let rainLevel;
    if (rain < rain33) rainLevel = 0;
    else if (rain < rain66) rainLevel = 1;
    else rainLevel = 2;

    // Classify sun into 3 levels
    let sunLevel;
    if (sun < sun33) sunLevel = 0;
    else if (sun < sun66) sunLevel = 1;
    else sunLevel = 2;

    return BIVARIATE_COLORS[rainLevel][sunLevel];
}

// ============================================================================
// UI UPDATES
// ============================================================================

function updateUI() {
    document.getElementById('yearValue').textContent = currentYear;
    document.getElementById('monthValue').textContent = MONTH_NAMES[currentMonth - 1];
    document.getElementById('yearSlider').value = currentYear;
    document.getElementById('monthSlider').value = currentMonth;
    document.getElementById('opacityValue').textContent = Math.round(opacity * 100) + '%';
    document.getElementById('opacitySlider').value = Math.round(opacity * 100);

    document.getElementById('rainSunBtn').classList.toggle('active', dataType === 'rainsun');
    document.getElementById('tempBtn').classList.toggle('active', dataType === 'temp');

    updateLegend();
}

function updateLegend() {
    const legendSection = document.getElementById('legendSection');

    if (dataType === 'temp') {
        const tempScale = metadata.temperature.scale_range || metadata.temperature.woolhampton_range;
        legendSection.innerHTML = `
            <h3>Temperature Legend</h3>
            <div class="legend">
                <h4>Temperature (°C)</h4>
                <div class="legend-gradient" style="background: linear-gradient(to right, ${TEMP_COLORS.join(', ')});"></div>
                <div class="legend-labels">
                    <span>${tempScale.min}°C</span>
                    <span>Colder</span>
                    <span>Warmer</span>
                    <span>${tempScale.max}°C</span>
                </div>
                <div style="margin-top: 8px; font-size: 11px; color: #999;">
                    Absolute scale: ${tempScale.min}°C to ${tempScale.max}°C
                </div>
            </div>
        `;
    } else {
        legendSection.innerHTML = `
            <h3>Rain/Sun Legend</h3>
            <div class="legend">
                <h4>Bivariate Color Scheme</h4>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-bottom: 8px;">
                    ${[2,1,0].map(r =>
                        [0,1,2].map(s =>
                            `<div style="background: ${BIVARIATE_COLORS[r][s]}; height: 30px; border-radius: 2px;"></div>`
                        ).join('')
                    ).join('')}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #999; margin-bottom: 4px;">
                    <span>← Less Sun</span>
                    <span>More Sun →</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #999;">
                    <span>↑ More Rain</span>
                    <span>↑</span>
                </div>
            </div>
        `;
    }
}

function updateInfoBox() {
    const info = document.getElementById('dataInfo');
    const period = `${MONTH_NAMES[currentMonth - 1]} ${currentYear}`;

    if (dataType === 'rainsun') {
        info.innerHTML = `<div style="margin-top: 8px;"><strong>Showing:</strong> Rain & Sunshine<br>${period}</div>`;
    } else {
        info.innerHTML = `<div style="margin-top: 8px;"><strong>Showing:</strong> Temperature<br>${period}</div>`;
    }
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function setupEventListeners() {
    // Data type buttons
    document.getElementById('rainSunBtn').addEventListener('click', () => {
        dataType = 'rainsun';
        updateUI();
        loadAndDisplayData();
    });

    document.getElementById('tempBtn').addEventListener('click', () => {
        dataType = 'temp';
        updateUI();
        loadAndDisplayData();
    });

    // Year slider
    document.getElementById('yearSlider').addEventListener('input', (e) => {
        currentYear = parseInt(e.target.value);
        updateUI();
        loadAndDisplayData();
    });

    // Month slider
    document.getElementById('monthSlider').addEventListener('input', (e) => {
        currentMonth = parseInt(e.target.value);
        updateUI();
        loadAndDisplayData();
    });

    // Opacity slider
    document.getElementById('opacitySlider').addEventListener('input', (e) => {
        opacity = parseInt(e.target.value) / 100;
        updateUI();
        renderOverlay(); // Re-render with new opacity
    });
}

// ============================================================================
// START APPLICATION
// ============================================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
