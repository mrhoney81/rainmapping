// ============================================================================
// UK CLIMATE INTERACTIVE VIEWER - Main Application
// ============================================================================

// --- GLOBAL STATE ---
let metadata = null;
let locations = [];
let currentYear = 2022;
let currentMonth = 1;
let viewMode = 'monthly'; // 'monthly' or 'averages'
let isPlaying = false;
let animationSpeed = 500;
let canvas, ctx;
let imageCache = new Map();
let currentImage = null;

// Zoom and Pan state
let zoomLevel = 1;
let panX = 0;
let panY = 0;
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;

// Month names for display
const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
    console.log('Initializing UK Climate Viewer...');

    // Get canvas element
    canvas = document.getElementById('mapCanvas');
    ctx = canvas.getContext('2d');

    try {
        // Load metadata
        console.log('Loading metadata...');
        const metadataResponse = await fetch('data/metadata.json');
        if (!metadataResponse.ok) {
            throw new Error('Failed to load metadata.json');
        }
        metadata = await metadataResponse.json();
        console.log('Metadata loaded:', metadata);

        // Load locations
        console.log('Loading locations...');
        const locationsResponse = await fetch('data/locations.json');
        if (!locationsResponse.ok) {
            throw new Error('Failed to load locations.json');
        }
        locations = await locationsResponse.json();
        console.log(`Loaded ${locations.length} locations`);

        // Load custom locations from local storage
        loadCustomLocations();

        // Setup canvas dimensions
        setupCanvas();

        // Setup event listeners
        setupEventListeners();

        // Initialize UI
        updateLocationList();
        updateUI();

        // Parse URL parameters
        parseURLParameters();

        // Load initial display
        await updateDisplay();

        console.log('Initialization complete!');

    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to initialize application. Please check that data files are present.');
    }
}

// ============================================================================
// CANVAS SETUP
// ============================================================================

function setupCanvas() {
    // Set canvas size to maintain aspect ratio of data
    const containerWidth = canvas.parentElement.clientWidth - 4; // Account for border

    if (metadata && metadata.extent) {
        const dataAspect = (metadata.extent.y_max - metadata.extent.y_min) /
                          (metadata.extent.x_max - metadata.extent.x_min);

        canvas.width = containerWidth;
        canvas.height = containerWidth * dataAspect;

        console.log(`Canvas dimensions: ${canvas.width}x${canvas.height}, aspect ratio: ${dataAspect}`);
    } else {
        // Default fallback
        canvas.width = containerWidth;
        canvas.height = containerWidth * 1.8; // Approximate UK aspect ratio
    }
}

// Resize canvas when window resizes
window.addEventListener('resize', () => {
    setupCanvas();
    updateDisplay();
});

// ============================================================================
// COORDINATE TRANSFORMATION
// ============================================================================

/**
 * Convert British National Grid coordinates to pixel coordinates on the canvas
 * @param {number} bng_x - British National Grid X coordinate
 * @param {number} bng_y - British National Grid Y coordinate
 * @param {number} canvasWidth - Canvas width in pixels
 * @param {number} canvasHeight - Canvas height in pixels
 * @returns {Array} [pixel_x, pixel_y]
 */
function britishGridToPixel(bng_x, bng_y, canvasWidth, canvasHeight) {
    if (!metadata || !metadata.extent) {
        console.error('Metadata not loaded');
        return [0, 0];
    }

    const {x_min, x_max, y_min, y_max} = metadata.extent;

    // Linear interpolation for x
    const pixel_x = ((bng_x - x_min) / (x_max - x_min)) * canvasWidth;

    // Y is flipped (image origin is top-left, BNG origin is bottom-left)
    const pixel_y = canvasHeight - ((bng_y - y_min) / (y_max - y_min)) * canvasHeight;

    return [pixel_x, pixel_y];
}

/**
 * Convert pixel coordinates to British National Grid coordinates
 * @param {number} pixel_x - Pixel X coordinate
 * @param {number} pixel_y - Pixel Y coordinate
 * @param {number} canvasWidth - Canvas width in pixels
 * @param {number} canvasHeight - Canvas height in pixels
 * @returns {Array} [bng_x, bng_y]
 */
