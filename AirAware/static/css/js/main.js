/**
 * AirAware Dashboard - Main JavaScript
 * Handles search, charts, and dynamic updates
 */

// DOM Elements
const searchInput = document.getElementById('citySearch');
const searchResults = document.getElementById('searchResults');
let searchTimeout = null;

// ==========================================================================
// City Search
// ==========================================================================

/**
 * Initialize search functionality
 */
function initSearch() {
    if (!searchInput || !searchResults) return;

    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('focus', handleSearchFocus);

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });

    // Keyboard navigation
    searchInput.addEventListener('keydown', handleSearchKeydown);
}

/**
 * Handle search input with debounce
 */
const DEFAULT_CITIES = [
    { name: "Ahmedabad", state: "Gujarat", url: "/in/gujarat/ahmedabad-aqi" },
    { name: "Mumbai", state: "Maharashtra", url: "/in/maharashtra/mumbai-aqi" },
    { name: "Bengaluru", state: "Karnataka", url: "/in/karnataka/bengaluru-aqi" },
    { name: "Chennai", state: "Tamil Nadu", url: "/in/tamil-nadu/chennai-aqi" },
    { name: "Kolkata", state: "West Bengal", url: "/in/west-bengal/kolkata-aqi" },
    { name: "Hyderabad", state: "Telangana", url: "/in/telangana/hyderabad-aqi" },
    { name: "Pune", state: "Maharashtra", url: "/in/maharashtra/pune-aqi" }
];

/**
 * Handle search input with debounce
 */
function handleSearchInput(e) {
    const query = e.target.value.trim();

    clearTimeout(searchTimeout);

    if (query.length === 0) {
        renderDefaultSuggestions();
        return;
    }

    if (query.length < 2) {
        // searchResults.classList.remove('active'); // Don't hide, show defaults or keep previous? 
        // Better to hide if 1 char but not empty, or show defaults? 
        // Let's show defaults for empty, and nothing for 1 char to avoid noise
        if (query.length === 0) renderDefaultSuggestions();
        else searchResults.classList.remove('active');
        return;
    }

    searchTimeout = setTimeout(() => {
        performSearch(query);
    }, 300);
}

/**
 * Handle search focus
 */
function handleSearchFocus() {
    const query = searchInput.value.trim();
    if (query.length === 0) {
        renderDefaultSuggestions();
    } else if (query.length >= 2 && searchResults.innerHTML) {
        searchResults.classList.add('active');
    }
}

/**
 * Render default city suggestions
 */
function renderDefaultSuggestions() {
    renderSearchResults(DEFAULT_CITIES);
}

/**
 * Handle keyboard navigation in search
 */
function handleSearchKeydown(e) {
    const items = searchResults.querySelectorAll('.search-result-item');
    const activeItem = searchResults.querySelector('.search-result-item.active');
    let activeIndex = Array.from(items).indexOf(activeItem);

    switch (e.key) {
        case 'ArrowDown':
            e.preventDefault();
            if (activeIndex < items.length - 1) {
                items[activeIndex + 1]?.classList.add('active');
                activeItem?.classList.remove('active');
            } else if (activeIndex === -1 && items.length > 0) {
                items[0].classList.add('active');
            }
            break;

        case 'ArrowUp':
            e.preventDefault();
            if (activeIndex > 0) {
                items[activeIndex - 1]?.classList.add('active');
                activeItem?.classList.remove('active');
            }
            break;

        case 'Enter':
            e.preventDefault();
            if (activeItem) {
                window.location.href = activeItem.dataset.url;
            }
            break;

        case 'Escape':
            searchResults.classList.remove('active');
            searchInput.blur();
            break;
    }
}

/**
 * Perform search API call
 */
async function performSearch(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        renderSearchResults(data.results);
    } catch (error) {
        console.error('Search error:', error);
    }
}

/**
 * Render search results
 */
function renderSearchResults(results) {
    if (!results || results.length === 0) {
        searchResults.innerHTML = '<div class="search-result-item"><span class="search-result-city">No cities found</span></div>';
        searchResults.classList.add('active');
        return;
    }

    const html = results.map(city => `
        <div class="search-result-item" data-url="${city.url}">
            <span class="search-result-city">${city.name}</span>
            <span class="search-result-state">${city.state}</span>
        </div>
    `).join('');

    searchResults.innerHTML = html;
    searchResults.classList.add('active');

    // Add click handlers
    searchResults.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
            window.location.href = item.dataset.url;
        });
    });
}

