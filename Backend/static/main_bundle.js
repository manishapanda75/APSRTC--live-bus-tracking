const API_BASE = ""; // Relative path for same-domain deployment
let trackingMap = null;
let trackingMarker = null;
let trackingInterval = null;
let routeRoadPath = [];   // Stores the OSRM road-following coordinates for the current route
let routePolyline = null;
let lastReachedStopIndex = 0;
let socket = null;         // WebSocket connection
let currentTrackingService = null;  // Currently tracked service number
let notificationSent = {};  // Track which notifications have been sent

document.addEventListener("DOMContentLoaded", () => {
    initServiceVehicleSearch();
    initTicketSearch();
    initTimetableSearch();
    initRoutesView();
    loadStationsForAutocomplete();
    initStopsMap();
    initWebSocket();
    requestNotificationPermission();

    setHumanGreeting();

    // Version Indicator
    const brand = document.querySelector('.navbar-brand');
    if (brand) brand.innerHTML += ' <span style="font-size:0.5em; opacity: 0.5; margin-left: 8px;">v7.0</span>';
    console.log("APP VERSION: 7.0 — WebSocket + PWA + Notifications");
});


// ═══════════════════════════════════════════════════════
// 🔌 WEBSOCKET (Socket.IO)
// ═══════════════════════════════════════════════════════

function initWebSocket() {
    if (typeof io === 'undefined') {
        console.warn("[WS] Socket.IO not loaded — falling back to polling");
        return;
    }

    try {
        socket = io({ transports: ['websocket', 'polling'] });

        socket.on('connect', () => {
            console.log('[WS] Connected:', socket.id);
            // Re-join tracking room if we were tracking
            if (currentTrackingService) {
                socket.emit('join_tracking', { service_no: currentTrackingService });
            }
        });

        socket.on('disconnect', () => {
            console.log('[WS] Disconnected — will auto-reconnect');
        });

        socket.on('location_update', (data) => {
            console.log('[WS] Live update received:', data);
            if (data.service_no === currentTrackingService) {
                handleLiveUpdate(data);
            }
        });

        socket.on('connect_error', (err) => {
            console.warn('[WS] Connection error, falling back to polling:', err.message);
        });

    } catch (e) {
        console.warn('[WS] Failed to initialize WebSocket:', e);
    }
}

function joinTrackingRoom(serviceNo) {
    currentTrackingService = serviceNo;
    if (socket && socket.connected) {
        socket.emit('join_tracking', { service_no: serviceNo });
        console.log(`[WS] Joined room: track_${serviceNo}`);
    }
}

function leaveTrackingRoom() {
    if (socket && socket.connected && currentTrackingService) {
        socket.emit('leave_tracking', { service_no: currentTrackingService });
        console.log(`[WS] Left room: track_${currentTrackingService}`);
    }
    currentTrackingService = null;
    notificationSent = {};
}

function handleLiveUpdate(liveData) {
    // Update text info
    const speedEl = document.getElementById("speedValue");
    const locEl = document.getElementById("locValue");
    const updEl = document.getElementById("updatedValue");

    if (speedEl) speedEl.innerHTML = `<i class="bi bi-speedometer2"></i> ${liveData.speed} km/h`;
    if (locEl) locEl.innerHTML = `<i class="bi bi-geo-alt"></i> ${parseFloat(liveData.lat).toFixed(4)}, ${parseFloat(liveData.lng).toFixed(4)}`;
    if (updEl) updEl.innerHTML = `<i class="bi bi-clock-history"></i> Updated: ${liveData.updated_at.split(' ')[1] || liveData.updated_at}`;

    const lat = parseFloat(liveData.lat);
    const lng = parseFloat(liveData.lng);

    // Update map marker
    if (trackingMap) {
        if (!trackingMarker) {
            trackingMarker = L.marker([lat, lng], { icon: busIcon }).addTo(trackingMap)
                .bindPopup(`<b>${liveData.service_no}</b><br>Speed: ${liveData.speed} km/h`)
                .openPopup();
            trackingMap.setView([lat, lng], 15);
        } else {
            trackingMarker.setLatLng([lat, lng]);
            trackingMarker.setPopupContent(`<b>${liveData.service_no}</b><br>Speed: ${liveData.speed} km/h`);
        }
    }

    // Update timeline
    if (currentRouteStops.length > 1) {
        updateTimelineBusPosition(lat, lng);
    }

    // Update ETA
    updateETADisplay(liveData.service_no);

    // Check notifications
    checkStopNotifications(lat, lng);
}


// ═══════════════════════════════════════════════════════
// 🔔 NOTIFICATION SYSTEM
// ═══════════════════════════════════════════════════════

function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        // Don't immediately ask — wait for user interaction
        console.log('[Notify] Permission will be requested when user selects a destination stop');
    }
}

async function askNotificationPermission() {
    if (!('Notification' in window)) {
        console.warn('[Notify] Browser does not support notifications');
        return false;
    }
    if (Notification.permission === 'granted') return true;
    if (Notification.permission === 'denied') return false;

    const perm = await Notification.requestPermission();
    return perm === 'granted';
}

function sendBusNotification(title, body) {
    if (Notification.permission === 'granted') {
        const notif = new Notification(title, {
            body: body,
            icon: '/static/icons/icon-192.png',
            badge: '/static/icons/icon-192.png',
            vibrate: [200, 100, 200],
            tag: 'bus-proximity',
            renotify: true
        });
        // Also show a toast
        showToast(body, 'success');
    }
}

