"""
AirAware Dashboard — Flask Application
Real-time Air Quality Index monitoring for Indian cities.
"""
from dotenv import load_dotenv
load_dotenv()

import os
import json
import pickle
from difflib import SequenceMatcher
from flask import Flask
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

from config import DATA_DIR, CHATBOT_DIR, STATIC_FILE_MAX_AGE


# ─── Load data ───────────────────────────────────────────────
with open(os.path.join(DATA_DIR, 'cities.json'), 'r', encoding='utf-8') as f:
    STATES_DATA = json.load(f)

# ─── Load chatbot model ─────────────────────────────────────
try:
    with open(os.path.join(CHATBOT_DIR, 'model.pkl'), 'rb') as f:
        chatbot_model = pickle.load(f)
    with open(os.path.join(CHATBOT_DIR, 'vectorizer.pkl'), 'rb') as f:
        chatbot_vectorizer = pickle.load(f)
    with open(os.path.join(CHATBOT_DIR, 'intents.json'), 'r') as f:
        intents_data = json.load(f)
    print("Chatbot model loaded successfully.")
except Exception as e:
    print(f"Error loading chatbot model: {e}")
    chatbot_model = None
    chatbot_vectorizer = None
    intents_data = None

# ─── Build city lookup ───────────────────────────────────────
CITY_INDEX = {}
ALL_CITIES = []

for state in STATES_DATA['states']:
    state_name = state['name']
    state_slug = state['slug']

    for city in state['cities']:
        city_key = city['slug']
        city_info = {
            **city,
            'state': state_name,
            'state_slug': state_slug
        }
        CITY_INDEX[city_key] = city_info
        CITY_INDEX[city['name'].lower()] = city_info
        ALL_CITIES.append(city_info)


def find_city(slug_or_name: str) -> dict:
    """Find a city by slug or name."""
    if slug_or_name in CITY_INDEX:
        return CITY_INDEX[slug_or_name]

    lower = slug_or_name.lower()
    if lower in CITY_INDEX:
        return CITY_INDEX[lower]

    slug = lower.replace(' ', '-')
    if slug in CITY_INDEX:
        return CITY_INDEX[slug]

    slug_aqi = f"{slug}-aqi"
    if slug_aqi in CITY_INDEX:
        return CITY_INDEX[slug_aqi]

    return None


def search_cities(query: str, limit: int = 10) -> list:
    """Search for cities matching the query."""
    if not query or len(query) < 2:
        return []

    query_lower = query.lower()
    results = []

    for city in ALL_CITIES:
        city_name_lower = city['name'].lower()
        state_name_lower = city['state'].lower()

        if query_lower in city_name_lower:
            score = SequenceMatcher(None, query_lower, city_name_lower).ratio()
            if city_name_lower.startswith(query_lower):
                score += 0.5
            results.append((score, city))
        elif query_lower in state_name_lower:
            score = SequenceMatcher(None, query_lower, state_name_lower).ratio() * 0.5
            results.append((score, city))

    results.sort(key=lambda x: x[0], reverse=True)
    return [city for _, city in results[:limit]]


# ─── App factory ─────────────────────────────────────────────
def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = STATIC_FILE_MAX_AGE

    # Register blueprints
    from routes.main import main_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)