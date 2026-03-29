const API_BASE = ""; // Relative path for same-domain deployment
let trackingMap = null;
let trackingMarker = null;
let trackingInterval = null;
let routeRoadPath = [];   // Stores the OSRM road-following coordinates for the current route

document.addEventListener("DOMContentLoaded", () => {
    initServiceVehicleSearch();
    initTicketSearch();
    initTimetableSearch();
    initRoutesView();
    loadStationsForAutocomplete();

    setHumanGreeting();

    // Version Indicator
    const brand = document.querySelector('.navbar-brand');
    if (brand) brand.innerHTML += ' <span style="font-size:0.5em; opacity: 0.5; margin-left: 8px;">v6.0</span>';
    console.log("APP VERSION: 6.0 PROFESSIONAL UI LOADED");
});

// Toast System
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

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOutRight 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Dynamic Human Greeting
function setHumanGreeting() {
    const header = document.getElementById("greetingHeader");
    if (!header) return;
    const hour = new Date().getHours();
    let greeting = "Good Evening!";
    if (hour < 12) greeting = "Good Morning!";
    else if (hour < 17) greeting = "Good Afternoon!";
    header.innerText = greeting;
}

// Skeleton Generator
function getSkeletonHTML(count = 1) {
    let html = '';
    for(let i=0; i<count; i++) {
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


// ---------------------------
// SERVICE / VEHICLE SEARCH
// ---------------------------

// ---------------------------
// SERVICE / VEHICLE SEARCH
// ---------------------------
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

        // Clear previous interval if any
        if (trackingInterval) clearInterval(trackingInterval);

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

let currentRouteStops = []; // Store stops globally for logic processing

// Toggle View Helper
window.toggleTrackingView = function(view) {
    if (view === 'timeline') {
        document.getElementById('timelineContainer').style.display = 'block';
        document.getElementById('mapContainer').style.display = 'none';
    } else {
        document.getElementById('timelineContainer').style.display = 'none';
        document.getElementById('mapContainer').style.display = 'block';
        if (trackingMap) {
            trackingMap.invalidateSize(); // Fix leafet rendering issue when unhidden
        }
    }
};

async function startLiveMap(serviceNo) {
    // 0. Reset UI
    document.getElementById('timelineLoading').style.display = 'block';
    document.getElementById('routeTimelineGrid').style.display = 'none';
    currentRouteStops = [];

    // 1. Initialize Map Container immediately
    if (trackingMap) {
        trackingMap.off();
        trackingMap.remove();
        trackingMap = null;
    }
    trackingMarker = null; // CRITICAL: reset so marker is re-added to the NEW map

    // Default center (Vizag) before we get data
    trackingMap = L.map('map').setView([17.6868, 83.2185], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(trackingMap);

    // 2. Fetch and Plot Route (Map & Timeline)
    await drawRouteOnMap(serviceNo);

    // 3. Initial Live Location Check
    await updateMapLocation(serviceNo);

    // 4. Start Polling
    trackingInterval = setInterval(() => {
        updateMapLocation(serviceNo);
    }, 3000);
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
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// ---------------------------
// 🛣️ OSRM ROAD-NETWORK HELPER
// ---------------------------

/**
 * Fetches a road-following path from the public OSRM demo server.
 * @param {Array} waypoints  Array of [lat, lng] pairs (stop coordinates)
 * @returns {Array|null}     Array of [lat, lng] for the road path, or null on failure
 */
async function fetchOsrmRoute(waypoints) {
    try {
        const coordStr = waypoints.map(([lat, lng]) => `${lng},${lat}`).join(';');
        const url = `https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`;

        const res = await fetch(url);
        if (!res.ok) return null;

        const data = await res.json();
        if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) return null;

        const roadCoords = data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng]);
        return roadCoords;
    } catch (err) {
        return null;
    }
}

async function drawRouteOnMap(serviceNo) {
    try {
        const res = await fetch(`${API_BASE}/api/route_details/${serviceNo}`);
        if (!res.ok) return;

        const stops = await res.json();
        if (!stops || stops.length === 0) return;

        currentRouteStops = stops; // Save for timeline calc

        // -----------------------------
        // Populate Linear Timeline UI
        // -----------------------------
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

        // -----------------------------
        // Render Geographic Map
        // -----------------------------
        const stopCoords = stops.map(s => [s.lat, s.lng]);
        const roadPath = await fetchOsrmRoute(stopCoords);

        if (roadPath && roadPath.length > 1) {
            routeRoadPath = roadPath;
            L.polyline(roadPath, { color: '#1a73e8', weight: 5, opacity: 0.85, lineJoin: 'round' }).addTo(trackingMap);
        } else {
            routeRoadPath = stopCoords;
            L.polyline(stopCoords, { color: 'blue', weight: 4, opacity: 0.7, dashArray: '8, 8' }).addTo(trackingMap);
        }

        // --- Add Stop Markers ---
        const smallBusIcon = L.icon({
            iconUrl: 'https://img.icons8.com/m_outlined/200/bus.png', // Small simple bus icon
            iconSize: [20, 20],
            iconAnchor: [10, 10], // Center of 20x20
            popupAnchor: [0, -10]
        });

        // Use standard blue marker for start and end terminals
        const terminalIcon = new L.Icon.Default();

        stops.forEach((stop, i) => {
            const isTerminal = (i === 0 || i === stops.length - 1);
            
            if (isTerminal) {
                // Pin marker for start and end stops
                L.marker([stop.lat, stop.lng], { icon: terminalIcon })
                 .addTo(trackingMap)
                 .bindPopup(`🚏 <b>${stop.name}</b> (Terminal)`);
            } else {
                // Small bus icon for intermediate stops
                L.marker([stop.lat, stop.lng], { icon: smallBusIcon })
                 .addTo(trackingMap)
                 .bindPopup(`🚏 <b>${stop.name}</b>`);
            }
        });

        trackingMap.fitBounds(roadPath && roadPath.length > 1 ? roadPath : stopCoords);

    } catch (err) {
        console.error('Error drawing route:', err);
    }
}

async function updateMapLocation(serviceNo) {
    try {
        const res = await fetch(`${API_BASE}/api/live/${serviceNo}?t=${Date.now()}`);
        if (!res.ok) {
            document.getElementById("updatedValue").innerHTML = `<i class="bi bi-clock-history"></i> Status: Waiting for driver...`;
            return;
        }

        const liveData = await res.json();

        // Update Text Info
        document.getElementById("speedValue").innerHTML = `<i class="bi bi-speedometer2"></i> ${liveData.speed} km/h`;
        document.getElementById("locValue").innerHTML = `<i class="bi bi-geo-alt"></i> ${liveData.lat.toFixed(4)}, ${liveData.lng.toFixed(4)}`;
        document.getElementById("updatedValue").innerHTML = `<i class="bi bi-clock-history"></i> Updated: ${liveData.updated_at.split(' ')[1]}`;

        const lat = liveData.lat;
        const lng = liveData.lng;

        // --------------------------------
        // Update Geographical Map Marker
        // --------------------------------
        if (!trackingMarker) {
            trackingMarker = L.marker([lat, lng], {icon: busIcon}).addTo(trackingMap)
                .bindPopup(`<b>${serviceNo}</b><br>Speed: ${liveData.speed} km/h`)
                .openPopup();
            trackingMap.setView([lat, lng], 15);
        } else {
            trackingMarker.setLatLng([lat, lng]);
            trackingMarker.setPopupContent(`<b>${serviceNo}</b><br>Speed: ${liveData.speed} km/h`);
            // trackingMap.panTo([lat, lng]); // Optional: uncomment if you want map to force pan
        }

        // --------------------------------
        // Update Linear Timeline Progress
        // --------------------------------
        if (currentRouteStops.length > 1) {
            updateTimelineBusPosition(lat, lng);
        }

    } catch (err) {
        console.error("Tracking Error:", err);
    }
}

function updateTimelineBusPosition(currentLat, currentLng) {
    if (currentRouteStops.length < 2) return;

    // Find the closest stop to determine segment
    let minDistance = Infinity;
    let closestIndex = 0;

    for (let i = 0; i < currentRouteStops.length; i++) {
        let d = getDistance(currentLat, currentLng, currentRouteStops[i].lat, currentRouteStops[i].lng);
        if (d < minDistance) {
            minDistance = d;
            closestIndex = i;
        }
    }

    // Determine if bus is heading to next or previous stop logically
    let segmentStartIndex = closestIndex;
    let segmentEndIndex = closestIndex + 1;

    // Boundary check
    if (closestIndex === currentRouteStops.length - 1) {
        segmentStartIndex = closestIndex - 1;
        segmentEndIndex = closestIndex;
    }

    // Mathematical progression percentage between the two stops
    let startStop = currentRouteStops[segmentStartIndex];
    let endStop = currentRouteStops[segmentEndIndex];

    let distToStart = getDistance(currentLat, currentLng, startStop.lat, startStop.lng);
    let distToEnd = getDistance(currentLat, currentLng, endStop.lat, endStop.lng);
    let segmentTotalDist = getDistance(startStop.lat, startStop.lng, endStop.lat, endStop.lng);

    // Guard against 0 division if stops are identical
    if (segmentTotalDist === 0) segmentTotalDist = 0.0001; 

    // Calculate percentage (0.0 to 1.0) along the segment 
    let progress = distToStart / (distToStart + distToEnd);
    if (progress > 1) progress = 1;
    if (progress < 0) progress = 0;

    // Map the progress to literal CSS 'top' value in the timeline 
    // Each stop visually takes up standard space (80px height per stop block)
    const blocksCount = currentRouteStops.length - 1;
    const basePercentagePerBlock = 100 / blocksCount;

    const blockStartPercent = segmentStartIndex * basePercentagePerBlock;
    const currentProgressPercent = blockStartPercent + (progress * basePercentagePerBlock);

    // Apply smooth CSS transition
    document.getElementById('busTrackerIcon').style.top = `calc(${currentProgressPercent}% - 25px)`;
}


// ---------------------------
// 🎟️ TICKET SEARCH (FROM - TO)
// ---------------------------

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

            if (service) {
                url += `&service=${encodeURIComponent(service)}`;
            }

            const response = await fetch(url);
            
            if (!response.ok) {
                resultBox.innerHTML = '';
                showToast("Failed to fetch tickets", "error");
                return;
            }
            
            const data = await response.json();

            if (!Array.isArray(data) || data.length === 0) {
                resultBox.innerHTML = '';
                showToast("No buses found", "warning");
                // Beautiful empty state for no tickets
                resultBox.innerHTML = `
                    <div class="text-center p-5 bg-white rounded-3 shadow-sm border border-light mt-3 fade-in">
                        <i class="bi bi-compass text-muted" style="font-size: 3.5rem; opacity: 0.3;"></i>
                        <h6 class="mt-3 text-dark fw-bold">No buses found</h6>
                        <p class="text-muted small">Try selecting different stops or removing the service filter.</p>
                    </div>
                `;
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


// ---------------------------
// 🕒 TIMETABLE SEARCH
// ---------------------------
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
            
            if (!response.ok) {
                resultBox.innerHTML = '';
                showToast("Failed to fetch timetable", "error");
                return;
            }
            
            const data = await response.json();

            if (!Array.isArray(data) || data.length === 0) {
                resultBox.innerHTML = '';
                showToast("No timetable found for this route", "warning");
                return;
            }

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
                        <div class="vehicle-info">
                            Expected Arrival at ${from}
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


// ---------------------------
// 🛣️ VIEW ALL ROUTES
// ---------------------------
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
            
            if (!response.ok) {
                routesResult.innerHTML = '';
                showToast("Failed to load routes", "error");
                return;
            }
            
            const data = await response.json();

            if (!Array.isArray(data) || data.length === 0) {
                routesResult.innerHTML = '';
                showToast("No routes found", "warning");
                return;
            }

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


// ---------------------------
// 🔍 AUTOCOMPLETE STATIONS
// ---------------------------
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