function checkStopNotifications(busLat, busLng) {
    const destSelect = document.getElementById('destinationStopSelect');
    if (!destSelect || !destSelect.value || currentRouteStops.length < 2) return;

    const destStopName = destSelect.value;

    // Find bus position in route
    let closestIdx = 0;
    let minDist = Infinity;
    for (let i = 0; i < currentRouteStops.length; i++) {
        const d = getDistance(busLat, busLng, currentRouteStops[i].lat, currentRouteStops[i].lng);
        if (d < minDist) { minDist = d; closestIdx = i; }
    }

    // Find destination stop index
    let destIdx = -1;
    for (let i = 0; i < currentRouteStops.length; i++) {
        if (currentRouteStops[i].name === destStopName) { destIdx = i; break; }
    }
    if (destIdx === -1) return;

    const stopsAway = destIdx - closestIdx;

    // Update stops-away indicator
    const stopsAwayEl = document.getElementById('stopsAwayIndicator');
    if (stopsAwayEl) {
        if (stopsAway > 0) {
            stopsAwayEl.innerHTML = `<i class="bi bi-geo-alt-fill"></i> <b>${stopsAway}</b> stop${stopsAway > 1 ? 's' : ''} away from ${destStopName}`;
            stopsAwayEl.style.display = 'block';
        } else if (stopsAway === 0) {
            stopsAwayEl.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> <b>Arrived</b> at ${destStopName}!`;
            stopsAwayEl.style.display = 'block';
        } else {
            stopsAwayEl.innerHTML = `<i class="bi bi-arrow-left-circle"></i> Bus has passed ${destStopName}`;
            stopsAwayEl.style.display = 'block';
        }
    }

    // Send notifications at 2 stops and 1 stop away
    if (stopsAway === 2 && !notificationSent['2stops']) {
        notificationSent['2stops'] = true;
        sendBusNotification('🚌 Bus Approaching!', `Bus is 2 stops away from ${destStopName}. Get ready!`);
    }
    if (stopsAway === 1 && !notificationSent['1stop']) {
        notificationSent['1stop'] = true;
        sendBusNotification('🚌 Almost There!', `Bus is 1 stop away from ${destStopName}. Please prepare to board!`);
    }
    if (stopsAway === 0 && !notificationSent['arrived']) {
        notificationSent['arrived'] = true;
        sendBusNotification('🚌 Bus Arrived!', `Bus has arrived at ${destStopName}!`);
    }
}


// ═══════════════════════════════════════════════════════
// 🍞 TOAST SYSTEM
// ═══════════════════════════════════════════════════════

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `custom-toast ${type}`;
    
    let icon = 'bi-check-circle-fill';
    if (type === 'error') icon = 'bi-exclamation-triangle-fill';
    if (type === 'warning') icon = 'bi-info-circle-fill';

    toast.innerHTML = `
        <i class="bi ${icon} toast-icon"></i>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeOutRight 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}


// ═══════════════════════════════════════════════════════
// 🌅 GREETING & SKELETON
// ═══════════════════════════════════════════════════════

function setHumanGreeting() {
    const header = document.getElementById("greetingHeader");
    if (!header) return;
    const hour = new Date().getHours();
    let greeting = "Good Evening!";
    if (hour < 12) greeting = "Good Morning!";
    else if (hour < 17) greeting = "Good Afternoon!";
    header.innerText = greeting;
}

function getSkeletonHTML(count = 1) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `
            <div class="skeleton-card">
                <div class="skeleton skeleton-title"></div>
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text-short"></div>
            </div>
        `;
    }
    return html;
}


// ═══════════════════════════════════════════════════════
// 🔍 SERVICE / VEHICLE SEARCH + LIVE TRACKING
// ═══════════════════════════════════════════════════════

