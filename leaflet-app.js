// ============================================================================
// UK CLIMATE LEAFLET VIEWER - Simple PNG overlay (fast & correct)
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

// Image bounds from generate_pngs.py
const IMAGE_BOUNDS = [[49.5, -8.5], [61.0, 2.0]];

let map;
let currentOverlay = null;
let currentYear = 2023;
let currentMonth = 1;
let dataType = 'rainsun';
let opacity = 0.7;

// ============================================================================
// INITIALIZATION
// ============================================================================

function init() {
    console.log('Initializing Leaflet Climate Viewer...');

    initMap();
    setupEventListeners();
    updateUI();
    updateDisplay();

    console.log('Initialization complete!');
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
// DISPLAY UPDATE
// ============================================================================

function updateDisplay() {
    // Remove old overlay
    if (currentOverlay) {
        map.removeLayer(currentOverlay);
    }

    // Determine image path
    const folder = dataType === 'temp' ? 'temp' : 'rain_sun';
    const imagePath = `leaflet_pngs/${folder}/${currentYear}_${String(currentMonth).padStart(2, '0')}.png`;

    console.log('Loading:', imagePath);

    // Create new overlay
    currentOverlay = L.imageOverlay(imagePath, IMAGE_BOUNDS, {
        opacity: opacity,
        interactive: false
    });

    currentOverlay.on('load', () => {
        console.log('Image loaded successfully');
        hideLoading();
    });

    currentOverlay.on('error', () => {
        console.error('Failed to load:', imagePath);
        hideLoading();
        alert('Failed to load image. Make sure you ran: python3 generate_pngs.py');
    });

    showLoading();
    currentOverlay.addTo(map);
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
    updateInfoBox();
}

function updateLegend() {
    const legendSection = document.getElementById('legendSection');

    if (dataType === 'temp') {
        legendSection.innerHTML = `
            <h3>Temperature Legend</h3>
            <div class="legend">
                <h4>Temperature (°C)</h4>
                <div class="legend-gradient" style="background: linear-gradient(to right, ${TEMP_COLORS.join(', ')});"></div>
                <div class="legend-labels">
                    <span>-10°C</span>
                    <span>Colder</span>
                    <span>Warmer</span>
                    <span>32°C</span>
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

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function setupEventListeners() {
    document.getElementById('rainSunBtn').addEventListener('click', () => {
        dataType = 'rainsun';
        updateUI();
        updateDisplay();
    });

    document.getElementById('tempBtn').addEventListener('click', () => {
        dataType = 'temp';
        updateUI();
        updateDisplay();
    });

    document.getElementById('yearSlider').addEventListener('input', (e) => {
        currentYear = parseInt(e.target.value);
        updateUI();
        updateDisplay();
    });

    document.getElementById('monthSlider').addEventListener('input', (e) => {
        currentMonth = parseInt(e.target.value);
        updateUI();
        updateDisplay();
    });

    document.getElementById('opacitySlider').addEventListener('input', (e) => {
        opacity = parseInt(e.target.value) / 100;
        updateUI();
        if (currentOverlay) {
            currentOverlay.setOpacity(opacity);
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