function pixelToBritishGrid(pixel_x, pixel_y, canvasWidth, canvasHeight) {
    if (!metadata || !metadata.extent) {
        console.error('Metadata not loaded');
        return [0, 0];
    }

    // Adjust for zoom and pan
    const adjusted_x = (pixel_x - panX) / zoomLevel;
    const adjusted_y = (pixel_y - panY) / zoomLevel;

    const {x_min, x_max, y_min, y_max} = metadata.extent;

    const bng_x = x_min + (adjusted_x / canvasWidth) * (x_max - x_min);
    const bng_y = y_min + ((canvasHeight - adjusted_y) / canvasHeight) * (y_max - y_min);

    return [Math.round(bng_x), Math.round(bng_y)];
}

// ============================================================================
// IMAGE LOADING AND DISPLAY
// ============================================================================

/**
 * Load an image with caching
 * @param {string} path - Path to the image
 * @returns {Promise<Image>}
 */
async function loadImage(path) {
    // Check cache first
    if (imageCache.has(path)) {
        return imageCache.get(path);
    }

    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            imageCache.set(path, img);
            resolve(img);
        };
        img.onerror = () => {
            reject(new Error(`Failed to load image: ${path}`));
        };
        img.src = path;
    });
}

/**
 * Update the display with the current year/month or average
 */
async function updateDisplay() {
    try {
        // Construct image path
        const imagePath = viewMode === 'monthly'
            ? `data/images/${currentYear}/${String(currentMonth).padStart(2, '0')}.png`
            : `data/averages/${String(currentMonth).padStart(2, '0')}.png`;

        // Load and display image
        const img = await loadImage(imagePath);
        currentImage = img;

        // Clear canvas and draw image with zoom/pan transformation
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Save the current context state
        ctx.save();

        // Apply zoom and pan transformations
        ctx.translate(panX, panY);
        ctx.scale(zoomLevel, zoomLevel);

        // Draw the image
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        // Draw locations on top
        drawLocations();

        // Restore the context state
        ctx.restore();

        // Preload adjacent images for smooth navigation
        preloadAdjacentImages();

    } catch (error) {
        console.error('Error updating display:', error);
        showError(`Failed to load image for ${MONTH_NAMES[currentMonth - 1]} ${viewMode === 'monthly' ? currentYear : 'average'}`);
    }
}

/**
 * Preload adjacent months for smooth navigation
 */
function preloadAdjacentImages() {
    if (viewMode === 'monthly') {
        // Preload next/previous month in same year
        const nextMonth = currentMonth === 12 ? 1 : currentMonth + 1;
        const prevMonth = currentMonth === 1 ? 12 : currentMonth - 1;
        const nextYear = currentMonth === 12 ? currentYear + 1 : currentYear;
        const prevYear = currentMonth === 1 ? currentYear - 1 : currentYear;

        if (metadata && metadata.years) {
            if (metadata.years.includes(nextYear)) {
                loadImage(`data/images/${nextYear}/${String(nextMonth).padStart(2, '0')}.png`).catch(() => {});
            }
            if (metadata.years.includes(prevYear)) {
                loadImage(`data/images/${prevYear}/${String(prevMonth).padStart(2, '0')}.png`).catch(() => {});
            }
        }
    } else {
        // Preload next/previous average
        const nextMonth = currentMonth === 12 ? 1 : currentMonth + 1;
        const prevMonth = currentMonth === 1 ? 12 : currentMonth - 1;

        loadImage(`data/averages/${String(nextMonth).padStart(2, '0')}.png`).catch(() => {});
        loadImage(`data/averages/${String(prevMonth).padStart(2, '0')}.png`).catch(() => {});
    }
}

// ============================================================================
// LOCATION DRAWING
// ============================================================================

/**
 * Draw all visible locations on the map
 */