function initServiceVehicleSearch() {
    const searchBtn = document.getElementById("searchBtn");
    const resultBox = document.getElementById("trackingResult");

    searchBtn.addEventListener("click", async () => {
        const searchInput = document.getElementById("searchInput").value.trim();
        const activeOption = document.querySelector(".toggle-option.active");
        const type = activeOption.getAttribute("data-type");

        if (!searchInput) {
            showToast("Please enter a service or vehicle number", "warning");
            return;
        }

        // Clear previous tracking
        if (trackingInterval) clearInterval(trackingInterval);
        leaveTrackingRoom();

        resultBox.innerHTML = getSkeletonHTML(1);

        try {
            let url = "";
            if (type === "service") {
                url = `${API_BASE}/api/service/${searchInput}`;
            } else {
                url = `${API_BASE}/api/vehicle/${searchInput}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                resultBox.innerHTML = '';
                showToast("Not found in database", "error");
                return;
            }

            const data = await response.json();
            let html = "";

            if (type === "service") {
                const serviceNo = data.service_no;

                html = `
                    <div class="bus-card fade-in">
                         <div class="bus-header">
                            <span class="service-no">${serviceNo}</span>
                            <span class="bus-type">Service</span>
                        </div>
                        <div class="route-info"><i class="bi bi-signpost-split"></i> ${data.route}</div>
                        
                        <div class="mt-3 p-2 bg-light rounded border">
                            <div class="d-flex justify-content-between">
                                <span id="speedValue"><i class="bi bi-speedometer2"></i> -- km/h</span>
                                <span class="text-success fw-bold">RUNNING</span>
                            </div>
                             <div class="small text-muted mt-1" id="locValue">
                                <i class="bi bi-geo-alt"></i> --, --
                            </div>
                             <div class="small text-muted" id="updatedValue">
                                <i class="bi bi-clock-history"></i> Updated: --
                            </div>
                        </div>

                        <!-- ETA Display -->
                        <div class="eta-display mt-3 p-3 rounded-3" id="etaDisplay" style="display: none;">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="small text-muted fw-bold">ETA</div>
                                    <div class="eta-time" id="etaTime">-- min</div>
                                </div>
                                <div class="text-end">
                                    <div class="small text-muted fw-bold">DISTANCE</div>
                                    <div class="eta-distance" id="etaDistance">-- km</div>
                                </div>
                                <div class="text-end">
                                    <div class="small text-muted fw-bold">STOPS</div>
                                    <div class="eta-stops" id="etaStops">--</div>
                                </div>
                            </div>
                        </div>

                        <!-- Destination Stop Selector + Notification -->
                        <div class="mt-3" id="destSelectWrapper" style="display: none;">
                            <label class="form-label small text-muted fw-bold">🔔 NOTIFY ME AT</label>
                            <select id="destinationStopSelect" class="form-select form-select-sm" onchange="onDestinationSelected()">
                                <option value="">Select destination stop...</option>
                            </select>
                            <div id="stopsAwayIndicator" class="stops-away-badge mt-2" style="display: none;"></div>
                        </div>

                        <!-- TIMELINE VS MAP TOGGLE -->
                        <div class="d-flex justify-content-center mt-3 mb-3">
                            <div class="btn-group btn-group-sm" role="group">
                                <input type="radio" class="btn-check" name="viewToggle" id="btnTimeline" autocomplete="off" checked onchange="toggleTrackingView('timeline')">
                                <label class="btn btn-outline-primary" for="btnTimeline"><i class="bi bi-distribute-vertical"></i> Route Progress</label>

                                <input type="radio" class="btn-check" name="viewToggle" id="btnMap" autocomplete="off" onchange="toggleTrackingView('map')">
                                <label class="btn btn-outline-primary" for="btnMap"><i class="bi bi-map"></i> GPS Map</label>
                            </div>
                        </div>

                        <!-- TIMELINE CONTAINER (Default) -->
                        <div id="timelineContainer" style="display: block;">
                            <div class="text-center p-4 text-muted" id="timelineLoading">
                                <i class="bi bi-hourglass-split spinning"></i> Loading route map...
                            </div>
                            <div id="routeTimelineGrid" class="route-timeline" style="display: none;">
                                <div class="timeline-line"></div>
                                <div id="busTrackerIcon" class="bus-tracker-icon" style="top: 0%;">
                                    <img src="https://img.icons8.com/color/48/bus.png" alt="Bus">
                                </div>
                                <div id="timelineStopsWrapper"></div>
                            </div>
                        </div>

                        <!-- MAP CONTAINER (Hidden initially) -->
                        <div id="mapContainer" style="display: none;">
                            <div id="map" style="height: 400px; width: 100%; border-radius: 8px; z-index: 1;"></div>
                        </div>

                        <!-- ROUTE STOPS PANEL -->
                        <div class="tracking-stops-panel mt-3" id="trackingStopsPanel" style="display: none;">
                            <h6 class="fw-bold mb-2" style="color: var(--primary-color);"><i class="bi bi-geo-alt"></i> Route Stops</h6>
                            <div id="trackingStopsList" class="tracking-stops-list"></div>
                        </div>
                    </div>
                `;

                resultBox.innerHTML = html;

                // Start Live Tracking
                startLiveMap(serviceNo);

            } else {
                html = `
                    <div class="bus-card fade-in">
                        <div class="bus-header">
                            <span class="service-no">${data.vehicle_no}</span>
                            <span class="bus-type ${data.status === 'Running' ? 'text-success' : 'text-danger'}">${data.status}</span>
                        </div>
                        <div class="route-info">Service: <b>${data.service_no}</b></div>
                        <div class="vehicle-info"><i class="bi bi-signpost-split"></i> ${data.route}</div>
                    </div>
                `;
                resultBox.innerHTML = html;
            }

        } catch (error) {
            console.error(error);
            resultBox.innerHTML = '';
            showToast("Backend Connection Failed", "error");
        }
    });
}

let currentRouteStops = [];

// Toggle View Helper
window.toggleTrackingView = function (view) {
    if (view === 'timeline') {
        document.getElementById('timelineContainer').style.display = 'block';
        document.getElementById('mapContainer').style.display = 'none';
    } else {
        document.getElementById('timelineContainer').style.display = 'none';
        document.getElementById('mapContainer').style.display = 'block';
        if (trackingMap) trackingMap.invalidateSize();
    }
};

async function startLiveMap(serviceNo) {
    // 0. Reset UI
    document.getElementById('timelineLoading').style.display = 'block';
    document.getElementById('routeTimelineGrid').style.display = 'none';
    currentRouteStops = [];
    notificationSent = {};

    // 1. Initialize Map Container
    if (trackingMap) {
        trackingMap.off();
        trackingMap.remove();
        trackingMap = null;
    }
    trackingMarker = null;

    trackingMap = L.map('map').setView([17.6868, 83.2185], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(trackingMap);

    // 2. Fetch and Plot Route
    await drawRouteOnMap(serviceNo);

    // 3. Join WebSocket room
    joinTrackingRoom(serviceNo);

    // 4. Initial Live Location Check
    await updateMapLocation(serviceNo);

    // 5. Fallback polling (in case WebSocket fails or is unavailable)
    trackingInterval = setInterval(() => {
        if (!socket || !socket.connected) {
            updateMapLocation(serviceNo);
        }
    }, 5000);
}

// Custom Bus Icon for Leaflet
const busIcon = L.icon({
    iconUrl: 'https://img.icons8.com/color/48/bus.png',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20]
});

// Haversine Distance Formula (km)
function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// OSRM Road-Network Helper
async function fetchOsrmRoute(waypoints) {
    try {
        const coordStr = waypoints.map(([lat, lng]) => `${lng},${lat}`).join(';');
        const url = `https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`;

        const res = await fetch(url);
        if (!res.ok) return null;

        const data = await res.json();
        if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) return null;

        return data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng]);
    } catch (err) {
        return null;
    }
}

async function drawRouteOnMap(serviceNo) {
    try {
        lastReachedStopIndex = 0; // Reset for new route
        const res = await fetch(`${API_BASE}/api/route_details/${serviceNo}`);
        if (!res.ok) return;

        const stops = await res.json();
        if (!stops || stops.length === 0) return;

        currentRouteStops = stops;

        // ── Populate Timeline UI ──
        const timelineWrapper = document.getElementById('timelineStopsWrapper');
        let timelineHTML = '';
        stops.forEach((stop, index) => {
            const isTerm = (index === 0 || index === stops.length - 1) ? 'terminal' : '';
            timelineHTML += `
                <div class="timeline-stop ${isTerm}" id="stop-${index}">
                    <div class="stop-node"></div>
                    <div class="stop-name">${stop.name}</div>
                    <div class="stop-dist"><i class="bi bi-geo"></i> Stop ${index + 1}</div>
                </div>
            `;
        });
        timelineWrapper.innerHTML = timelineHTML;
        document.getElementById('timelineLoading').style.display = 'none';
        document.getElementById('routeTimelineGrid').style.display = 'block';

        // ── Populate Destination Stop Selector ──
        const destSelect = document.getElementById('destinationStopSelect');
        if (destSelect) {
            destSelect.innerHTML = '<option value="">Select destination stop...</option>';
            stops.forEach((stop, idx) => {
                destSelect.innerHTML += `<option value="${stop.name}">${stop.name}${idx === 0 || idx === stops.length - 1 ? ' (Terminal)' : ''}</option>`;
            });
            document.getElementById('destSelectWrapper').style.display = 'block';
        }

        // ── Populate Tracking Stops Panel ──
        renderTrackingStopsPanel(stops);

        // ── Render Geographic Map ──
        const stopCoords = stops.map(s => [s.lat, s.lng]);
        const roadPath = await fetchOsrmRoute(stopCoords);

        if (roadPath && roadPath.length > 1) {
            routeRoadPath = roadPath;
            L.polyline(roadPath, { color: '#1a73e8', weight: 5, opacity: 0.85, lineJoin: 'round' }).addTo(trackingMap);
        } else {
            routeRoadPath = stopCoords;
            L.polyline(stopCoords, { color: 'blue', weight: 4, opacity: 0.7, dashArray: '8, 8' }).addTo(trackingMap);
        }

        // ── Add Stop Markers with Labels ──
        const terminalIcon = new L.Icon.Default();
        const stopIcon = L.divIcon({
            className: '',
            html: `<div style="width:14px;height:14px;background:#1a73e8;border:2px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
            popupAnchor: [0, -10]
        });

        stops.forEach((stop, i) => {
            const isTerminal = (i === 0 || i === stops.length - 1);
            const icon = isTerminal ? terminalIcon : stopIcon;

            const marker = L.marker([stop.lat, stop.lng], { icon })
                .addTo(trackingMap)
                .bindPopup(`🚏 <b>${stop.name}</b>${isTerminal ? ' (Terminal)' : ''}<br><small>Stop ${i + 1}</small>`);

            // Add permanent label for all stops on map
            L.marker([stop.lat, stop.lng], {
                icon: L.divIcon({
                    className: 'stop-map-label',
                    html: `<span>${stop.name}</span>`,
                    iconAnchor: [-10, 6]
                })
            }).addTo(trackingMap);
        });

        trackingMap.fitBounds(roadPath && roadPath.length > 1 ? roadPath : stopCoords);

    } catch (err) {
        console.error('Error drawing route:', err);
    }
}

function renderTrackingStopsPanel(stops) {
    const panel = document.getElementById('trackingStopsPanel');
    const list = document.getElementById('trackingStopsList');
    if (!panel || !list) return;

    let html = '';
    stops.forEach((stop, idx) => {
        const isTerminal = (idx === 0 || idx === stops.length - 1);
        html += `
            <div class="tracking-stop-item ${isTerminal ? 'terminal' : ''}" id="tracking-stop-${idx}">
                <div class="tracking-stop-dot"></div>
                <div class="tracking-stop-info">
                    <div class="tracking-stop-name">${stop.name}</div>
                    <div class="tracking-stop-meta">Stop ${idx + 1}${isTerminal ? ' • Terminal' : ''}</div>
                </div>
                <div class="tracking-stop-dist" id="tracking-stop-dist-${idx}">--</div>
            </div>
        `;
    });
    list.innerHTML = html;
    panel.style.display = 'block';
}

function updateTrackingStopsDistances(busLat, busLng) {
    if (!currentRouteStops.length) return;

    let closestIdx = 0;
    let minDist = Infinity;

    currentRouteStops.forEach((stop, idx) => {
        const dist = getDistance(busLat, busLng, stop.lat, stop.lng);
        const distEl = document.getElementById(`tracking-stop-dist-${idx}`);
        if (distEl) {
            distEl.textContent = dist < 1 ? `${(dist * 1000).toFixed(0)}m` : `${dist.toFixed(1)}km`;
        }

        if (dist < minDist) {
            minDist = dist;
            closestIdx = idx;
        }

        // Remove previous highlight
        const itemEl = document.getElementById(`tracking-stop-${idx}`);
        if (itemEl) itemEl.classList.remove('nearest');
    });

    // Highlight nearest stop
    const nearestEl = document.getElementById(`tracking-stop-${closestIdx}`);
    if (nearestEl) {
        nearestEl.classList.add('nearest');
        nearestEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

async function onDestinationSelected() {
    const destSelect = document.getElementById('destinationStopSelect');
    if (!destSelect || !destSelect.value) return;

    // Request notification permission when user selects a destination
    const granted = await askNotificationPermission();
    if (granted) {
        showToast(`🔔 Notifications enabled for ${destSelect.value}`, 'success');
    }
    notificationSent = {}; // Reset notifications for new destination
}
window.onDestinationSelected = onDestinationSelected;


// ── ETA Display ──

async function updateETADisplay(serviceNo) {
    try {
        const destSelect = document.getElementById('destinationStopSelect');
        let etaUrl = `${API_BASE}/api/eta/${serviceNo}`;
        if (destSelect && destSelect.value) {
            etaUrl += `?destination=${encodeURIComponent(destSelect.value)}`;
        }

        const res = await fetch(etaUrl);
        if (!res.ok) return;

        const eta = await res.json();
        const display = document.getElementById('etaDisplay');
        if (display) {
            display.style.display = 'block';
            if (eta.bus_status === 'At Station') {
                document.getElementById('etaTime').innerHTML = `<span class="text-success fw-bold" style="font-size: 1.2rem;">Reached</span><br><small class="text-muted d-block" style="line-height: 1;">${eta.closest_stop}</small>`;
                document.getElementById('etaDistance').textContent = `--`;
            } else if (eta.bus_status === 'Approaching') {
                document.getElementById('etaTime').innerHTML = `<span class="text-warning fw-bold" style="font-size: 1.2rem;">Approaching</span><br><small class="text-muted d-block" style="line-height: 1;">${eta.closest_stop}</small>`;
                document.getElementById('etaDistance').textContent = `${eta.remaining_distance_km} km`;
            } else {
                document.getElementById('etaTime').innerHTML = `${eta.eta_minutes} min`;
                document.getElementById('etaDistance').textContent = `${eta.remaining_distance_km} km`;
            }
            document.getElementById('etaStops').textContent = eta.stops_remaining;
        }
    } catch (e) {
        console.error('ETA update error:', e);
    }
}


async function updateMapLocation(serviceNo) {
    try {
        const res = await fetch(`${API_BASE}/api/live/${serviceNo}?t=${Date.now()}`);
        if (!res.ok) {
            const updEl = document.getElementById("updatedValue");
            if (updEl) updEl.innerHTML = `<i class="bi bi-clock-history"></i> Status: Waiting for driver...`;
            return;
        }

        const liveData = await res.json();
        liveData.service_no = serviceNo;
        handleLiveUpdate(liveData);

        // Update stops panel distances
        updateTrackingStopsDistances(parseFloat(liveData.lat), parseFloat(liveData.lng));

    } catch (err) {
        console.error("Tracking Error:", err);
    }
}

function updateTimelineBusPosition(currentLat, currentLng) {
    if (currentRouteStops.length < 2) return;

    let minDistance = Infinity;
    let closestIndex = 0;

    for (let i = 0; i < currentRouteStops.length; i++) {
        let d = getDistance(currentLat, currentLng, currentRouteStops[i].lat, currentRouteStops[i].lng);
        if (d < minDistance) {
            minDistance = d;
            closestIndex = i;
        }
    }

    // Determine the precise physical segment
    let segmentStartIndex = 0;
    let segmentEndIndex = 1;

    if (closestIndex === 0) {
        segmentStartIndex = 0;
        segmentEndIndex = 1;
    } else if (closestIndex === currentRouteStops.length - 1) {
        segmentStartIndex = currentRouteStops.length - 2;
        segmentEndIndex = currentRouteStops.length - 1;
    } else {
        let distPrev = getDistance(currentLat, currentLng, currentRouteStops[closestIndex - 1].lat, currentRouteStops[closestIndex - 1].lng);
        let distNext = getDistance(currentLat, currentLng, currentRouteStops[closestIndex + 1].lat, currentRouteStops[closestIndex + 1].lng);
        if (distPrev < distNext) {
            segmentStartIndex = closestIndex - 1;
            segmentEndIndex = closestIndex;
        } else {
            segmentStartIndex = closestIndex;
            segmentEndIndex = closestIndex + 1;
        }
    }

    let startStop = currentRouteStops[segmentStartIndex];
    let endStop = currentRouteStops[segmentEndIndex];

    let distToStart = getDistance(currentLat, currentLng, startStop.lat, startStop.lng);
    let distToEnd = getDistance(currentLat, currentLng, endStop.lat, endStop.lng);

    // Calculate real-time continuous progress ratio based strictly on GPS mathematically
    let progress = Math.max(0, Math.min(1, distToStart / (distToStart + distToEnd)));

    // Lock perfectly onto the junction if the buses physical proximity is < 0.3km
    // This ensures the icon isn't floating "between" stops while actually parked at a stop
    if (distToStart < 0.3) {
        progress = 0;
    } else if (distToEnd < 0.3) {
        progress = 1;
    }

    const blocksCount = currentRouteStops.length - 1;
    const basePercentagePerBlock = 100 / blocksCount;

    // Bus icon precisely tracks physical map movement without artificial animations
    const currentProgressPercent = (segmentStartIndex * basePercentagePerBlock) + (progress * basePercentagePerBlock);
    const busTrackerIcon = document.getElementById('busTrackerIcon');
    if (busTrackerIcon) {
        busTrackerIcon.style.transition = 'none'; // strictly driven by gps coordinates in real-time
        busTrackerIcon.style.top = `calc(${currentProgressPercent}% - 25px)`;
    }

    // We reached a node if we physically start the segment, or if we are touching the end stop
    let reachedIndex = segmentStartIndex;
    if (minDistance < 0.3 && closestIndex === segmentEndIndex) {
        reachedIndex = segmentEndIndex;
    }

    // Keep the timeline moving forward, don't jump backward purely due to GPS bounce
    lastReachedStopIndex = Math.max(lastReachedStopIndex, reachedIndex);

    // Style the timeline junction nodes based on reach status
    for (let i = 0; i < currentRouteStops.length; i++) {
        const stopEl = document.getElementById(`stop-${i}`);
        if (!stopEl) continue;
        const node = stopEl.querySelector('.stop-node');
        if (node) {
            if (i <= lastReachedStopIndex) {
                node.style.background = '#00A859';
                node.style.borderColor = '#00A859';
                if (i === lastReachedStopIndex) {
                    node.style.boxShadow = '0 0 0 4px rgba(0, 168, 89, 0.2)';
                } else {
                    node.style.boxShadow = 'none';
                }
            } else {
                node.style.background = '#fff';
                node.style.borderColor = '#ccc';
                node.style.boxShadow = 'none';
            }
        }
    }
}


// ═══════════════════════════════════════════════════════
// 🎟️ TICKET SEARCH (FROM - TO)
// ═══════════════════════════════════════════════════════

function initTicketSearch() {
    const ticketForm = document.getElementById("ticketForm");

    ticketForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const from = document.getElementById("ticketFrom").value.trim();
        const to = document.getElementById("ticketTo").value.trim();
        const service = document.getElementById("ticketService").value;

        const resultBox = document.getElementById("ticketResult");
        resultBox.innerHTML = getSkeletonHTML(3);

        try {
            let url = `${API_BASE}/api/search?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`;
            if (service) url += `&service=${encodeURIComponent(service)}`;

            const response = await fetch(url);
            if (!response.ok) { resultBox.innerHTML = ''; showToast("Failed to fetch tickets", "error"); return; }

            const data = await response.json();

            if (!Array.isArray(data) || data.length === 0) {
                resultBox.innerHTML = `
                    <div class="text-center p-5 bg-white rounded-3 shadow-sm border border-light mt-3 fade-in">
                        <i class="bi bi-compass text-muted" style="font-size: 3.5rem; opacity: 0.3;"></i>
                        <h6 class="mt-3 text-dark fw-bold">No buses found</h6>
                        <p class="text-muted small">Try selecting different stops or removing the service filter.</p>
                    </div>
                `;
                showToast("No buses found", "warning");
                return;
            }

            let html = "";
            data.forEach(bus => {
                html += `
                    <div class="bus-card fade-in">
                        <div class="bus-header">
                            <span class="service-no">${bus.service_no}</span>
                            <span class="bus-type">${bus.service_type}</span>
                        </div>
                        <div class="route-info">
                            <i class="bi bi-arrow-right-circle-fill text-primary"></i> ${bus.route_name}
                        </div>
                        <div class="d-flex justify-content-between align-items-center mt-2">
                             <div class="vehicle-info">
                                <i class="bi bi-bus-front"></i> ${bus.vehicle_no}
                            </div>
                            <span class="badge bg-success" style="font-size: 0.9rem;">₹ ${bus.ticket_price}</span>
                        </div>
                    </div>
                `;
            });
            resultBox.innerHTML = html;

        } catch (error) {
            console.error(error);
            resultBox.innerHTML = '';
            showToast("Backend Connection Error", "error");
        }
    });
}


// ═══════════════════════════════════════════════════════
// 🕒 TIMETABLE SEARCH
// ═══════════════════════════════════════════════════════

function initTimetableSearch() {
    const timetableForm = document.getElementById("timetableForm");

    timetableForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const from = document.getElementById("timetableFrom").value.trim();
        const to = document.getElementById("timetableTo").value.trim();
        const resultBox = document.getElementById("timetableResult");
        resultBox.innerHTML = getSkeletonHTML(2);

        try {
            const url = `${API_BASE}/api/timetable?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`;
            const response = await fetch(url);
            if (!response.ok) { resultBox.innerHTML = ''; showToast("Failed to fetch timetable", "error"); return; }

            const data = await response.json();
            if (!Array.isArray(data) || data.length === 0) { resultBox.innerHTML = ''; showToast("No timetable found", "warning"); return; }

            let html = "";
            data.forEach(t => {
                html += `
                    <div class="bus-card fade-in" style="border-left-color: #333;">
                        <div class="bus-header">
                            <span class="service-no" style="color: #333;">${t.service_no}</span>
                            <span class="bus-type" style="background: #eee; color: #333;">
                                <i class="bi bi-clock"></i> ${t.arrival_time}
                            </span>
                        </div>
                        <div class="vehicle-info">Expected Arrival at ${from}</div>
                    </div>
                `;
            });
            resultBox.innerHTML = html;
        } catch (error) {
            console.error(error);
            resultBox.innerHTML = '';
            showToast("Backend Connection Error", "error");
        }
    });
}


