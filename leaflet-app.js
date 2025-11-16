// ============================================================================
// UK CLIMATE LEAFLET VIEWER - Proper coordinate transformation per-cell
// Using CanvasLayer with correct projection handling
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
let canvasLayer;
let metadata;
let currentYear = 2023;
let currentMonth = 1;
let dataType = 'rainsun';
let opacity = 0.7;
let currentData = { rain: null, sun: null, temp: null };
let dataCache = new Map();

// Pre-computed grid data for fast rendering
let gridData = null;

// ============================================================================
// CUSTOM CANVAS LAYER - renders to map projection correctly
// ============================================================================

L.GridCanvasLayer = L.Layer.extend({
    initialize: function(options) {
        L.setOptions(this, options);
    },

    onAdd: function(map) {
        this._map = map;

        if (!this._canvas) {
            this._canvas = L.DomUtil.create('canvas', 'leaflet-layer');
            this._ctx = this._canvas.getContext('2d');
        }

        this.getPane().appendChild(this._canvas);

        this._reset();
        map.on('moveend zoom', this._reset, this);
    },

    onRemove: function(map) {
        this.getPane().removeChild(this._canvas);
        map.off('moveend zoom', this._reset, this);
    },

    _reset: function() {
        const size = this._map.getSize();
        this._canvas.width = size.x;
        this._canvas.height = size.y;

        const topLeft = this._map.containerPointToLayerPoint([0, 0]);
        L.DomUtil.setPosition(this._canvas, topLeft);

        this._render();
    },

    setData: function(gridData) {
        this._gridData = gridData;
        this._render();
    },

    setOpacity: function(opacity) {
        this._opacity = opacity;
        this._render();
    },

    _render: function() {
        if (!this._gridData || !this._gridData.length) return;

        const ctx = this._ctx;
        ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
        ctx.globalAlpha = this._opacity || 0.7;

        // Get current map bounds
        const bounds = this._map.getBounds();
        const zoom = this._map.getZoom();

        // Render each grid cell
        for (const cell of this._gridData) {
            // Check if cell is in view
            if (cell.lat < bounds.getSouth() || cell.lat > bounds.getNorth() ||
                cell.lng < bounds.getWest() || cell.lng > bounds.getEast()) {
                continue;
            }

            // Get corners of 1km cell in screen coordinates
            const nw = this._map.latLngToContainerPoint([cell.ne_lat, cell.nw_lng]);
            const se = this._map.latLngToContainerPoint([cell.se_lat, cell.se_lng]);
            const ne = this._map.latLngToContainerPoint([cell.ne_lat, cell.ne_lng]);
            const sw = this._map.latLngToContainerPoint([cell.sw_lat, cell.sw_lng]);

            // Draw as a quad (cells may be slightly skewed due to projection)
            ctx.fillStyle = cell.color;
            ctx.beginPath();
            ctx.moveTo(nw.x, nw.y);
            ctx.lineTo(ne.x, ne.y);
            ctx.lineTo(se.x, se.y);
            ctx.lineTo(sw.x, sw.y);
            ctx.closePath();
            ctx.fill();
        }
    }
});

L.gridCanvasLayer = function(options) {
    return new L.GridCanvasLayer(options);
};

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
    console.log('Initializing Leaflet Climate Viewer...');

    try {
        const response = await fetch('leaflet_data/metadata.json');
        metadata = await response.json();
        console.log('Metadata loaded:', metadata);

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
    if (!window.proj4) return null;

    if (!proj4.defs['EPSG:27700']) {
        proj4.defs('EPSG:27700',
            '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 ' +
            '+ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 ' +
            '+units=m +no_defs'
        );
    }

    const [lng, lat] = proj4('EPSG:27700', 'EPSG:4326', [easting, northing]);
    return { lat, lng };
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

    canvasLayer = L.gridCanvasLayer().addTo(map);

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

        prepareGridData();
        updateInfoBox();
    } catch (error) {
        console.error('Error loading data:', error);
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// GRID DATA PREPARATION
// ============================================================================

function prepareGridData() {
    console.time('prepareGridData');

    gridData = [];
    const extent = metadata.extent;
    const resolution = extent.resolution_meters;
    const halfRes = resolution / 2;

    if (dataType === 'temp') {
        const tempData = currentData.temp;
        if (!tempData) return;

        const tempScale = metadata.temperature.scale_range;

        Object.entries(tempData).forEach(([x, yData]) => {
            Object.entries(yData).forEach(([y, temp]) => {
                const bngX = parseFloat(x);
                const bngY = parseFloat(y);

                // Get cell corners in BNG
                const sw = bngToLatLng(bngX - halfRes, bngY - halfRes);
                const se = bngToLatLng(bngX + halfRes, bngY - halfRes);
                const ne = bngToLatLng(bngX + halfRes, bngY + halfRes);
                const nw = bngToLatLng(bngX - halfRes, bngY + halfRes);

                if (!sw || !se || !ne || !nw) return;

                const color = getTempColor(temp, tempScale.min, tempScale.max);

                gridData.push({
                    lat: sw.lat + (ne.lat - sw.lat) / 2,  // center for bounds checking
                    lng: sw.lng + (ne.lng - sw.lng) / 2,
                    sw_lat: sw.lat, sw_lng: sw.lng,
                    se_lat: se.lat, se_lng: se.lng,
                    ne_lat: ne.lat, ne_lng: ne.lng,
                    nw_lat: nw.lat, nw_lng: nw.lng,
                    color: color
                });
            });
        });
    } else {
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

        Object.entries(rainData).forEach(([x, yData]) => {
            Object.entries(yData).forEach(([y, rainVal]) => {
                const sunVal = sunData[x]?.[y];
                if (sunVal === undefined) return;

                const bngX = parseFloat(x);
                const bngY = parseFloat(y);

                const sw = bngToLatLng(bngX - halfRes, bngY - halfRes);
                const se = bngToLatLng(bngX + halfRes, bngY - halfRes);
                const ne = bngToLatLng(bngX + halfRes, bngY + halfRes);
                const nw = bngToLatLng(bngX - halfRes, bngY + halfRes);

                if (!sw || !se || !ne || !nw) return;

                const color = getBivariateColor(rainVal, sunVal, rain33, rain66, sun33, sun66);

                gridData.push({
                    lat: sw.lat + (ne.lat - sw.lat) / 2,
                    lng: sw.lng + (ne.lng - sw.lng) / 2,
                    sw_lat: sw.lat, sw_lng: sw.lng,
                    se_lat: se.lat, se_lng: se.lng,
                    ne_lat: ne.lat, ne_lng: ne.lng,
                    nw_lat: nw.lat, nw_lng: nw.lng,
                    color: color
                });
            });
        });
    }

    console.timeEnd('prepareGridData');
    console.log(`Prepared ${gridData.length} grid cells`);

    if (canvasLayer) {
        canvasLayer.setData(gridData);
        canvasLayer.setOpacity(opacity);
    }
}

// ============================================================================
// COLOR FUNCTIONS
// ============================================================================

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
        if (canvasLayer) {
            canvasLayer.setOpacity(opacity);
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
