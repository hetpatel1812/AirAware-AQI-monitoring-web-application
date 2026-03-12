"""
Main page routes — dashboard, city pages, static pages.
"""
import os
from flask import Blueprint, render_template, send_from_directory, current_app

main_bp = Blueprint('main', __name__)


@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon from static directory."""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
        max_age=31536000
    )


@main_bp.route('/')
def home():
    """Home page — shows Delhi AQI by default."""
    return render_city_page('delhi-aqi')


@main_bp.route('/maps')
def maps():
    """Live AQI Map page."""
    return render_template('pages/maps.html')


@main_bp.route('/news')
def news_page():
    """Render the news page."""
    return render_template('pages/news.html')


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('pages/about.html')


@main_bp.route('/india-overview')
def india_overview():
    """India air quality overview page."""
    return render_template('pages/overview.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('pages/privacy.html')


@main_bp.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('pages/terms.html')


@main_bp.route('/faq')
def faq():
    """FAQ page."""
    return render_template('pages/faq.html')


@main_bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('pages/contact.html')


@main_bp.route('/in/<city_slug>')
def city_direct(city_slug):
    """Direct city route (e.g., /in/delhi-aqi)."""
    return render_city_page(city_slug)


@main_bp.route('/in/<state_slug>/<city_slug>')
def city_with_state(state_slug, city_slug):
    """City route with state (e.g., /in/maharashtra/mumbai-aqi)."""
    return render_city_page(city_slug)


def render_city_page(city_slug: str):
    """Render the city AQI page."""
    from services.data_generator import get_city_data
    from app import find_city, STATES_DATA

    city_info = find_city(city_slug)

    if not city_info:
        city_info = find_city('delhi-aqi')

    city_data = get_city_data(city_info)

    top_cities = [
        find_city('delhi-aqi'),
        find_city('mumbai-aqi'),
        find_city('bengaluru-aqi'),
        find_city('kolkata-aqi'),
        find_city('chennai-aqi')
    ]

    return render_template(
        'pages/dashboard.html',
        city=city_data,
        states=STATES_DATA['states'],
        top_cities=top_cities
    )