// ═══════════════════════════════════════════════════════
// 🛣️ VIEW ALL ROUTES
// ═══════════════════════════════════════════════════════

function initRoutesView() {
    const viewRoutesBtn = document.getElementById("viewRoutesBtn");
    const routesResult = document.getElementById("routesResult");

    viewRoutesBtn.addEventListener("click", async () => {
        if (routesResult.style.display === "block") {
            routesResult.style.display = "none";
            viewRoutesBtn.textContent = "Load All Routes";
            return;
        }

        routesResult.innerHTML = getSkeletonHTML(3);
        routesResult.style.display = "block";
        viewRoutesBtn.innerHTML = "<i class='bi bi-eye-slash'></i> Hide Routes";

        try {
            const response = await fetch(`${API_BASE}/api/routes`);
            if (!response.ok) { routesResult.innerHTML = ''; showToast("Failed to load routes", "error"); return; }

            const data = await response.json();
            if (!Array.isArray(data) || data.length === 0) { routesResult.innerHTML = ''; showToast("No routes found", "warning"); return; }

            let html = "";
            data.forEach(r => {
                html += `
                    <div class="bus-card fade-in" style="border-left-color: #007bff;">
                        <div class="bus-header">
                            <span class="service-no" style="font-size: 1rem; color: #007bff;">${r.route_name}</span>
                        </div>
                        <div class="route-info text-muted small">
                            ${r.from} <i class="bi bi-arrow-right"></i> ${r.to}
                        </div>
                    </div>
                `;
            });
            routesResult.innerHTML = html;
        } catch (error) {
            console.error(error);
            routesResult.innerHTML = '';
            showToast("Error fetching routes", "error");
        }
    });
}


