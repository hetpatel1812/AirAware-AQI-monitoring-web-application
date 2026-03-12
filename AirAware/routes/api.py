"""
API routes — data endpoints and chatbot.
"""
import random
from datetime import datetime
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/map-data')
def map_data():
    """API endpoint for map data (all cities)."""
    from services.data_generator import get_all_cities_aqi
    from app import ALL_CITIES

    cities_data = get_all_cities_aqi(ALL_CITIES)

    return jsonify({
        'cities': cities_data,
        'count': len(cities_data),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@api_bp.route('/news')
def news():
    """API endpoint for AQI news."""
    from services.news_service import fetch_aqi_news
    news_data = fetch_aqi_news()
    return jsonify({'news': news_data})


@api_bp.route('/aqi/<city_slug>')
def aqi(city_slug):
    """API endpoint for city AQI data."""
    from services.data_generator import get_city_data
    from app import find_city

    city_info = find_city(city_slug)

    if not city_info:
        return jsonify({'error': 'City not found'}), 404

    city_data = get_city_data(city_info)
    return jsonify(city_data)


@api_bp.route('/search')
def search():
    """API endpoint for city search."""
    from app import search_cities

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


@api_bp.route('/cities')
def cities():
    """API endpoint to get all cities."""
    from app import ALL_CITIES

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


@api_bp.route('/states')
def states():
    """API endpoint to get all states with their cities."""
    from app import STATES_DATA
    return jsonify(STATES_DATA)


@api_bp.route('/top-cities')
def top_cities():
    """API endpoint to get top polluted cities."""
    from services.data_generator import get_city_data
    from app import find_city

    major_cities = [
        'delhi-aqi', 'mumbai-aqi', 'kolkata-aqi', 'chennai-aqi',
        'bengaluru-aqi', 'hyderabad-aqi', 'ahmedabad-aqi', 'pune-aqi',
        'lucknow-aqi', 'jaipur-aqi'
    ]

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

    city_data.sort(key=lambda x: x['aqi'], reverse=True)
    return jsonify({'cities': city_data})


@api_bp.route('/chat', methods=['POST'])
def chat():
    """Chatbot API endpoint with context awareness."""
    from app import chatbot_model, chatbot_vectorizer, intents_data

    if not chatbot_model or not chatbot_vectorizer:
        return jsonify({
            'response': "I'm currently undergoing maintenance. Please try again later.",
            'tag': 'error'
        })

    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Predict Intent
    try:
        vec = chatbot_vectorizer.transform([message])
        tag = chatbot_model.predict(vec)[0]
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({
            'response': "I didn't quite catch that. Could you rephrase?",
            'tag': 'error'
        })

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
        category = context.get('category', 'unknown')

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
