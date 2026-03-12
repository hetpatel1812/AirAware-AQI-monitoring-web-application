
/**
 * AirAware - Live AQI Map Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    initMap();
});

function initMap() {
    // Center of India
    const map = L.map('indiaMap').setView([20.5937, 78.9629], 5);

    // Add Esri Dark Gray Canvas Tile Layer
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16
    }).addTo(map);

    // Fetch and plot data
    fetchMapData(map);
}

async function fetchMapData(map) {
    try {
        const response = await fetch('/api/map-data');
        const data = await response.json();

        if (data.cities) {
            plotCities(map, data.cities);
            updateTimestamp(data.timestamp);
        }
    } catch (error) {
        console.error('Error fetching map data:', error);
    }
}

function plotCities(map, cities) {
    cities.forEach(city => {
        if (!city.lat || !city.lng) return;

        // Determine color based on AQI
        const color = getAqiColor(city.aqi);

        // Create custom marker icon
        const icon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color: ${color}; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; color: white; font-weight: bold; font-size: 10px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">${city.aqi}</div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        // Add marker to map
        const marker = L.marker([city.lat, city.lng], { icon: icon }).addTo(map);

        // Create popup content
        const popupContent = `
            <div class="popup-header" style="background-color: ${color}">
                <span>${city.name}</span>
                <span class="material-symbols-rounded" style="font-size: 18px;">cloud</span>
            </div>
            <div class="popup-body">
                <span class="popup-aqi" style="color: ${color}">${city.aqi}</span>
                <span class="popup-category">${city.category}</span>
                <a href="/in/${city.state.replace(/\s+/g, '-').toLowerCase()}/${city.slug}" class="popup-btn">View Details</a>
            </div>
        `;

        marker.bindPopup(popupContent);
    });
}

function getAqiColor(aqi) {
    if (aqi <= 50) return '#00e400';      // Good
    if (aqi <= 100) return '#ffff00';     // Satisfactory
    if (aqi <= 200) return '#ff7e00';     // Moderate
    if (aqi <= 300) return '#ff0000';     // Poor
    if (aqi <= 400) return '#99004c';     // Very Poor
    return '#7e0023';                     // Severe
}

function updateTimestamp(timestamp) {
    const el = document.querySelector('.update-time');
    if (el) {
        el.textContent = `Last updated: ${timestamp}`;
    }
}