// ═══════════════════════════════════════════════════════
// 🔍 AUTOCOMPLETE STATIONS
// ═══════════════════════════════════════════════════════

async function loadStationsForAutocomplete() {
    try {
        const response = await fetch(`${API_BASE}/api/stations`);
        const stations = await response.json();
        const datalist = document.getElementById("stationList");
        datalist.innerHTML = "";
        stations.forEach(station => {
            const option = document.createElement("option");
            option.value = station;
            datalist.appendChild(option);
        });
    } catch (error) {
        console.error("Failed to load stations for autocomplete", error);
    }
}


// ═══════════════════════════════════════════════════════
// 🚏 BUS STOP LOCATOR — Visakhapatnam Map
// ═══════════════════════════════════════════════════════

const ROUTE_COLORS = {
    '28A': '#1a73e8',
    '6K': '#e8300a',
    '400K': '#8e24aa',
};

const ROUTE_META = {
    '28A': { label: '28A', route: 'Anakapalle → Steel Plant' },
    '6K': { label: '6K', route: 'NAD Junction → Pendurthi' },
    '400K': { label: '400K', route: 'Rushikonda → Bheemili' },
};

let stopsMap = null;
let stopsLayerGroups = {};
let userLocationMarker = null;

function makeStopIcon(color, isTerminal) {
    const size = isTerminal ? 18 : 13;
    const border = isTerminal ? 3 : 2;
    return L.divIcon({
        className: '',
        html: `<div style="
            width:${size}px; height:${size}px;
            background:${color};
            border:${border}px solid white;
            border-radius:50%;
            box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        "></div>`,
        iconAnchor: [size / 2, size / 2],
        popupAnchor: [0, -(size / 2 + 4)]
    });
}