function drawLocations() {
    locations.forEach(loc => {
        if (!loc.visible) return;

        const [px, py] = britishGridToPixel(loc.x, loc.y, canvas.width, canvas.height);

        // Check if location is within canvas bounds
        if (px < 0 || px > canvas.width || py < 0 || py > canvas.height) {
            return;
        }

        // Draw marker (circle with outline)
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#dc2626'; // Red
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();

        // Draw label with background
        ctx.font = 'bold 13px Arial';
        const textWidth = ctx.measureText(loc.name).width;
        const textHeight = 14;
        const padding = 6;

        // Draw dark semi-transparent background for better readability
        ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
        ctx.fillRect(px + 8, py - textHeight/2 - padding/2, textWidth + padding * 2, textHeight + padding);

        // Draw text with white color for better contrast
        ctx.fillStyle = '#ffffff';
        ctx.fillText(loc.name, px + 10 + padding/2, py + 4);
    });
}

// ============================================================================
// UI UPDATE FUNCTIONS
// ============================================================================

/**
 * Update UI elements to reflect current state
 */
function updateUI() {
    // Update year/month displays
    document.getElementById('yearValue').textContent = currentYear;
    document.getElementById('monthValue').textContent = MONTH_NAMES[currentMonth - 1];
    document.getElementById('yearSlider').value = currentYear;
    document.getElementById('monthSlider').value = currentMonth;

    // Update view mode buttons
    document.getElementById('monthlyBtn').classList.toggle('active', viewMode === 'monthly');
    document.getElementById('averagesBtn').classList.toggle('active', viewMode === 'averages');

    // Disable/enable year slider based on view mode
    document.getElementById('yearSlider').disabled = viewMode === 'averages';

    // Update play button
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    if (isPlaying) {
        playIcon.textContent = '⏸';
        playText.textContent = 'Pause';
    } else {
        playIcon.textContent = '▶';
        playText.textContent = 'Play';
    }

    // Update URL
    updateURL();
}

/**
 * Update location list in the sidebar
 */
function updateLocationList() {
    const locationList = document.getElementById('locationList');
    const searchTerm = document.getElementById('locationSearch').value.toLowerCase();

    // Filter locations based on search
    const filteredLocations = locations.filter(loc =>
        loc.name.toLowerCase().includes(searchTerm)
    );

    // Sort: visible first, then alphabetically
    filteredLocations.sort((a, b) => {
        if (a.visible !== b.visible) return b.visible - a.visible;
        return a.name.localeCompare(b.name);
    });

    // Build HTML
    locationList.innerHTML = filteredLocations.map((loc, index) => `
        <div class="location-item ${loc.visible ? 'visible' : ''}" data-index="${locations.indexOf(loc)}">
            <div>
                <div class="location-name">${loc.name}</div>
                <div class="location-type">${loc.type}</div>
            </div>
            <div class="location-actions">
                <button class="location-toggle" onclick="toggleLocation(${locations.indexOf(loc)})">
                    ${loc.visible ? 'Hide' : 'Show'}
                </button>
                ${loc.custom ? `<button class="location-remove" onclick="removeLocation(${locations.indexOf(loc)})">Remove</button>` : ''}
            </div>
        </div>
    `).join('');
}

// ============================================================================
// ANIMATION
// ============================================================================

/**
 * Animation loop for play mode
 */
