"""
Data fetcher for AQI and weather data from external APIs.
Uses OpenAQ for air quality and OpenWeatherMap for weather.
"""
import os
import json
import time
import random
import requests
from datetime import datetime, timedelta
from functools import lru_cache

# API Configuration
OPENAQ_BASE_URL = "https://api.openaq.org/v2"
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Cache duration in seconds
CACHE_DURATION = 1800  # 30 minutes

# In-memory cache
_cache = {}


def get_cached_data(cache_key: str):
    """Get data from cache if not expired."""
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None


def set_cache(cache_key: str, data):
    """Store data in cache."""
    _cache[cache_key] = (data, time.time())


def fetch_aqi_from_openaq(city: str, lat: float = None, lng: float = None) -> dict:
    """
    Fetch AQI data from OpenAQ API.
    
    Args:
        city: City name
        lat: Latitude (optional, for more accurate results)
        lng: Longitude (optional)
    
    Returns:
        Dictionary with pollutant concentrations
    """
    cache_key = f"openaq_{city}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    try:
        # First try to find locations by city name
        params = {
            "country": "IN",
            "city": city,
            "limit": 10
        }
        
        # If coordinates provided, use radius search
        if lat and lng:
            params = {
                "coordinates": f"{lat},{lng}",
                "radius": 50000,  # 50km radius
                "limit": 10
            }
        
        response = requests.get(
            f"{OPENAQ_BASE_URL}/latest",
            params=params,
            headers={"Accept": "application/json"},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                # Aggregate measurements from all stations
                pollutants = aggregate_measurements(data["results"])
                set_cache(cache_key, pollutants)
                return pollutants
    
    except requests.Timeout:
        print(f"OpenAQ API timed out (city: {city})")
    except requests.RequestException as e:
        print(f"OpenAQ API error: {e}")
    
    # Return None to indicate API failure (will trigger demo data)
    return None


def aggregate_measurements(results: list) -> dict:
    """
    Aggregate measurements from multiple monitoring stations.
    Uses the most recent reading for each pollutant.
    """
    pollutants = {
        "pm25": None,
        "pm10": None,
        "no2": None,
        "so2": None,
        "co": None,
        "o3": None
    }
    
    # Mapping from OpenAQ parameter names to our keys
    param_mapping = {
        "pm25": "pm25",
        "pm10": "pm10",
        "no2": "no2",
        "so2": "so2",
        "co": "co",
        "o3": "o3"
    }
    
    for result in results:
        for measurement in result.get("measurements", []):
            param = measurement.get("parameter", "").lower()
            if param in param_mapping:
                key = param_mapping[param]
                value = measurement.get("value")
                if value is not None and value >= 0:
                    # Keep the highest value (worst case) for each pollutant
                    if pollutants[key] is None or value > pollutants[key]:
                        pollutants[key] = value
    
    return pollutants


def fetch_all_india_aqi() -> dict:
    """
    Fetch latest AQI data for all available locations in India from OpenAQ.
    Returns a dictionary mapping city names (lowercase) to their pollutants.
    """
    cache_key = "openaq_all_india"
    cached = get_cached_data(cache_key)
    if cached:
        return cached

    try:
        # Fetching a larger limit to cover many cities
        response = requests.get(
            f"{OPENAQ_BASE_URL}/latest",
            params={
                "country": "IN",
                "limit": 500,  # Adjust limit as needed based on coverage
                "order_by": "city"
            },
            headers={"Accept": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            city_map = {}
            
            if data.get("results"):
                for result in data["results"]:
                    city = result.get("city")
                    if not city:
                        continue
                    
                    # Normalize city name for matching
                    city_key = city.lower().strip()
                    
                    # If city already exists, we might want to average or pick max.
                    # For simplicity, we'll reuse the existing aggregation logic per result,
                    # but OpenAQ 'latest' returns one result per location.
                    # A city might have multiple locations. We should aggregate them.
                    
                    result_list = [result] # aggregate_measurements expects a list of results
                    pollutants = aggregate_measurements(result_list)
                    
                    if city_key in city_map:
                        # Update existing with max values (worst case scenario)
                        existing = city_map[city_key]
                        for key, val in pollutants.items():
                            if val is not None:
                                if existing.get(key) is None or val > existing[key]:
                                    existing[key] = val
                    else:
                        city_map[city_key] = pollutants
            
            set_cache(cache_key, city_map)
            return city_map

    except requests.RequestException as e:
        print(f"OpenAQ Bulk API error: {e}")

    return {}


def get_all_cities_aqi(all_cities_list: list) -> list:
    """
    Get AQI data for all cities in our application.
    Prioritizes live data from bulk fetch, falls back to demo data.
    """
    from utils.aqi_calculator import calculate_aqi # Import here to avoid circular dependency if needed
    
    # Try to get live data for all of India
    live_data_map = fetch_all_india_aqi()
    
    results = []
    
    for city_info in all_cities_list:
        city_name = city_info['name']
        city_key = city_name.lower().strip()
        
        pollutants = None
        
        # 1. Try exact match from live data
        if live_data_map and city_key in live_data_map:
            pollutants = live_data_map[city_key]
        
        # 2. If no live data, use demo data
        is_demo = False
        if pollutants is None or all(v is None for v in pollutants.values()):
            pollutants = get_demo_aqi_data(city_name)
            is_demo = True
            
        # Calculate AQI
        aqi_result = calculate_aqi(pollutants)
        
        results.append({
            'name': city_name,
            'slug': city_info['slug'],
            'state': city_info['state'],
            'lat': city_info.get('lat'),
            'lng': city_info.get('lng'),
            'aqi': aqi_result['aqi'],
            'category': aqi_result['category'],
            'color': aqi_result['color'],
            'is_demo': is_demo
        })
        
    return results


def fetch_weather(lat: float, lng: float) -> dict:
    """
    Fetch weather data from OpenWeatherMap API.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Dictionary with weather data
    """
    cache_key = f"weather_{lat}_{lng}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    if not WEATHER_API_KEY:
        return get_demo_weather()
    
    try:
        response = requests.get(
            f"{WEATHER_BASE_URL}/weather",
            params={
                "lat": lat,
                "lon": lng,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            },
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            weather = {
                "temperature": round(data.get("main", {}).get("temp", 0)),
                "feels_like": round(data.get("main", {}).get("feels_like", 0)),
                "humidity": data.get("main", {}).get("humidity", 0),
                "wind_speed": round(data.get("wind", {}).get("speed", 0) * 3.6),  # Convert m/s to km/h
                "wind_direction": data.get("wind", {}).get("deg", 0),
                "description": data.get("weather", [{}])[0].get("description", "").title(),
                "icon": data.get("weather", [{}])[0].get("icon", "01d")
            }
            set_cache(cache_key, weather)
            return weather
    
    except requests.Timeout:
        print(f"Weather API timed out (lat: {lat}, lng: {lng})")
    except requests.RequestException as e:
        print(f"Weather API error: {e}")
    
    return get_demo_weather()


def get_demo_weather() -> dict:
    """Generate demo weather data with accurate hourly forecast times."""
    now = datetime.now()
    current_hour = now.hour

    # Use date-based seed so values stay consistent within the same hour
    seed = int(now.strftime("%Y%m%d%H"))
    rng = random.Random(seed)

    base_temp = rng.randint(18, 35)

    # Generate hourly forecast: current hour + next 5 hours
    hourly_forecast = []
    day_conditions = [
        {"condition": "Clear Sky", "icon": "☀️"},
        {"condition": "Partly Cloudy", "icon": "⛅"},
        {"condition": "Scattered Clouds", "icon": "🌤️"},
        {"condition": "Cloudy", "icon": "☁️"},
        {"condition": "Hazy", "icon": "🌫️"},
    ]

    for i in range(6):
        hour = (current_hour + i) % 24

        # Temperature varies by time of day
        if 6 <= hour <= 14:
            temp_offset = rng.randint(-2, 4)
        elif 14 < hour <= 18:
            temp_offset = rng.randint(-4, 0)
        else:
            temp_offset = rng.randint(-8, -3)

        forecast_temp = base_temp + temp_offset

        # Pick weather condition (night hours get moon/cloud icons)
        if hour >= 19 or hour < 6:
            if rng.random() < 0.5:
                condition = {"condition": "Clear Night", "icon": "🌙"}
            else:
                condition = {"condition": "Partly Cloudy", "icon": "☁️"}
        else:
            condition = rng.choice(day_conditions)

        # Show "Now" for first slot, then upcoming full hours
        if i == 0:
            time_label = "Now"
        else:
            time_label = f"{hour:02d}:00"

        hourly_forecast.append({
            "time": time_label,
            "temp": forecast_temp,
            "icon": condition["icon"],
            "condition": condition["condition"]
        })

    return {
        "temperature": base_temp,
        "feels_like": base_temp + rng.randint(-2, 3),
        "humidity": rng.randint(30, 80),
        "wind_speed": rng.randint(5, 25),
        "wind_direction": rng.randint(0, 360),
        "description": rng.choice(["Clear Sky", "Partly Cloudy", "Hazy", "Scattered Clouds"]),
        "icon": "01d",
        "hourly_forecast": hourly_forecast
    }


def get_demo_aqi_data(city: str = "Delhi") -> dict:
    """
    Generate realistic demo AQI data when API is unavailable.
    Values are based on typical pollution levels for specific Indian cities.
    
    PM2.5 to AQI mapping (CPCB India):
    - PM2.5: 0-30 μg/m³ → AQI 0-50 (Good)
    - PM2.5: 31-60 μg/m³ → AQI 51-100 (Satisfactory)
    - PM2.5: 61-90 μg/m³ → AQI 101-200 (Moderate)
    - PM2.5: 91-120 μg/m³ → AQI 201-300 (Poor)
    - PM2.5: 121-250 μg/m³ → AQI 301-400 (Very Poor)
    - PM2.5: 251+ μg/m³ → AQI 401-500 (Severe)
    """
    
    # City pollution profiles with PM2.5 ranges calibrated to target AQI
    # Format: (pm25_min, pm25_max, target_aqi_min, target_aqi_max)
    city_profiles = {
        # Severely Polluted - NCR Region (AQI 250-450)
        # PM2.5: 91-250 for AQI 201-400
        "Delhi": (100, 220, 250, 450),
        "Ghaziabad": (110, 240, 280, 480),
        "Noida": (95, 210, 240, 430),
        "Gurugram": (95, 200, 240, 420),
        "Faridabad": (100, 220, 250, 450),
        "Greater Noida": (105, 230, 260, 460),
        
        # Highly Polluted - Industrial/North India (AQI 150-350)
        # PM2.5: 70-150 for AQI 150-350
        "Patna": (75, 140, 150, 320),
        "Lucknow": (70, 130, 140, 300),
        "Kanpur": (72, 135, 145, 310),
        "Muzaffarpur": (78, 145, 160, 330),
        "Varanasi": (68, 125, 135, 290),
        "Agra": (65, 120, 130, 280),
        "Meerut": (72, 130, 145, 300),
        "Dhanbad": (70, 128, 140, 295),
        "Jamshedpur": (65, 120, 130, 280),
        "Bhilai": (62, 115, 125, 270),
        "Raipur": (58, 110, 115, 260),
        "Ludhiana": (75, 145, 150, 330),
        "Amritsar": (70, 138, 140, 315),
        "Jalandhar": (65, 130, 130, 300),
        "Patiala": (70, 135, 140, 310),
        "Chandigarh": (60, 120, 120, 280),
        "Bathinda": (75, 142, 150, 325),
        "Prayagraj": (70, 130, 140, 300),
        "Gorakhpur": (72, 135, 145, 310),
        "Bareilly": (70, 130, 140, 300),
        "Aligarh": (75, 138, 150, 315),
        "Moradabad": (70, 130, 140, 300),
        
        # Moderately Polluted - Major Metros (AQI 100-200)
        # PM2.5: 61-90 for AQI 101-200
        "Mumbai": (61, 88, 101, 195),
        "Kolkata": (63, 90, 105, 200),
        "Ahmedabad": (65, 90, 108, 200),
        "Hyderabad": (58, 85, 95, 188),
        "Surat": (60, 88, 100, 195),
        "Jaipur": (63, 90, 105, 200),
        "Nagpur": (60, 87, 100, 192),
        "Indore": (58, 85, 95, 188),
        "Bhopal": (60, 88, 100, 195),
        "Thane": (58, 86, 95, 190),
        "Nashik": (55, 82, 90, 180),
        "Rajkot": (58, 85, 95, 188),
        "Vadodara": (60, 88, 100, 195),
        "Jodhpur": (62, 89, 103, 198),
        "Udaipur": (55, 80, 90, 175),
        "Jamnagar": (56, 82, 92, 180),
        "Bhubaneswar": (55, 82, 90, 180),
        "Cuttack": (56, 83, 92, 182),
        "Siliguri": (58, 85, 95, 188),
        "Durgapur": (63, 90, 105, 200),
        "Asansol": (65, 92, 108, 205),
        "Guwahati": (55, 80, 90, 175),
        "Agartala": (52, 78, 85, 170),
        
        # Low Pollution - Southern/Coastal Cities (AQI 50-120)
        # PM2.5: 25-70 for AQI 50-120
        "Chennai": (28, 65, 50, 115),
        "Bengaluru": (30, 68, 52, 118),
        "Pune": (28, 65, 50, 115),
        "Kochi": (18, 52, 35, 88),
        "Thiruvananthapuram": (15, 48, 30, 82),
        "Coimbatore": (22, 58, 42, 98),
        "Mangaluru": (15, 48, 30, 82),
        "Visakhapatnam": (22, 60, 42, 100),
        "Mysuru": (18, 54, 35, 92),
        "Madurai": (25, 62, 45, 105),
        "Kozhikode": (14, 46, 28, 78),
        "Panaji": (12, 42, 24, 72),
        "Margao": (12, 42, 24, 72),
        
        # Very Clean - Hill Stations & Remote (AQI 15-60)
        # PM2.5: 5-30 for AQI 15-60
        "Shimla": (8, 28, 15, 52),
        "Manali": (6, 25, 12, 48),
        "Dharamshala": (8, 27, 15, 50),
        "Gangtok": (6, 24, 12, 45),
        "Shillong": (10, 30, 18, 55),
        "Aizawl": (8, 26, 15, 48),
        "Kohima": (8, 27, 15, 50),
        "Imphal": (10, 28, 18, 52),
        "Itanagar": (8, 27, 15, 50),
        "Port Blair": (5, 22, 10, 42),
        "Leh": (4, 18, 8, 35),
        "Rishikesh": (12, 38, 22, 65),
        "Haridwar": (15, 42, 28, 72),
        "Dehradun": (18, 48, 32, 82),
        "Ooty": (5, 22, 10, 42),
        "Munnar": (4, 18, 8, 35),
    }
    
    # Get profile for city or use default moderate profile
    if city in city_profiles:
        pm25_min, pm25_max, target_aqi_min, target_aqi_max = city_profiles[city]
    else:
        # Default: moderate pollution (similar to tier-2 city)
        pm25_min, pm25_max, target_aqi_min, target_aqi_max = (55, 82, 90, 180)
    
    # Generate PM2.5 value within range
    pm25 = random.uniform(pm25_min, pm25_max)
    
    # Calculate multiplier based on PM2.5 level
    if pm25 <= 30:
        multiplier = 0.3
    elif pm25 <= 60:
        multiplier = 0.6
    elif pm25 <= 90:
        multiplier = 1.0
    elif pm25 <= 120:
        multiplier = 1.4
    else:
        multiplier = 1.8
    
    # PM10 is typically 1.5-2x PM2.5
    pm10 = pm25 * random.uniform(1.5, 2.2)
    
    return {
        "pm25": round(pm25, 1),
        "pm10": round(pm10, 1),
        "no2": round(random.uniform(12, 60) * multiplier, 1),
        "so2": round(random.uniform(6, 35) * multiplier, 1),
        "co": round(random.uniform(0.2, 2.0) * multiplier, 2),
        "o3": round(random.uniform(20, 80) * multiplier, 1)
    }


def get_historical_data(city: str, hours: int = 24) -> list:
    """
    Generate historical AQI data for charts.
    Uses city-specific base values for realistic trends.
    """
    now = datetime.now()
    data = []
    
    # City-specific base AQI ranges for historical trends
    city_base_aqi = {
        # Severely polluted
        "Delhi": (200, 350), "Ghaziabad": (220, 380), "Noida": (190, 340),
        "Gurugram": (180, 320), "Faridabad": (200, 350),
        # Highly polluted
        "Patna": (150, 280), "Lucknow": (140, 260), "Kanpur": (145, 270),
        "Varanasi": (130, 250), "Agra": (120, 240),
        # Moderately polluted
        "Mumbai": (80, 160), "Kolkata": (90, 170), "Ahmedabad": (100, 180),
        "Hyderabad": (70, 150), "Jaipur": (90, 175),
        # Low pollution
        "Chennai": (50, 100), "Bengaluru": (55, 110), "Pune": (50, 105),
        "Kochi": (30, 70), "Thiruvananthapuram": (25, 65),
        # Very clean
        "Shimla": (20, 50), "Gangtok": (15, 45), "Shillong": (20, 55),
        "Port Blair": (15, 40), "Leh": (10, 35),
    }
    
    # Get base range for city
    if city in city_base_aqi:
        base_min, base_max = city_base_aqi[city]
    else:
        base_min, base_max = (60, 150)  # Default moderate
    
    base_aqi = random.randint(base_min, base_max)
    
    for i in range(hours, 0, -1):
        timestamp = now - timedelta(hours=i)
        # Add hourly variation (pollution tends to be higher in morning/evening)
        hour = timestamp.hour
        if 7 <= hour <= 10 or 17 <= hour <= 21:
            time_factor = 1.15  # Rush hours - higher pollution
        elif 2 <= hour <= 5:
            time_factor = 0.85  # Early morning - lower pollution
        else:
            time_factor = 1.0
        
        variation = random.randint(-20, 20)
        aqi = int(max(10, min(500, (base_aqi + variation) * time_factor)))
        
        data.append({
            "timestamp": timestamp.strftime("%H:%M"),
            "aqi": aqi,
            "hour": timestamp.hour
        })
        
        # Slowly drift the base value within city's typical range
        base_aqi += random.randint(-8, 8)
        base_aqi = max(base_min, min(base_max, base_aqi))
    
    return data


def get_city_data(city_info: dict) -> dict:
    """
    Get complete data for a city including AQI, weather, and recommendations.
    
    Args:
        city_info: Dictionary with city name, lat, lng
    
    Returns:
        Complete city data dictionary
    """
    city_name = city_info.get("name", "Unknown")
    lat = city_info.get("lat")
    lng = city_info.get("lng")
    
    # Fetch pollutant data
    pollutants = fetch_aqi_from_openaq(city_name, lat, lng)
    
    # Use demo data if API fails
    if pollutants is None or all(v is None for v in pollutants.values()):
        pollutants = get_demo_aqi_data(city_name)
        data_source = "demo"
    else:
        data_source = "openaq"
    
    # Calculate AQI
    from utils.aqi_calculator import calculate_aqi, get_health_recommendations, format_pollutant_display, get_health_risks
    
    aqi_result = calculate_aqi(pollutants)
    # health_info = get_health_recommendations(aqi_result["category"]) # Removed in favor of Health Impact Card
    health_risks = get_health_risks(aqi_result["category"])
    
    # Calculate Cigarette Equivalence (Berkeley Earth: 1 cigarette = 22 µg/m3 PM2.5)
    pm25_val = pollutants.get('pm25', 0) or 0
    cigarettes_per_day = round(pm25_val / 22, 1)
    
    # Calculate Solutions based on AQI (Simple logic for demo)
    solutions = []
    
    # Air Purifier
    if aqi_result["aqi"] > 100:
        solutions.append({"name": "Air Purifier", "action": "Turn On", "icon": "air_purifier_gen", "status": "must"})
    else:
        solutions.append({"name": "Air Purifier", "action": "Optional", "icon": "air_purifier_gen", "status": "optional"})
        
    # Car Filter
    if aqi_result["aqi"] > 150:
         solutions.append({"name": "Car Filter", "action": "Must", "icon": "directions_car", "status": "must"})
    else:
         solutions.append({"name": "Car Filter", "action": "Check", "icon": "directions_car", "status": "optional"})
         
    # N95 Mask
    if aqi_result["aqi"] > 200:
        solutions.append({"name": "N95 Mask", "action": "Must", "icon": "masks", "status": "must"})
    else:
        solutions.append({"name": "N95 Mask", "action": "Optional", "icon": "masks", "status": "optional"})

    # Stay Indoor
    if aqi_result["aqi"] > 250:
        solutions.append({"name": "Stay Indoor", "action": "Must", "icon": "home", "status": "must"})
    else:
        solutions.append({"name": "Stay Indoor", "action": "Preferred", "icon": "home", "status": "optional"})


    # Fetch weather
    weather = fetch_weather(lat, lng) if lat and lng else get_demo_weather()
    
    # Format pollutants for display
    pollutants_display = []
    for key, value in pollutants.items():
        if value is not None:
            display = format_pollutant_display(key)
            pollutants_display.append({
                "key": key,
                "name": display["name"],
                "value": value,
                "unit": display["unit"],
                "full_name": display["full_name"],
                "sub_index": aqi_result["sub_indices"].get(key, 0)
            })
    
    # Get historical data
    historical = get_historical_data(city_name)
    
    return {
        "city": city_name,
        "state": city_info.get("state", ""),
        "aqi": aqi_result["aqi"],
        "category": aqi_result["category"],
        "color": aqi_result["color"],
        "description": aqi_result["description"],
        "dominant_pollutant": aqi_result["dominant_pollutant"],
        "pollutants": pollutants_display,
        "weather": weather,
        # "health": health_info, # Removed
        "health_impact": {
            "cigarettes_per_day": cigarettes_per_day,
            "cigarettes_weekly": round(cigarettes_per_day * 7, 1),
            "cigarettes_monthly": round(cigarettes_per_day * 30, 0),
            "solutions": solutions
        },
        "health_risks": health_risks,
        "historical": historical,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": data_source
    }