async function initStopsMap() {
    const mapEl = document.getElementById('stopsMap');
    if (!mapEl) return;

    stopsMap = L.map('stopsMap', { zoomControl: true }).setView([17.6868, 83.2185], 13);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(stopsMap);

    // Load stops for all known services + dynamically from API
    await loadDynamicRoutes();

    renderStopListAll();

    const filterEl = document.getElementById('stopsRouteFilter');
    if (filterEl) {
        filterEl.addEventListener('change', () => {
            applyRouteFilter(filterEl.value);
        });
    }
}

async function loadDynamicRoutes() {
    try {
        // Fetch all routes from API to dynamically populate
        const res = await fetch(`${API_BASE}/api/routes`);
        if (!res.ok) return;
        const routes = await res.json();

        // Update filter dropdown
        const filterEl = document.getElementById('stopsRouteFilter');
        if (filterEl) {
            filterEl.innerHTML = '<option value="all">All Routes</option>';
            
            // Also fetch services to match
            const svcRes = await fetch(`${API_BASE}/api/search?from=&to=`);
            const services = svcRes.ok ? await svcRes.json() : [];

            for (const route of routes) {
                // Find service_no for this route
                const svc = services.find(s => s.route_name === route.route_name);
                const serviceNo = svc ? svc.service_no : null;

                if (serviceNo) {
                    filterEl.innerHTML += `<option value="${serviceNo}">${serviceNo} — ${route.route_name}</option>`;

                    // Set dynamic color/meta if not predefined
                    if (!ROUTE_COLORS[serviceNo]) {
                        const hue = (Object.keys(ROUTE_COLORS).length * 137) % 360;
                        ROUTE_COLORS[serviceNo] = `hsl(${hue}, 70%, 50%)`;
                    }
                    if (!ROUTE_META[serviceNo]) {
                        ROUTE_META[serviceNo] = { label: serviceNo, route: route.route_name };
                    }

                    await loadStopsLayer(serviceNo);
                } else {
                    // fallback: use route name
                    filterEl.innerHTML += `<option value="${route.route_name}">${route.route_name}</option>`;
                }
            }
        }

        // Also load predefined services in case they weren't in the API response
        const predefined = Object.keys(ROUTE_META);
        for (const svc of predefined) {
            if (!stopsLayerGroups[svc]) {
                await loadStopsLayer(svc);
            }
        }
    } catch (e) {
        console.error('Error loading dynamic routes:', e);
        // Fallback: load predefined only
        for (const svc of Object.keys(ROUTE_META)) {
            if (!stopsLayerGroups[svc]) await loadStopsLayer(svc);
        }
    }
}

