"""
AirAware Dashboard - Flask Application
Real-time Air Quality Index monitoring for Indian cities.
"""
import os
import json
import pickle
import random
from difflib import SequenceMatcher
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

# Initialize Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache static files for 1 year

# Load city data
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')

with open(os.path.join(DATA_DIR, 'states_cities.json'), 'r', encoding='utf-8') as f:
    STATES_DATA = json.load(f)

# Load Chatbot Model and Vectorizer
try:
    with open(os.path.join(MODEL_DIR, 'chatbot_model.pkl'), 'rb') as f:
        chatbot_model = pickle.load(f)
    with open(os.path.join(MODEL_DIR, 'vectorizer.pkl'), 'rb') as f:
        chatbot_vectorizer = pickle.load(f)
    with open(os.path.join(MODEL_DIR, 'intents.json'), 'r') as f:
        intents_data = json.load(f)
    print("Chatbot model loaded successfully.")
except Exception as e:
    print(f"Error loading chatbot model: {e}")
    chatbot_model = None
    chatbot_vectorizer = None
    intents_data = None

# Build city lookup index
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
    # Try exact match first
    if slug_or_name in CITY_INDEX:
        return CITY_INDEX[slug_or_name]
    
    # Try lowercase match
    lower = slug_or_name.lower()
    if lower in CITY_INDEX:
        return CITY_INDEX[lower]
    
    # Try slug format
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
        
        # Check if query matches city or state name
        if query_lower in city_name_lower:
            # Calculate match score
            score = SequenceMatcher(None, query_lower, city_name_lower).ratio()
            if city_name_lower.startswith(query_lower):
                score += 0.5  # Boost for prefix match
            results.append((score, city))
        elif query_lower in state_name_lower:
            score = SequenceMatcher(None, query_lower, state_name_lower).ratio() * 0.5
            results.append((score, city))
    
    # Sort by score and return top results
    results.sort(key=lambda x: x[0], reverse=True)
    return [city for _, city in results[:limit]]



@app.route('/favicon.ico')
def favicon():
    """Serve favicon from static directory."""
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
        max_age=31536000  # Cache for 1 year
    )


@app.route('/maps')
def maps():
    """Live AQI Map page."""
    return render_template('maps.html')


@app.route('/news')
def news_page():
    """Render the news page."""
    return render_template('news.html')


@app.route('/api/map-data')
def api_map_data():
    """API endpoint for map data (all cities)."""
    from utils.data_fetcher import get_all_cities_aqi
    
    # Get all cities data
    cities_data = get_all_cities_aqi(ALL_CITIES)
    
    return jsonify({
        'cities': cities_data,
        'count': len(cities_data),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/news')
def api_news():
    """API endpoint for AQI news."""
    from utils.news_fetcher import fetch_aqi_news
    news = fetch_aqi_news()
    return jsonify({'news': news})


@app.route('/')
def home():
    """Home page - shows Delhi AQI by default."""
    return render_city_page('delhi-aqi')



@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@app.route('/india-overview')
def india_overview():
    """India air quality overview page."""
    return render_template('india_overview.html')


@app.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('terms.html')


@app.route('/faq')
def faq():
    """FAQ page."""
    return render_template('faq.html')


@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')



@app.route('/in/<city_slug>')
def city_direct(city_slug):
    """Direct city route (e.g., /in/delhi-aqi)."""
    return render_city_page(city_slug)


@app.route('/in/<state_slug>/<city_slug>')
def city_with_state(state_slug, city_slug):
    """City route with state (e.g., /in/maharashtra/mumbai-aqi)."""
    return render_city_page(city_slug)


def render_city_page(city_slug: str):
    """Render the city AQI page."""
    from utils.data_fetcher import get_city_data
    
    city_info = find_city(city_slug)
    
    if not city_info:
        # Default to Delhi if city not found
        city_info = find_city('delhi-aqi')
    
    # Get complete city data
    city_data = get_city_data(city_info)
    
    # Get top cities for footer
    top_cities = [
        find_city('delhi-aqi'),
        find_city('mumbai-aqi'),
        find_city('bengaluru-aqi'),
        find_city('kolkata-aqi'),
        find_city('chennai-aqi')
    ]
    
    return render_template(
        'index.html',
        city=city_data,
        states=STATES_DATA['states'],
        top_cities=top_cities
    )


@app.route('/api/aqi/<city_slug>')
def api_aqi(city_slug):
    """API endpoint for city AQI data."""
    from utils.data_fetcher import get_city_data
    
    city_info = find_city(city_slug)
    
    if not city_info:
        return jsonify({'error': 'City not found'}), 404
    
    city_data = get_city_data(city_info)
    return jsonify(city_data)


@app.route('/api/search')
def api_search():
    """API endpoint for city search."""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 10)), 20)
    
    results = search_cities(query, limit)
    
    return jsonify({
        'query': query,
        'results': [
            {
                'name': city['name'],
                'state': city['state'],
                'slug': city['slug'],
                'url': f"/in/{city['state_slug']}/{city['slug']}"
            }
            for city in results
        ]
    })


