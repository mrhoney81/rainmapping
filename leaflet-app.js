// ============================================================================
// UK CLIMATE LEAFLET VIEWER - Canvas-based overlay for performance
// ============================================================================

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

// Temperature color scheme (blue to red)
const TEMP_COLORS = [
    "#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0",
    "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"
];

// Bivariate color scheme for rain/sun
const BIVARIATE_COLORS = {
    0: { 0: "#f3f3f3", 1: "#f3e6b3", 2: "#f3b300" },
    1: { 0: "#b4d3e1", 1: "#b3b3b3", 2: "#b36600" },
    2: { 0: "#509dc2", 1: "#376387", 2: "#000000" }
};

// Application state
let map;
let canvasOverlay;
let metadata;
let currentYear = 2023;
let currentMonth = 1;
let dataType = 'rainsun';
let opacity = 0.7;
let currentData = { rain: null, sun: null, temp: null };
let dataCache = new Map();

// ============================================================================
// CUSTOM CANVAS LAYER FOR LEAFLET
// ============================================================================

L.CanvasOverlay = L.Layer.extend({
    initialize: function(options) {
        this._canvas = null;
        this._context = null;
        this._data = null;
        this._metadata = null;
        this._dataType = 'rainsun';
        this._opacity = 0.7;
        L.setOptions(this, options);
    },

    onAdd: function(map) {
        this._map = map;

        if (!this._canvas) {
            this._initCanvas();
        }

        map.getPanes().overlayPane.appendChild(this._canvas);

        map.on('moveend', this._reset, this);
        map.on('zoom', this._reset, this);

        this._reset();
    },

    onRemove: function(map) {
        map.getPanes().overlayPane.removeChild(this._canvas);
        map.off('moveend', this._reset, this);
        map.off('zoom', this._reset, this);
    },

    _initCanvas: function() {
        this._canvas = L.DomUtil.create('canvas', 'leaflet-canvas-overlay');
        this._context = this._canvas.getContext('2d');

        const size = this._map.getSize();
        this._canvas.width = size.x;
        this._canvas.height = size.y;

        this._canvas.style.position = 'absolute';
        this._canvas.style.pointerEvents = 'none';

        const animated = this._map.options.zoomAnimation && L.Browser.any3d;
        L.DomUtil.addClass(this._canvas, 'leaflet-zoom-' + (animated ? 'animated' : 'hide'));
    },

    _reset: function() {
        const topLeft = this._map.containerPointToLayerPoint([0, 0]);
        L.DomUtil.setPosition(this._canvas, topLeft);

        const size = this._map.getSize();
        this._canvas.width = size.x;
        this._canvas.height = size.y;

        this._render();
    },

    setData: function(data, metadata, dataType, opacity) {
        this._data = data;
        this._metadata = metadata;
        this._dataType = dataType;
        this._opacity = opacity;
        this._render();
    },

    _render: function() {
        if (!this._data || !this._metadata) return;

        const ctx = this._context;
        const bounds = this._map.getBounds();

        // Clear canvas
        ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
        ctx.globalAlpha = this._opacity;

        // Get BNG bounds
        const sw = this._latLngToBNG(bounds.getSouthWest());
        const ne = this._latLngToBNG(bounds.getNorthEast());

        if (!sw || !ne) return;

        const resolution = this._metadata.extent.resolution_meters;

        // Iterate through data and render visible cells
        if (this._dataType === 'temp') {
            this._renderTemp(ctx, sw, ne, resolution);
        } else {
            this._renderRainSun(ctx, sw, ne, resolution);
        }
    },

    _renderTemp: function(ctx, sw, ne, resolution) {
        const tempData = this._data.temp;
        if (!tempData) return;

        const tempScale = this._metadata.temperature.scale_range;

        // Iterate through visible cells
        Object.entries(tempData).forEach(([x, yData]) => {
            const xCoord = parseFloat(x);
            if (xCoord < sw.x - resolution || xCoord > ne.x + resolution) return;

            Object.entries(yData).forEach(([y, temp]) => {
                const yCoord = parseFloat(y);
                if (yCoord < sw.y - resolution || yCoord > ne.y + resolution) return;

                const color = this._getTempColor(temp, tempScale.min, tempScale.max);
                this._drawCell(ctx, xCoord, yCoord, resolution, color);
            });
        });
    },

    _renderRainSun: function(ctx, sw, ne, resolution) {
        const rainData = this._data.rain;
        const sunData = this._data.sun;
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

        // Render visible cells
        Object.entries(rainData).forEach(([x, yData]) => {
            const xCoord = parseFloat(x);
            if (xCoord < sw.x - resolution || xCoord > ne.x + resolution) return;

            Object.entries(yData).forEach(([y, rainVal]) => {
                const yCoord = parseFloat(y);
                if (yCoord < sw.y - resolution || yCoord > ne.y + resolution) return;

                const sunVal = sunData[x]?.[y];
                if (sunVal !== undefined) {
                    const color = this._getBivariateColor(rainVal, sunVal, rain33, rain66, sun33, sun66);
                    this._drawCell(ctx, xCoord, yCoord, resolution, color);
                }
            });
        });
    },

    _drawCell: function(ctx, bngX, bngY, resolution, color) {
        // Convert BNG cell to screen coordinates
        const halfRes = resolution / 2;

        const sw = this._bngToLatLng(bngX - halfRes, bngY - halfRes);
        const ne = this._bngToLatLng(bngX + halfRes, bngY + halfRes);

        if (!sw || !ne) return;

        const swPoint = this._map.latLngToContainerPoint(sw);
        const nePoint = this._map.latLngToContainerPoint(ne);

        const width = nePoint.x - swPoint.x;
        const height = swPoint.y - nePoint.y;

        ctx.fillStyle = color;
        ctx.fillRect(swPoint.x, nePoint.y, width, height);
    },

    _bngToLatLng: function(easting, northing) {
        try {
            if (!window.proj4) return null;

            if (!proj4.defs['EPSG:27700']) {
                proj4.defs('EPSG:27700',
                    '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 ' +
                    '+ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 ' +
                    '+units=m +no_defs'
                );
            }

            const [lng, lat] = proj4('EPSG:27700', 'EPSG:4326', [easting, northing]);
            return L.latLng(lat, lng);
        } catch (error) {
            return null;
        }
    },

    _latLngToBNG: function(latLng) {
        try {
            if (!window.proj4) return null;

            if (!proj4.defs['EPSG:27700']) {
                proj4.defs('EPSG:27700',
                    '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 ' +
                    '+ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 ' +
                    '+units=m +no_defs'
                );
            }

            const [x, y] = proj4('EPSG:4326', 'EPSG:27700', [latLng.lng, latLng.lat]);
            return { x: x, y: y };
        } catch (error) {
            return null;
        }
    },

    _getTempColor: function(temp, minTemp, maxTemp) {
        const normalized = (temp - minTemp) / (maxTemp - minTemp);
        const clamped = Math.max(0, Math.min(1, normalized));
        const colorIndex = Math.floor(clamped * (TEMP_COLORS.length - 1));
        return TEMP_COLORS[colorIndex];
    },

    _getBivariateColor: function(rain, sun, rain33, rain66, sun33, sun66) {
        let rainLevel = rain < rain33 ? 0 : rain < rain66 ? 1 : 2;
        let sunLevel = sun < sun33 ? 0 : sun < sun66 ? 1 : 2;
        return BIVARIATE_COLORS[rainLevel][sunLevel];
    }
});

L.canvasOverlay = function(options) {
    return new L.CanvasOverlay(options);
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

    canvasOverlay = L.canvasOverlay().addTo(map);

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
    if (canvasOverlay) {
        canvasOverlay.setData(currentData, metadata, dataType, opacity);
    }
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
        renderOverlay();
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