function playAnimation() {
    if (!isPlaying) return;

    // Advance to next month
    currentMonth++;

    if (currentMonth > 12) {
        currentMonth = 1;

        if (viewMode === 'monthly') {
            currentYear++;

            // Loop back to start if we reach the end
            if (metadata && metadata.years && currentYear > metadata.years[metadata.years.length - 1]) {
                currentYear = metadata.years[0];
            }
        }
    }

    updateDisplay();
    updateUI();

    // Schedule next frame
    setTimeout(playAnimation, animationSpeed);
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // View mode toggle
    document.getElementById('monthlyBtn').addEventListener('click', () => {
        viewMode = 'monthly';
        updateUI();
        updateDisplay();
    });

    document.getElementById('averagesBtn').addEventListener('click', () => {
        viewMode = 'averages';
        updateUI();
        updateDisplay();
    });

    // Year slider
    document.getElementById('yearSlider').addEventListener('input', (e) => {
        currentYear = parseInt(e.target.value);
        updateUI();
        updateDisplay();
    });

    // Month slider
    document.getElementById('monthSlider').addEventListener('input', (e) => {
        currentMonth = parseInt(e.target.value);
        updateUI();
        updateDisplay();
    });

    // Play/pause button
    document.getElementById('playBtn').addEventListener('click', () => {
        isPlaying = !isPlaying;
        updateUI();
        if (isPlaying) {
            playAnimation();
        }
    });

    // Speed selector
    document.getElementById('speedSelect').addEventListener('change', (e) => {
        animationSpeed = parseInt(e.target.value);
    });

    // Location search
    document.getElementById('locationSearch').addEventListener('input', () => {
        updateLocationList();
    });

    // Toggle all locations
    document.getElementById('toggleAllLocations').addEventListener('click', () => {
        const anyVisible = locations.some(loc => loc.visible);
        locations.forEach(loc => loc.visible = !anyVisible);
        updateLocationList();
        updateDisplay();

        // Update button text
        document.getElementById('toggleAllLocations').textContent = anyVisible ? 'Show All' : 'Hide All';
    });

    // Add custom location button
    document.getElementById('addCustomBtn').addEventListener('click', () => {
        showCustomLocationModal();
    });

    // Reset zoom button
    document.getElementById('resetZoomBtn').addEventListener('click', () => {
        zoomLevel = 1;
        panX = 0;
        panY = 0;
        updateDisplay();
    });

    // Custom location modal
    document.getElementById('saveCustomLocation').addEventListener('click', () => {
        saveCustomLocationFromModal();
    });

    document.getElementById('cancelCustomLocation').addEventListener('click', () => {
        hideCustomLocationModal();
    });

    // Canvas click to add location
    canvas.addEventListener('click', (e) => {
        if (e.shiftKey) {
            const rect = canvas.getBoundingClientRect();
            const px = (e.clientX - rect.left) * (canvas.width / rect.width);
            const py = (e.clientY - rect.top) * (canvas.height / rect.height);

            const [bng_x, bng_y] = pixelToBritishGrid(px, py, canvas.width, canvas.height);
            showCustomLocationModal(bng_x, bng_y);
        }
    });

    canvas.addEventListener('mouseleave', () => {
        document.getElementById('coordsDisplay').classList.remove('active');
        isDragging = false;
    });

    // Zoom with mouse wheel
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();

        const rect = canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
        const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);

        // Zoom in or out
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        const newZoom = Math.max(1, Math.min(10, zoomLevel * zoomFactor));

        // Adjust pan to zoom toward mouse position
        if (newZoom !== zoomLevel) {
            const scale = newZoom / zoomLevel;
            panX = mouseX - (mouseX - panX) * scale;
            panY = mouseY - (mouseY - panY) * scale;
            zoomLevel = newZoom;

            updateDisplay();
        }
    }, { passive: false });

    // Pan with mouse drag
    canvas.addEventListener('mousedown', (e) => {
        if (!e.shiftKey) { // Only drag when not adding a location
            isDragging = true;
            const rect = canvas.getBoundingClientRect();
            lastMouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
            lastMouseY = (e.clientY - rect.top) * (canvas.height / rect.height);
            canvas.style.cursor = 'grabbing';
        }
    });

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
        const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);

        if (isDragging) {
            const dx = mouseX - lastMouseX;
            const dy = mouseY - lastMouseY;

            panX += dx;
            panY += dy;

            lastMouseX = mouseX;
            lastMouseY = mouseY;

            updateDisplay();
        }

        // Update coordinates display
        const [bng_x, bng_y] = pixelToBritishGrid(mouseX, mouseY, canvas.width, canvas.height);
        const coordsDisplay = document.getElementById('coordsDisplay');
        coordsDisplay.textContent = `BNG: ${bng_x}, ${bng_y} | Zoom: ${zoomLevel.toFixed(1)}x`;
        coordsDisplay.classList.add('active');
    });

    canvas.addEventListener('mouseup', () => {
        isDragging = false;
        canvas.style.cursor = 'crosshair';
    });

    // Touch support for mobile devices
    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartDistance = 0;
    let initialPanX = 0;
    let initialPanY = 0;
    let initialZoom = 1;
    let isTwoFingerTouch = false;

    canvas.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
            // Two finger pinch zoom
            e.preventDefault();
            isTwoFingerTouch = true;

            const touch1 = e.touches[0];
            const touch2 = e.touches[1];

            touchStartDistance = Math.hypot(
                touch2.clientX - touch1.clientX,
                touch2.clientY - touch1.clientY
            );

            initialZoom = zoomLevel;
            initialPanX = panX;
            initialPanY = panY;
        } else if (e.touches.length === 1) {
            // Single finger pan (but only if already zoomed in)
            if (zoomLevel > 1) {
                e.preventDefault();
                const rect = canvas.getBoundingClientRect();
                const touch = e.touches[0];
                touchStartX = (touch.clientX - rect.left) * (canvas.width / rect.width);
                touchStartY = (touch.clientY - rect.top) * (canvas.height / rect.height);
                initialPanX = panX;
                initialPanY = panY;
                isDragging = true;
            }
            // Otherwise allow normal page scrolling
        }
    }, { passive: false });

    canvas.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2 && isTwoFingerTouch) {
            e.preventDefault();

            const touch1 = e.touches[0];
            const touch2 = e.touches[1];

            const currentDistance = Math.hypot(
                touch2.clientX - touch1.clientX,
                touch2.clientY - touch1.clientY
            );

            const scale = currentDistance / touchStartDistance;
            const newZoom = Math.max(1, Math.min(10, initialZoom * scale));

            if (newZoom !== zoomLevel) {
                zoomLevel = newZoom;
                updateDisplay();
            }
        } else if (e.touches.length === 1 && isDragging && zoomLevel > 1) {
            e.preventDefault();

            const rect = canvas.getBoundingClientRect();
            const touch = e.touches[0];
            const currentX = (touch.clientX - rect.left) * (canvas.width / rect.width);
            const currentY = (touch.clientY - rect.top) * (canvas.height / rect.height);

            const dx = currentX - touchStartX;
            const dy = currentY - touchStartY;

            panX = initialPanX + dx;
            panY = initialPanY + dy;

            updateDisplay();
        }
    }, { passive: false });

    canvas.addEventListener('touchend', (e) => {
        if (e.touches.length === 0) {
            isDragging = false;
            isTwoFingerTouch = false;
        } else if (e.touches.length === 1) {
            isTwoFingerTouch = false;

            if (zoomLevel > 1) {
                const rect = canvas.getBoundingClientRect();
                const touch = e.touches[0];
                touchStartX = (touch.clientX - rect.left) * (canvas.width / rect.width);
                touchStartY = (touch.clientY - rect.top) * (canvas.height / rect.height);
                initialPanX = panX;
                initialPanY = panY;
            }
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                currentMonth--;
                if (currentMonth < 1) {
                    currentMonth = 12;
                    if (viewMode === 'monthly') currentYear--;
                }
                updateUI();
                updateDisplay();
                break;
            case 'ArrowRight':
                e.preventDefault();
                currentMonth++;
                if (currentMonth > 12) {
                    currentMonth = 1;
                    if (viewMode === 'monthly') currentYear++;
                }
                updateUI();
                updateDisplay();
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (viewMode === 'monthly') {
                    currentYear++;
                    updateUI();
                    updateDisplay();
                }
                break;
            case 'ArrowDown':
                e.preventDefault();
                if (viewMode === 'monthly') {
                    currentYear--;
                    updateUI();
                    updateDisplay();
                }
                break;
            case ' ':
                e.preventDefault();
                isPlaying = !isPlaying;
                updateUI();
                if (isPlaying) playAnimation();
                break;
            case '+':
            case '=':
                e.preventDefault();
                zoomLevel = Math.min(10, zoomLevel * 1.2);
                updateDisplay();
                break;
            case '-':
            case '_':
                e.preventDefault();
                zoomLevel = Math.max(1, zoomLevel / 1.2);
                if (zoomLevel === 1) {
                    panX = 0;
                    panY = 0;
                }
                updateDisplay();
                break;
            case '0':
                e.preventDefault();
                zoomLevel = 1;
                panX = 0;
                panY = 0;
                updateDisplay();
                break;
        }
    });
}