@app.route('/api/cities')
def api_cities():
    """API endpoint to get all cities."""
    return jsonify({
        'total': len(ALL_CITIES),
        'cities': [
            {
                'name': city['name'],
                'state': city['state'],
                'slug': city['slug'],
                'lat': city.get('lat'),
                'lng': city.get('lng')
            }
            for city in ALL_CITIES
        ]
    })


@app.route('/api/states')
def api_states():
    """API endpoint to get all states with their cities."""
    return jsonify(STATES_DATA)


@app.route('/api/top-cities')
def api_top_cities():
    """API endpoint to get top polluted cities (demo data)."""
    from utils.data_fetcher import get_city_data
    
    # Get AQI for major cities
    major_cities = ['delhi-aqi', 'mumbai-aqi', 'kolkata-aqi', 'chennai-aqi', 
                    'bengaluru-aqi', 'hyderabad-aqi', 'ahmedabad-aqi', 'pune-aqi',
                    'lucknow-aqi', 'jaipur-aqi']
    
    city_data = []
    for slug in major_cities:
        city_info = find_city(slug)
        if city_info:
            data = get_city_data(city_info)
            city_data.append({
                'name': data['city'],
                'state': data['state'],
                'aqi': data['aqi'],
                'category': data['category'],
                'color': data['color']
            })
    
    # Sort by AQI (highest first)
    city_data.sort(key=lambda x: x['aqi'], reverse=True)
    
    return jsonify({'cities': city_data})


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chatbot API endpoint with context awareness."""
    if not chatbot_model or not chatbot_vectorizer:
        return jsonify({'response': "I'm currently undergoing maintenance. Please try again later.", 'tag': 'error'})

    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})  # Expecting {'city': 'Name', 'aqi': 123, 'category': 'Good'}

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Predict Intent
    try:
        vec = chatbot_vectorizer.transform([message])
        tag = chatbot_model.predict(vec)[0]
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'response': "I didn't quite catch that. Could you rephrase?", 'tag': 'error'})

    # Get Response
    response = "I'm not sure how to answer that."
    for intent in intents_data['intents']:
        if intent['tag'] == tag:
            response = random.choice(intent['responses'])
            break
    
    # Context Injection
    if context:
        city_name = context.get('city', 'your city')
        aqi_level = context.get('aqi', 'unknown')
        category = context.get('category', 'unknown') # Good, Moderate, etc.

        if tag == 'greeting':
            response = f"{response} I see you're looking at {city_name} (AQI: {aqi_level})."
        elif tag == 'precautions_high_aqi':
            if isinstance(aqi_level, int) and aqi_level > 200:
                response = f"Since the AQI in {city_name} is {aqi_level} ({category}), it's very important to {response.lower()}"
            else:
                response = f"For {city_name} with AQI {aqi_level}, keep this in mind: {response}"
        elif tag == 'aqi_levels':
             response = f"{response} Currently, {city_name} is in the '{category}' category."
        elif tag == "health_impacts":
             if isinstance(aqi_level, int) and aqi_level > 150:
                 response = f"With an AQI of {aqi_level} in {city_name}, the health risks are significant. {response}"

    return jsonify({'response': response, 'tag': tag})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
