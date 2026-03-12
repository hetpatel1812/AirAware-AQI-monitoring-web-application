"""
Centralized configuration for the AirAware application.
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data paths
DATA_DIR = os.path.join(BASE_DIR, 'data')
CHATBOT_DIR = os.path.join(BASE_DIR, 'chatbot')

# Cache settings
CACHE_DURATION = 1800  # 30 minutes for AQI/weather data
NEWS_CACHE_DURATION = 3600  # 1 hour for news

# Weather API
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# News API
NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY", "")
NEWSDATA_BASE_URL = "https://newsdata.io/api/1/latest"

# Flask settings
STATIC_FILE_MAX_AGE = 31536000  # 1 year