// ============================================================================
// LOCATION MANAGEMENT
// ============================================================================

/**
 * Toggle visibility of a location
 */
function toggleLocation(index) {
    locations[index].visible = !locations[index].visible;
    updateLocationList();
    updateDisplay();

    // Save custom locations to local storage
    saveCustomLocations();
}

/**
 * Remove a custom location
 */
function removeLocation(index) {
    if (confirm(`Remove "${locations[index].name}"?`)) {
        locations.splice(index, 1);
        updateLocationList();
        updateDisplay();
        saveCustomLocations();
    }
}

/**
 * Show custom location modal
 */
function showCustomLocationModal(x = '', y = '') {
    const modal = document.getElementById('customLocationModal');
    modal.classList.add('active');

    document.getElementById('customLocationName').value = '';
    document.getElementById('customLocationX').value = x;
    document.getElementById('customLocationY').value = y;
    document.getElementById('customLocationName').focus();
}

/**
 * Hide custom location modal
 */
function hideCustomLocationModal() {
    document.getElementById('customLocationModal').classList.remove('active');
}

/**
 * Save custom location from modal
 */
function saveCustomLocationFromModal() {
    const name = document.getElementById('customLocationName').value.trim();
    const x = parseInt(document.getElementById('customLocationX').value);
    const y = parseInt(document.getElementById('customLocationY').value);

    if (!name || isNaN(x) || isNaN(y)) {
        alert('Please fill in all fields with valid values.');
        return;
    }

    // Add new location
    locations.push({
        name: name,
        x: x,
        y: y,
        type: 'custom',
        visible: true,
        custom: true
    });

    updateLocationList();
    updateDisplay();
    hideCustomLocationModal();
    saveCustomLocations();
}

