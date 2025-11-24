// Import Leaflet library
const L = window.L

// API Configuration
const API_BASE_URL = window.location.origin

// Global state
let map
let stops = []
const routes = []
let currentRoutes = []
let routeLayers = []

// Initialize map
function initMap() {
  map = L.map("map").setView([47.322, 5.0415], 13) // Dijon coordinates

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map)
}

// Load stops from API
async function loadStops() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/stops?limit=1000`)
    const data = await response.json()
    stops = data.stops

    // Populate select dropdowns
    populateStopSelects()

    console.log(`Loaded ${stops.length} stops`)
  } catch (error) {
    console.error("Error loading stops:", error)
    showMessage("Erreur lors du chargement des arrêts", "error")
  }
}

// Populate stop select dropdowns
function populateStopSelects() {
  const departureSelect = document.getElementById("departureSelect")
  const arrivalSelect = document.getElementById("arrivalSelect")

  stops.forEach((stop) => {
    const option1 = document.createElement("option")
    option1.value = stop.stop_id
    option1.textContent = stop.stop_name
    departureSelect.appendChild(option1)

    const option2 = document.createElement("option")
    option2.value = stop.stop_id
    option2.textContent = stop.stop_name
    arrivalSelect.appendChild(option2)
  })

  // Show selects, hide inputs
  document.getElementById("departure").style.display = "none"
  document.getElementById("arrival").style.display = "none"
  departureSelect.style.display = "block"
  arrivalSelect.style.display = "block"
}

// Search for route
async function searchRoute() {
  const departureId = document.getElementById("departureSelect").value
  const arrivalId = document.getElementById("arrivalSelect").value
  const alternatives = Number.parseInt(document.getElementById("alternatives").value)

  if (!departureId || !arrivalId) {
    showMessage("Veuillez sélectionner un arrêt de départ et d'arrivée", "error")
    return
  }

  if (departureId === arrivalId) {
    showMessage("Le départ et l'arrivée doivent être différents", "error")
    return
  }

  // Show loading
  showMessage("Recherche en cours...", "loading")
  document.getElementById("searchBtn").disabled = true

  try {
    const includeAlternatives = alternatives > 1
    const response = await fetch(`${API_BASE_URL}/api/v1/route`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        departure: departureId,
        arrival: arrivalId,
        include_alternatives: includeAlternatives,
        max_alternatives: alternatives,
      }),
    })

    if (!response.ok) {
      throw new Error("Aucun itinéraire trouvé")
    }

    const data = await response.json()
    if (data.routes) {
      // Multiple routes (AlternativeRoutesResponse)
      currentRoutes = data.routes
    } else {
      // Single route (RouteResponse)
      currentRoutes = [data]
    }

    displayRoutes(currentRoutes)
    showMessage(`${currentRoutes.length} itinéraire(s) trouvé(s)`, "success")

    // Display first route on map
    if (currentRoutes.length > 0) {
      displayRouteOnMap(currentRoutes[0], 0)
    }
  } catch (error) {
    console.error("Error searching route:", error)
    showMessage(error.message || "Erreur lors de la recherche", "error")
  } finally {
    document.getElementById("searchBtn").disabled = false
  }
}

// Display routes in the list
function displayRoutes(routes) {
  const routesList = document.getElementById("routesList")
  const resultsSection = document.getElementById("results")

  routesList.innerHTML = ""

  routes.forEach((route, index) => {
    const routeCard = document.createElement("div")
    routeCard.className = "route-card"
    if (index === 0) routeCard.classList.add("selected")

    routeCard.innerHTML = `
            <div class="route-header">
                <strong>Itinéraire</strong>
                <div class="route-stats">
                    <span class="stat">🚏 ${route.num_stops} arrêts</span>
                    <span class="stat">🔄 ${route.num_transfers} correspondances</span>
                </div>
            </div>
            <div class="stop-list">
                ${route.stops
                  .map(
                    (stop, idx) => `
                    <div class="stop-item">
                        <div class="stop-marker ${stop.is_transfer ? "transfer" : ""}">
                            ${idx + 1}
                        </div>
                        <div class="stop-info">
                            <div class="stop-name">${stop.stop_name}</div>
                            ${stop.route_to_next ? `<div class="stop-route">Ligne: ${stop.route_to_next}</div>` : ""}
                        </div>
                    </div>
                `,
                  )
                  .join("")}
            </div>
        `

    routeCard.addEventListener("click", () => {
      document.querySelectorAll(".route-card").forEach((card) => {
        card.classList.remove("selected")
      })
      routeCard.classList.add("selected")
      displayRouteOnMap(route, index)
    })

    routesList.appendChild(routeCard)
  })

  resultsSection.style.display = "block"
}

// Display route on map
function displayRouteOnMap(route, routeIndex) {
  // Clear existing layers
  routeLayers.forEach((layer) => map.removeLayer(layer))
  routeLayers = []

  // Create bounds
  const bounds = []

  // Add markers for each stop
  route.stops.forEach((stop, index) => {
    const isFirst = index === 0
    const isLast = index === route.stops.length - 1
    const isTransfer = stop.is_transfer

    let markerColor = "#667eea"
    if (isFirst) markerColor = "#10b981"
    else if (isLast) markerColor = "#ef4444"
    else if (isTransfer) markerColor = "#f59e0b"

    const marker = L.circleMarker([stop.lat, stop.lon], {
      radius: isFirst || isLast ? 10 : 6,
      fillColor: markerColor,
      color: "white",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9,
    }).addTo(map)

    marker.bindPopup(`
            <strong>${stop.stop_name}</strong><br>
            ${isFirst ? "🟢 Départ" : isLast ? "🔴 Arrivée" : isTransfer ? "🔄 Correspondance" : `Arrêt ${index + 1}`}
        `)

    routeLayers.push(marker)
    bounds.push([stop.lat, stop.lon])
  })

  // Draw lines between stops
  for (let i = 0; i < route.stops.length - 1; i++) {
    const stop1 = route.stops[i]
    const stop2 = route.stops[i + 1]

    const lineColor = stop2.is_transfer ? "#f59e0b" : "#667eea"
    const lineStyle = stop2.is_transfer ? "dashed" : "solid"

    const polyline = L.polyline(
      [
        [stop1.lat, stop1.lon],
        [stop2.lat, stop2.lon],
      ],
      {
        color: lineColor,
        weight: 4,
        opacity: 0.7,
        dashArray: lineStyle === "dashed" ? "10, 10" : null,
      },
    ).addTo(map)

    routeLayers.push(polyline)
  }

  // Fit map to bounds
  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [50, 50] })
  }
}

// Show message
function showMessage(message, type) {
  const messageDiv = document.getElementById("message")

  if (type === "loading") {
    messageDiv.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div>${message}</div>
            </div>
        `
  } else if (type === "error") {
    messageDiv.innerHTML = `<div class="error">${message}</div>`
  } else if (type === "success") {
    messageDiv.innerHTML = `<div class="success">${message}</div>`
  } else {
    messageDiv.innerHTML = ""
  }
}