// ==========================================================================
// AQI Chart
// ==========================================================================

/**
 * Initialize the AQI trend chart
 */
function initChart() {
    const canvas = document.getElementById('aqiChart');
    if (!canvas || !cityData || !cityData.historical) return;

    const ctx = canvas.getContext('2d');
    const historical = cityData.historical;

    // Get AQI color for gradient
    const aqiColor = cityData.color;

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, hexToRgba(aqiColor, 0.4));
    gradient.addColorStop(1, hexToRgba(aqiColor, 0));

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: historical.map(d => d.timestamp),
            datasets: [{
                label: 'AQI',
                data: historical.map(d => d.aqi),
                borderColor: aqiColor,
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: aqiColor,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: aqiColor,
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: (items) => `Time: ${items[0].label}`,
                        label: (item) => `AQI: ${item.raw}`
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.5)',
                        maxTicksLimit: 8
                    }
                },
                y: {
                    min: 0,
                    max: Math.max(500, Math.max(...historical.map(d => d.aqi)) + 50),
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.5)',
                        stepSize: 100
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Convert hex color to rgba
 */
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// ==========================================================================
// AQI Gauge Animation
// ==========================================================================

/**
 * Animate the AQI gauge on page load
 */
function animateGauge() {
    const gauge = document.querySelector('.aqi-gauge');
    if (!gauge) return;

    const targetPercentage = parseInt(gauge.style.getPropertyValue('--aqi-percentage'));
    let currentPercentage = 0;

    const animate = () => {
        if (currentPercentage < targetPercentage) {
            currentPercentage += 2;
            gauge.style.setProperty('--aqi-percentage', `${Math.min(currentPercentage, targetPercentage)}%`);
            requestAnimationFrame(animate);
        }
    };

    // Start animation after a short delay
    setTimeout(animate, 300);
}

// ==========================================================================
// Auto Refresh
// ==========================================================================

/**
 * Set up auto-refresh for AQI data
 */
function initAutoRefresh() {
    // Refresh every 30 minutes
    const REFRESH_INTERVAL = 30 * 60 * 1000;

    setInterval(async () => {
        try {
            const citySlug = window.location.pathname.split('/').pop();
            const response = await fetch(`/api/aqi/${citySlug}`);
            const data = await response.json();

            // Update AQI value
            const aqiValue = document.querySelector('.aqi-value');
            if (aqiValue && data.aqi !== undefined) {
                aqiValue.textContent = data.aqi;
            }

            // Update last updated time
            const updateTime = document.querySelector('.update-time');
            if (updateTime && data.last_updated) {
                updateTime.textContent = `Last updated: ${data.last_updated}`;
            }

            console.log('AQI data refreshed');
        } catch (error) {
            console.error('Auto-refresh error:', error);
        }
    }, REFRESH_INTERVAL);
}

// ==========================================================================
// Utility Functions
// ==========================================================================

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Get AQI category class
 */
function getAqiClass(aqi) {
    if (aqi <= 50) return 'good';
    if (aqi <= 100) return 'satisfactory';
    if (aqi <= 200) return 'moderate';
    if (aqi <= 300) return 'poor';
    if (aqi <= 400) return 'very-poor';
    return 'severe';
}

// ==========================================================================
// Scroll Background Animation
// ==========================================================================

/**
 * Initialize scroll-based gradient animation
 */
function initScrollAnimation() {
    let ticking = false;

    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.scrollY;
                // Rotate gradient based on scroll position
                // Base angle is 180deg, we add rotation
                const rotation = scrolled * 0.2; // Adjust speed factor as needed
                const angle = 180 + rotation;

                document.body.style.setProperty('--gradient-angle', `${angle}deg`);
                ticking = false;
            });
            ticking = true;
        }
    });
}

// ==========================================================================
// Initialize
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initSearch();
    initChart();
    animateGauge();
    initAutoRefresh();
    initScrollAnimation();

    console.log('AirAware Dashboard initialized');
});

// ==========================================================================
// Namaste Air Chatbot
// ==========================================================================

const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");

let userMessage = null; // Variable to store user's message
const inputInitHeight = chatInput.scrollHeight;


const createChatLi = (message, className) => {
    // Create a chat <li> element with passed message and className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", `${className}`);
    let chatContent = className === "outgoing" ? `<p></p>` : `<img src="/static/images/namaste_air_logo.png" alt="Namaste Air"><p></p>`;
    chatLi.innerHTML = chatContent;
    chatLi.querySelector("p").textContent = message; // Safely set text content
    return chatLi;
}