async function loadStopsLayer(serviceNo) {
    try {
        const res = await fetch(`${API_BASE}/api/route_details/${serviceNo}`);
        if (!res.ok) return;

        const stops = await res.json();
        if (!stops || stops.length === 0) return;

        const color = ROUTE_COLORS[serviceNo] || '#00A859';
        const meta = ROUTE_META[serviceNo] || { label: serviceNo, route: '' };

        const markers = [];
        stops.forEach((stop, idx) => {
            const isTerminal = (idx === 0 || idx === stops.length - 1);
            const icon = makeStopIcon(color, isTerminal);

            const popupHTML = `
                <div class="stop-popup">
                    <div class="stop-popup-name">🚏 ${stop.name}</div>
                    <div class="stop-popup-route">${meta.route}</div>
                    <span class="stop-popup-badge" style="background:${color};">${meta.label}</span>
                    ${isTerminal ? ' <span class="stop-popup-badge" style="background:#FF5E00; margin-left:4px;">Terminal</span>' : ''}
                </div>
            `;

            const marker = L.marker([stop.lat, stop.lng], { icon })
                .bindPopup(popupHTML, { maxWidth: 220 });

            markers.push({ marker, stop, isTerminal });
        });

        const latlngs = stops.map(s => [s.lat, s.lng]);
        const polyline = L.polyline(latlngs, { color, weight: 3, opacity: 0.7, dashArray: '6, 4' });

        const group = L.layerGroup();
        group.addLayer(polyline);
        markers.forEach(({ marker }) => group.addLayer(marker));

        stopsLayerGroups[serviceNo] = { group, markers, stops, color, meta };
        group.addTo(stopsMap);

    } catch (err) {
        console.error(`Failed to load stops for ${serviceNo}:`, err);
    }
}