/**
 * Save custom locations to local storage
 */
function saveCustomLocations() {
    const customLocations = locations.filter(loc => loc.custom);
    localStorage.setItem('ukClimateCustomLocations', JSON.stringify(customLocations));
}

/**
 * Load custom locations from local storage
 */
function loadCustomLocations() {
    const stored = localStorage.getItem('ukClimateCustomLocations');
    if (stored) {
        try {
            const customLocations = JSON.parse(stored);
            locations.push(...customLocations);
        } catch (e) {
            console.error('Error loading custom locations:', e);
        }
    }
}

// ============================================================================
// URL PARAMETERS
// ============================================================================

/**
 * Parse URL parameters
 */
function parseURLParameters() {
    const params = new URLSearchParams(window.location.search);

    if (params.has('year')) {
        const year = parseInt(params.get('year'));
        if (!isNaN(year)) currentYear = year;
    }

    if (params.has('month')) {
        const month = parseInt(params.get('month'));
        if (!isNaN(month) && month >= 1 && month <= 12) currentMonth = month;
    }

    if (params.has('view')) {
        const view = params.get('view');
        if (view === 'monthly' || view === 'averages') viewMode = view;
    }
}

/**
 * Update URL with current state
 */
function updateURL() {
    const params = new URLSearchParams();
    params.set('year', currentYear);
    params.set('month', currentMonth);
    params.set('view', viewMode);

    const newURL = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newURL);
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

/**
 * Show error message to user
 */
function showError(message) {
    // Simple error display - could be enhanced with a modal
    console.error(message);
    alert(message);
}

// ============================================================================
// START APPLICATION
// ============================================================================

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