const renderSuggestions = () => {
    // Check if suggestions already exist to avoid duplicates
    if (document.querySelector('.suggestions-container')) return;

    const suggestions = [
        "outdoor is safe?",
        "Health tips?",
        "Do I need a mask?"
    ];

    const suggestionsContainer = document.createElement("div");
    suggestionsContainer.classList.add("suggestions-container");

    suggestions.forEach(question => {
        const chip = document.createElement("button");
        chip.classList.add("suggestion-chip");
        chip.textContent = question;
        chip.addEventListener("click", () => {
            chatInput.value = question;
            handleChat();
        });
        suggestionsContainer.appendChild(chip);
    });

    // Insert before the chat input container
    const chatInputDiv = document.querySelector(".chat-input");
    const chatbot = document.querySelector(".chatbot");
    if (chatInputDiv && chatbot) {
        chatbot.insertBefore(suggestionsContainer, chatInputDiv);
    } else {
        // Fallback
        chatbox.appendChild(suggestionsContainer);
    }
}

const generateResponse = async (chatElement) => {
    const messageElement = chatElement.querySelector("p");

    try {
        // Prepare context data
        // cityData is available globally from index.html
        const context = typeof cityData !== 'undefined' ? {
            city: cityData.city,
            aqi: cityData.aqi,
            category: cityData.category
        } : {};

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userMessage,
                context: context
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();

        // Simulate thinking delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        messageElement.textContent = data.response;
    } catch (error) {
        console.error('Chatbot error:', error);
        messageElement.classList.add("error");
        messageElement.textContent = "I'm having trouble connecting to the server. Please try again later.";
    } finally {
        chatbox.scrollTo(0, chatbox.scrollHeight);
    }
}

const handleChat = () => {
    userMessage = chatInput.value.trim(); // Get user entered message and remove extra whitespace
    if (!userMessage) return;

    // Clear the input textarea and set its height to default
    chatInput.value = "";
    chatInput.style.height = `${inputInitHeight}px`;

    // Append the user's message to the chatbox
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
    chatbox.scrollTo(0, chatbox.scrollHeight);

    // Display "Thinking..." message while waiting for the response
    setTimeout(() => {
        const incomingChatLi = createChatLi("Thinking...", "incoming");
        chatbox.appendChild(incomingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);
        generateResponse(incomingChatLi);
    }, 600);
}

if (chatInput) {
    chatInput.addEventListener("input", () => {
        // Adjust the height of the input textarea based on its content
        chatInput.style.height = `${inputInitHeight}px`;
        chatInput.style.height = `${chatInput.scrollHeight}px`;
    });

    chatInput.addEventListener("keydown", (e) => {
        // If Enter key is pressed without Shift key and the window 
        // width is greater than 800px, handle the chat
        if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
            e.preventDefault();
            handleChat();
        }
    });
}

if (sendChatBtn) {
    sendChatBtn.addEventListener("click", handleChat);
}

if (closeBtn) {
    closeBtn.addEventListener("click", () => document.body.classList.remove("show-chatbot"));
}

if (chatbotToggler) {
    chatbotToggler.addEventListener("click", () => {
        document.body.classList.toggle("show-chatbot");
        // Put focus on input when opened
        if (document.body.classList.contains("show-chatbot")) {
            setTimeout(() => {
                chatInput.focus();
                renderSuggestions();
            }, 100);
        }
    });
}

// Close chatbot when clicking outside
document.addEventListener("click", (e) => {
    const chatbot = document.querySelector(".chatbot");
    if (document.body.classList.contains("show-chatbot") && chatbot && chatbotToggler) {
        // If click is not inside/on chatbot and not on toggler
        if (!chatbot.contains(e.target) && !chatbotToggler.contains(e.target)) {
            document.body.classList.remove("show-chatbot");
        }
    }
});

// ==========================================================================
// Health Risk Tabs
// ==========================================================================

const riskTabs = document.querySelectorAll('.risk-tab-btn');
const riskPanels = document.querySelectorAll('.risk-content-panel');

if (riskTabs.length > 0 && riskPanels.length > 0) {
    riskTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            riskTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');

            // Hide all panels
            riskPanels.forEach(panel => panel.classList.remove('active'));

            // Show target panel
            const targetId = tab.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}
