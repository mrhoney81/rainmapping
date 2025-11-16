// ============================================================================
// UK CLIMATE LEAFLET VIEWER - Proper bitmap rendering approach
// ============================================================================

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

const TEMP_COLORS = [
    "#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0",
    "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"
];

const BIVARIATE_COLORS = {
    0: { 0: "#f3f3f3", 1: "#f3e6b3", 2: "#f3b300" },
    1: { 0: "#b4d3e1", 1: "#b3b3b3", 2: "#b36600" },
    2: { 0: "#509dc2", 1: "#376387", 2: "#000000" }
};

let map;
let imageOverlay = null;
let metadata;
let currentYear = 2023;
let currentMonth = 1;
let dataType = 'rainsun';
let opacity = 0.7;
let currentData = { rain: null, sun: null, temp: null };
let dataCache = new Map();

// BNG bounds (will be converted to lat/lng for ImageOverlay)
let imageBounds = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
    console.log('Initializing Leaflet Climate Viewer...');

    try {
        const response = await fetch('leaflet_data/metadata.json');
        metadata = await response.json();
        console.log('Metadata loaded:', metadata);

        // Calculate image bounds
        const sw = bngToLatLng(metadata.extent.x_min, metadata.extent.y_min);
        const ne = bngToLatLng(metadata.extent.x_max, metadata.extent.y_max);
        imageBounds = [[sw[0], sw[1]], [ne[0], ne[1]]];

        console.log('Image bounds:', imageBounds);

        initMap();
        setupEventListeners();
        await loadAndDisplayData();

        console.log('Initialization complete!');
    } catch (error) {
        console.error('Initialization error:', error);
        alert('Failed to initialize. Check console for details.');
    }
}

// ============================================================================
// COORDINATE CONVERSION
// ============================================================================

function bngToLatLng(easting, northing) {
    // BNG to WGS84 conversion using proj4
    if (!window.proj4) return [0, 0];

    if (!proj4.defs['EPSG:27700']) {
        proj4.defs('EPSG:27700',
            '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 ' +
            '+ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 ' +
            '+units=m +no_defs'
        );
    }

    const [lng, lat] = proj4('EPSG:27700', 'EPSG:4326', [easting, northing]);
    return [lat, lng];
}

// ============================================================================
// MAP INITIALIZATION
// ============================================================================