// Clear form
function clearForm() {
  document.getElementById("departureSelect").value = ""
  document.getElementById("arrivalSelect").value = ""
  document.getElementById("alternatives").value = "3"
  document.getElementById("results").style.display = "none"
  document.getElementById("message").innerHTML = ""

  // Clear map
  routeLayers.forEach((layer) => map.removeLayer(layer))
  routeLayers = []

  // Reset map view
  map.setView([47.322, 5.0415], 13)
}

function getGradioUrl() {
  // If localhost, use local Gradio URL
  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    return window.location.origin + "/gradio";
  }
  // We use huffingface space URL in production
  return "https://tabodino-divia-transport-planner.hf.space/proxy/gradio";
}

// Initialize Chatbot Widget
function initChatbotWidget() {
  const btn = document.createElement('button');
  btn.id = 'chatbot-toggle';
  btn.style = `
    position: fixed; bottom: 32px; right: 32px; z-index: 10001; width:62px; height:62px; 
    border-radius:50%; background:linear-gradient(135deg,#6366f1 60%,#312e81 100%);
    color:#fff; border:none; box-shadow:0 2px 16px rgba(50,50,150,.22); font-size:32px;
    display:flex; align-items:center; justify-content:center; cursor:pointer;
  `;
  btn.innerHTML = '<i class="chatbot-icon"></i>';

  // Chatbot Window (hidden by default)
  const container = document.createElement('div');
  container.id = 'chatbot-container';
  container.style = `
    position: fixed; bottom: 32px; right: 32px; width: 400px; height: 560px; background: #fff;
    border-radius: 21px; box-shadow: 0 8px 36px rgba(34,34,78,0.32); z-index: 10000;
    border: 1px solid #ddd; overflow: hidden; display: none;
  `;

  // Close button "X"
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '&times;';
  closeBtn.style = `
    position: absolute; top: 8px; right: 12px; z-index: 10002; background: transparent;
    border: none; font-size: 2rem; color: #444; cursor: pointer;
  `;

  // Gradio Component (Absolute url needed on production)
  const gradio = document.createElement('iframe');
  gradio.setAttribute('src', getGradioUrl());
  gradio.style = 'width:100%; height:100%; border:none; display:block;';

  // Assemble
  container.appendChild(closeBtn);
  container.appendChild(gradio);
  document.body.appendChild(btn);
  document.body.appendChild(container);

  // Open/Close logic
  btn.addEventListener('click', () => {
    container.style.display = 'block';
    btn.style.display = 'none';
  });
  closeBtn.addEventListener('click', () => {
    container.style.display = 'none';
    btn.style.display = 'flex';
  });

  // Close on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === "Escape" && container.style.display === "block") {
      container.style.display = 'none';
      btn.style.display = 'flex';
    }
  });
}


// Event listeners
document.getElementById("searchBtn").addEventListener("click", searchRoute)
document.getElementById("clearBtn").addEventListener("click", clearForm)

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initMap()
  loadStops()
  initChatbotWidget()
})
