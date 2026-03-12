"""
News service for fetching AQI-related news from NewsData.io.
"""
import requests
import time
import os
from config import NEWSDATA_API_KEY, NEWSDATA_BASE_URL, NEWS_CACHE_DURATION

# Simple in-memory cache
_news_cache = {
    "data": None,
    "timestamp": 0
}


def fetch_aqi_news():
    """
    Fetches the latest AQI-related news from NewsData.io for India.
    Uses caching to avoid hitting rate limits.
    """
    global _news_cache

    current_time = time.time()

    # Check if cache is valid
    if _news_cache["data"] and (current_time - _news_cache["timestamp"] < NEWS_CACHE_DURATION):
        print("DEBUG: Serving news from cache")
        return _news_cache["data"]

    if not NEWSDATA_API_KEY:
        print("WARNING: NEWSDATA_API_KEY not set in .env file")
        return []

    print("DEBUG: Fetching news from API")

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": "AQI",
        "country": "in",
        "language": "en",
        "image": 1,
        "removeduplicate": 1
    }

    try:
        response = requests.get(NEWSDATA_BASE_URL, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                results = data.get("results", [])

                # Update cache
                _news_cache["data"] = results
                _news_cache["timestamp"] = current_time

                return results
            else:
                print(f"ERROR: News API returned status {data.get('status')}")
                return []
        else:
            print(f"ERROR: News API failed with status code {response.status_code}")
            return []

    except Exception as e:
        print(f"ERROR: Exception fetching news: {e}")
        return []