function initMap() {
    map = L.map('map', {
        center: [54.5, -3.0],
        zoom: 6,
        minZoom: 5,
        maxZoom: 11
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    console.log('Map initialized');
}

// ============================================================================
// DATA LOADING
// ============================================================================

async function loadData(year, month, type) {
    const cacheKey = `${type}_${year}_${month}`;

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

        dataCache.set(cacheKey, data);

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
            const [rain, sun] = await Promise.all([
                loadData(currentYear, currentMonth, 'rain'),
                loadData(currentYear, currentMonth, 'sun')
            ]);
            currentData.rain = rain;
            currentData.sun = sun;
        } else {
            const temp = await loadData(currentYear, currentMonth, 'temp');
            currentData.temp = temp;
        }

        renderToImage();
        updateInfoBox();
    } catch (error) {
        console.error('Error loading data:', error);
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// RENDERING TO BITMAP
// ============================================================================

function renderToImage() {
    // Create canvas for bitmap rendering
    const canvas = document.createElement('canvas');
    const width = 900;  // Grid width from metadata
    const height = 1450; // Grid height from metadata

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;

    if (dataType === 'temp') {
        renderTempToBitmap(data, width, height);
    } else {
        renderRainSunToBitmap(data, width, height);
    }

    ctx.putImageData(imageData, 0, 0);

    // Convert canvas to data URL
    const imageUrl = canvas.toDataURL('image/png');

    // Update or create ImageOverlay
    if (imageOverlay) {
        map.removeLayer(imageOverlay);
    }

    imageOverlay = L.imageOverlay(imageUrl, imageBounds, {
        opacity: opacity,
        interactive: false
    });

    imageOverlay.addTo(map);
}

function renderTempToBitmap(data, width, height) {
    const tempData = currentData.temp;
    if (!tempData) return;

    const tempScale = metadata.temperature.scale_range;
    const extent = metadata.extent;
    const resolution = extent.resolution_meters;

    // Create lookup for faster access
    for (let row = 0; row < height; row++) {
        for (let col = 0; col < width; col++) {
            // Calculate BNG coordinates for this cell (center)
            const x = extent.x_min + (col + 0.5) * resolution;
            const y = extent.y_max - (row + 0.5) * resolution;

            const xKey = Math.round(x).toString();
            const yKey = Math.round(y).toString();

            if (tempData[xKey] && tempData[xKey][yKey] !== undefined) {
                const temp = tempData[xKey][yKey];
                const color = getTempColor(temp, tempScale.min, tempScale.max);
                const rgb = hexToRgb(color);

                const idx = (row * width + col) * 4;
                data[idx] = rgb[0];     // R
                data[idx + 1] = rgb[1]; // G
                data[idx + 2] = rgb[2]; // B
                data[idx + 3] = 255;    // A
            }
        }
    }
}

function renderRainSunToBitmap(data, width, height) {
    const rainData = currentData.rain;
    const sunData = currentData.sun;
    if (!rainData || !sunData) return;

    // Calculate percentiles
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

    const extent = metadata.extent;
    const resolution = extent.resolution_meters;

    for (let row = 0; row < height; row++) {
        for (let col = 0; col < width; col++) {
            const x = extent.x_min + (col + 0.5) * resolution;
            const y = extent.y_max - (row + 0.5) * resolution;

            const xKey = Math.round(x).toString();
            const yKey = Math.round(y).toString();

            if (rainData[xKey] && rainData[xKey][yKey] !== undefined &&
                sunData[xKey] && sunData[xKey][yKey] !== undefined) {

                const rainVal = rainData[xKey][yKey];
                const sunVal = sunData[xKey][yKey];

                const color = getBivariateColor(rainVal, sunVal, rain33, rain66, sun33, sun66);
                const rgb = hexToRgb(color);

                const idx = (row * width + col) * 4;
                data[idx] = rgb[0];
                data[idx + 1] = rgb[1];
                data[idx + 2] = rgb[2];
                data[idx + 3] = 255;
            }
        }
    }
}

// ============================================================================
// COLOR FUNCTIONS
// ============================================================================

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
    ] : [0, 0, 0];
}

function getTempColor(temp, minTemp, maxTemp) {
    const normalized = (temp - minTemp) / (maxTemp - minTemp);
    const clamped = Math.max(0, Math.min(1, normalized));
    const colorIndex = Math.floor(clamped * (TEMP_COLORS.length - 1));
    return TEMP_COLORS[colorIndex];
}

function getBivariateColor(rain, sun, rain33, rain66, sun33, sun66) {
    const rainLevel = rain < rain33 ? 0 : rain < rain66 ? 1 : 2;
    const sunLevel = sun < sun33 ? 0 : sun < sun66 ? 1 : 2;
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
        const tempScale = metadata.temperature.scale_range;
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
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #999;">
                    <span>← Less Sun</span>
                    <span>More Sun →</span>
                </div>
            </div>
        `;
    }
}

function updateInfoBox() {
    const info = document.getElementById('dataInfo');
    const period = `${MONTH_NAMES[currentMonth - 1]} ${currentYear}`;
    info.innerHTML = `<div style="margin-top: 8px;"><strong>Showing:</strong> ${dataType === 'temp' ? 'Temperature' : 'Rain & Sunshine'}<br>${period}</div>`;
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function setupEventListeners() {
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

    document.getElementById('yearSlider').addEventListener('input', (e) => {
        currentYear = parseInt(e.target.value);
        updateUI();
        loadAndDisplayData();
    });

    document.getElementById('monthSlider').addEventListener('input', (e) => {
        currentMonth = parseInt(e.target.value);
        updateUI();
        loadAndDisplayData();
    });

    document.getElementById('opacitySlider').addEventListener('input', (e) => {
        opacity = parseInt(e.target.value) / 100;
        updateUI();
        if (imageOverlay) {
            imageOverlay.setOpacity(opacity);
        }
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