function applyRouteFilter(selected) {
    Object.entries(stopsLayerGroups).forEach(([svc, data]) => {
        if (selected === 'all' || selected === svc) {
            stopsMap.addLayer(data.group);
        } else {
            stopsMap.removeLayer(data.group);
        }
    });

    if (selected === 'all') {
        renderStopListAll();
        stopsMap.setView([17.6868, 83.2185], 13);
    } else {
        renderStopListSingle(selected);
        const data = stopsLayerGroups[selected];
        if (data && data.stops.length > 0) {
            const latlngs = data.stops.map(s => [s.lat, s.lng]);
            stopsMap.fitBounds(latlngs, { padding: [40, 40] });
        }
    }
}

function renderStopListAll() {
    const panel = document.getElementById('stopListPanel');
    if (!panel) return;

    let html = '';
    Object.entries(stopsLayerGroups).forEach(([svc, data]) => {
        html += `
            <div class="d-flex align-items-center gap-2 mb-2 mt-3">
                <div class="legend-dot" style="background:${data.color};"></div>
                <span class="fw-bold small" style="color:${data.color};">${data.meta.label} — ${data.meta.route}</span>
            </div>
        `;
        data.stops.forEach((stop, idx) => {
            const isTerminal = (idx === 0 || idx === data.stops.length - 1);
            html += buildStopListItem(stop, svc, data.color, isTerminal, idx);
        });
    });

    panel.innerHTML = html || '<p class="text-muted text-center small">No stops loaded</p>';
}

function renderStopListSingle(serviceNo) {
    const panel = document.getElementById('stopListPanel');
    if (!panel) return;

    const data = stopsLayerGroups[serviceNo];
    if (!data) { panel.innerHTML = '<p class="text-muted text-center small">No stops found</p>'; return; }

    let html = `
        <div class="d-flex align-items-center gap-2 mb-3">
            <div class="legend-dot" style="background:${data.color};"></div>
            <span class="fw-bold small" style="color:${data.color};">${data.meta.route}</span>
        </div>
    `;

    data.stops.forEach((stop, idx) => {
        const isTerminal = (idx === 0 || idx === data.stops.length - 1);
        html += buildStopListItem(stop, serviceNo, data.color, isTerminal, idx);
    });

    panel.innerHTML = html;
}

function buildStopListItem(stop, serviceNo, color, isTerminal, idx) {
    const terminalClass = isTerminal ? 'terminal' : '';
    const badge = isTerminal ? 'Terminal' : `Stop ${idx + 1}`;
    return `
        <div class="stop-list-item ${terminalClass}"
             onclick="panToStop('${serviceNo}', ${idx})"
             title="Tap to locate on map">
            <div class="stop-route-dot" style="background:${color};"></div>
            <div class="stop-item-info">
                <div class="stop-item-name">${stop.name}</div>
                <div class="stop-item-route">${ROUTE_META[serviceNo]?.route || ''}</div>
            </div>
            <span class="stop-item-badge" style="background:${color};">${badge}</span>
        </div>
    `;
}

window.panToStop = function (serviceNo, stopIdx) {
    const data = stopsLayerGroups[serviceNo];
    if (!data) return;
    const stop = data.stops[stopIdx];
    if (!stop) return;
    stopsMap.setView([stop.lat, stop.lng], 16, { animate: true });
    const markerEntry = data.markers[stopIdx];
    if (markerEntry) markerEntry.marker.openPopup();
    document.getElementById('stopsMap').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
};

window.locateUserOnStopsMap = function () {
    if (!navigator.geolocation) {
        showToast('Geolocation is not supported by your browser', 'error');
        return;
    }

    const btn = document.getElementById('locateMeBtn');
    btn.classList.add('locating');
    btn.innerHTML = '<i class="bi bi-hourglass-split spinning"></i> Locating...';

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const { latitude, longitude } = pos.coords;
            if (userLocationMarker) stopsMap.removeLayer(userLocationMarker);
            const userIcon = L.divIcon({ className: 'user-location-marker', html: '', iconSize: [18, 18], iconAnchor: [9, 9] });
            userLocationMarker = L.marker([latitude, longitude], { icon: userIcon })
                .addTo(stopsMap).bindPopup('<b>📍 You are here</b>').openPopup();
            stopsMap.setView([latitude, longitude], 15, { animate: true });
            btn.classList.remove('locating');
            btn.innerHTML = '<i class="bi bi-crosshair"></i> Locate Me';
            showToast('Location found! 📍', 'success');
        },
        (err) => {
            btn.classList.remove('locating');
            btn.innerHTML = '<i class="bi bi-crosshair"></i> Locate Me';
            showToast('Could not get your location', 'error');
            console.error('Geolocation error:', err);
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
};