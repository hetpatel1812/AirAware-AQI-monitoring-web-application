"""
AQI Calculator based on CPCB (Central Pollution Control Board) India standards.
"""
import json
import os

# Load breakpoints
BREAKPOINTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'aqi_breakpoints.json')

with open(BREAKPOINTS_PATH, 'r') as f:
    BREAKPOINTS = json.load(f)

# AQI Categories
AQI_CATEGORIES = [
    {"min": 0, "max": 50, "category": "Good", "color": "#00e400", "description": "Minimal impact on health"},
    {"min": 51, "max": 100, "category": "Satisfactory", "color": "#ffff00", "description": "Minor breathing discomfort for sensitive people"},
    {"min": 101, "max": 200, "category": "Moderate", "color": "#ff7e00", "description": "Breathing discomfort for people with asthma and heart conditions"},
    {"min": 201, "max": 300, "category": "Poor", "color": "#ff0000", "description": "Breathing discomfort on prolonged exposure"},
    {"min": 301, "max": 400, "category": "Very Poor", "color": "#99004c", "description": "Respiratory illness on prolonged exposure"},
    {"min": 401, "max": 500, "category": "Severe", "color": "#7e0023", "description": "Affects healthy people, serious impact on those with existing conditions"}
]

# Health recommendations by AQI category
HEALTH_RECOMMENDATIONS = {
    "Good": {
        "general": "Air quality is satisfactory. Enjoy outdoor activities!",
        "sensitive": "No precautions needed.",
        "outdoor_activity": "All outdoor activities are safe.",
        "mask_required": False
    },
    "Satisfactory": {
        "general": "Air quality is acceptable. Some pollutants may affect very sensitive individuals.",
        "sensitive": "Unusually sensitive people may experience minor symptoms.",
        "outdoor_activity": "Outdoor activities are generally safe.",
        "mask_required": False
    },
    "Moderate": {
        "general": "Air quality is unhealthy for sensitive groups.",
        "sensitive": "People with respiratory or heart conditions should limit outdoor exertion.",
        "outdoor_activity": "Reduce prolonged outdoor exertion.",
        "mask_required": True
    },
    "Poor": {
        "general": "Everyone may experience health effects; sensitive groups more seriously affected.",
        "sensitive": "People with respiratory or heart disease should avoid outdoor activities.",
        "outdoor_activity": "Avoid prolonged outdoor activities. Wear N95 mask if going outside.",
        "mask_required": True
    },
    "Very Poor": {
        "general": "Health alert: everyone may experience more serious health effects.",
        "sensitive": "People with respiratory or heart conditions should stay indoors.",
        "outdoor_activity": "Avoid all outdoor activities. Keep windows closed.",
        "mask_required": True
    },
    "Severe": {
        "general": "Health warning of emergency conditions. Everyone is likely to be affected.",
        "sensitive": "All people should stay indoors and keep activity levels low.",
        "outdoor_activity": "Stay indoors. Use air purifiers. Seek medical help if experiencing symptoms.",
        "mask_required": True
    }
}


def calculate_sub_index(pollutant: str, concentration: float) -> int:
    """
    Calculate sub-index for a specific pollutant.
    
    Args:
        pollutant: One of 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3'
        concentration: Pollutant concentration value
    
    Returns:
        Sub-index value (0-500)
    """
    if pollutant not in BREAKPOINTS:
        return 0
    
    breakpoints = BREAKPOINTS[pollutant]
    
    for bp in breakpoints:
        if bp['low_conc'] <= concentration <= bp['high_conc']:
            # Linear interpolation formula
            sub_index = ((bp['high_aqi'] - bp['low_aqi']) / (bp['high_conc'] - bp['low_conc'])) * \
                       (concentration - bp['low_conc']) + bp['low_aqi']
            return round(sub_index)
    
    # If concentration exceeds highest breakpoint
    if concentration > breakpoints[-1]['high_conc']:
        return 500
    
    return 0


def calculate_aqi(pollutants: dict) -> dict:
    """
    Calculate overall AQI from pollutant concentrations.
    
    Args:
        pollutants: Dictionary with pollutant concentrations
                   Keys: pm25, pm10, no2, so2, co, o3
    
    Returns:
        Dictionary with AQI value, category, color, and sub-indices
    """
    sub_indices = {}
    
    # Calculate sub-index for each pollutant
    for pollutant, concentration in pollutants.items():
        if concentration is not None and concentration >= 0:
            sub_indices[pollutant] = calculate_sub_index(pollutant, concentration)
    
    # Overall AQI is the maximum of all sub-indices
    if sub_indices:
        aqi_value = max(sub_indices.values())
        dominant_pollutant = max(sub_indices, key=sub_indices.get)
    else:
        aqi_value = 0
        dominant_pollutant = None
    
    # Get category info
    category_info = get_category_info(aqi_value)
    
    return {
        "aqi": aqi_value,
        "category": category_info["category"],
        "color": category_info["color"],
        "description": category_info["description"],
        "dominant_pollutant": dominant_pollutant,
        "sub_indices": sub_indices
    }


def get_category_info(aqi_value: int) -> dict:
    """Get category information for a given AQI value."""
    for category in AQI_CATEGORIES:
        if category["min"] <= aqi_value <= category["max"]:
            return category
    
    # Default to Severe if above 500
    if aqi_value > 500:
        return AQI_CATEGORIES[-1]
    
    return AQI_CATEGORIES[0]


def get_health_recommendations(category: str) -> dict:
    """Get health recommendations for a given AQI category."""
    return HEALTH_RECOMMENDATIONS.get(category, HEALTH_RECOMMENDATIONS["Good"])


def format_pollutant_display(pollutant: str) -> dict:
    """Get display information for a pollutant."""
    display_info = {
        "pm25": {"name": "PM2.5", "unit": "µg/m³", "full_name": "Fine Particulate Matter"},
        "pm10": {"name": "PM10", "unit": "µg/m³", "full_name": "Particulate Matter"},
        "no2": {"name": "NO₂", "unit": "µg/m³", "full_name": "Nitrogen Dioxide"},
        "so2": {"name": "SO₂", "unit": "µg/m³", "full_name": "Sulfur Dioxide"},
        "co": {"name": "CO", "unit": "mg/m³", "full_name": "Carbon Monoxide"},
        "o3": {"name": "O₃", "unit": "µg/m³", "full_name": "Ozone"}
    }
    return display_info.get(pollutant, {"name": pollutant.upper(), "unit": "", "full_name": pollutant})


# Health Risk Data by AQI Category
# Structure: { Disease: { AQI_Category: { Risk_Level, Symptoms, Dos, Donts } } }
DISEASE_RISKS = {
    "Headaches": {
        "Good": {"risk": "Low", "symptoms": "None expected.", "dos": ["Enjoy outdoor activities."], "donts": ["No restrictions."]},
        "Satisfactory": {"risk": "Low", "symptoms": "None expected.", "dos": ["Enjoy outdoor activities."], "donts": ["No restrictions."]},
        "Moderate": {"risk": "Mild", "symptoms": "Pressure or tightness around the forehead and temples, Fatigue.", "dos": ["Hydrate and take breaks.", "Favor indoor air if migraine-prone."], "donts": ["Avoid intense outdoor exercise.", "Ignore worsening effects."]},
        "Poor": {"risk": "Moderate", "symptoms": "Frequent headaches, Sinus pressure.", "dos": ["Stay hydrated.", "Use air purifiers."], "donts": ["Prolonged outdoor exposure."]},
        "Very Poor": {"risk": "High", "symptoms": "Severe headaches, Nausea, Dizziness.", "dos": ["Stay indoors.", "Keep windows closed."], "donts": ["Outdoor exercise."]},
        "Severe": {"risk": "Very High", "symptoms": "Intense migraines, Confusion.", "dos": ["Strictly stay indoors.", "Seek medical help if needed."], "donts": ["Going outside without N95 mask."]}
    },
    "Asthma": {
        "Good": {"risk": "Low", "symptoms": "None.", "dos": ["Keep inhaler nearby just in case."], "donts": ["None."]},
        "Satisfactory": {"risk": "Low", "symptoms": "Minor wheezing possible for very sensitive.", "dos": ["Keep inhaler accessible."], "donts": ["None."]},
        "Moderate": {"risk": "Moderate", "symptoms": "Coughing, Shortness of breath.", "dos": ["Keep inhaler ready.", "Limit outdoor exertion."], "donts": ["Heavy outdoor exercise."]},
        "Poor": {"risk": "High", "symptoms": "Chest tightness, Wheezing.", "dos": ["Stay indoors.", "Use air purifier."], "donts": ["Outdoor activities."]},
        "Very Poor": {"risk": "Very High", "symptoms": "Frequent attacks, Difficulty breathing.", "dos": ["Stay strictly indoors.", "Wear N95 if travel is necessary."], "donts": ["Open windows."]},
        "Severe": {"risk": "Critical", "symptoms": "Severe attacks, Respiratory distress.", "dos": ["Stay indoors.", "Consult doctor if symptoms worsen."], "donts": ["Any outdoor exposure."]}
    },
    "Heart Issues": {
        "Good": {"risk": "Low", "symptoms": "None.", "dos": ["Regular exercise."], "donts": ["None."]},
        "Satisfactory": {"risk": "Low", "symptoms": "None.", "dos": ["Regular exercise."], "donts": ["None."]},
        "Moderate": {"risk": "Moderate", "symptoms": "Palpitations in sensitive groups.", "dos": ["Monitor blood pressure.", "Take medication on time."], "donts": ["Strenuous outdoor work."]},
        "Poor": {"risk": "High", "symptoms": "Chest discomfort, Fatigue.", "dos": ["Avoid exertion.", "Stay indoors."], "donts": ["Heavy lifting.", "Outdoor running."]},
        "Very Poor": {"risk": "Very High", "symptoms": "Irregular heartbeat, Breathlessness.", "dos": ["Rest indoors.", "Keep emergency contacts ready."], "donts": ["Stressful activities."]},
        "Severe": {"risk": "Critical", "symptoms": "Chest pain, severe distress.", "dos": ["Complete rest.", "Medical attention if needed."], "donts": ["Any physical exertion."]}
    },
    "Eye Irritation": {
        "Good": {"risk": "Low", "symptoms": "None.", "dos": ["None."], "donts": ["None."]},
        "Satisfactory": {"risk": "Low", "symptoms": "None.", "dos": ["None."], "donts": ["None."]},
        "Moderate": {"risk": "Mild", "symptoms": "Slight itching or redness.", "dos": ["Wash eyes with water.", "Wear sunglasses."], "donts": ["Rubbing eyes."]},
        "Poor": {"risk": "Moderate", "symptoms": "Watery eyes, Burning sensation.", "dos": ["Use lubricating eye drops.", "Wear protective glasses."], "donts": ["Contact lenses if irritated."]},
        "Very Poor": {"risk": "High", "symptoms": "Redness, Swelling, Blurred vision.", "dos": ["Cold compress.", "Stay indoors."], "donts": ["Exposure to dust/smoke."]},
        "Severe": {"risk": "Very High", "symptoms": "Severe burning, discharge.", "dos": ["Consult eye specialist.", "Stay in filtered air."], "donts": ["Touching eyes with unclean hands."]}
    },
    "Pregnancy & Infants": {
         "Good": {"risk": "Low", "symptoms": "None.", "dos": ["Walks and fresh air."], "donts": ["None."]},
         "Satisfactory": {"risk": "Low", "symptoms": "None.", "dos": ["Normal activities."], "donts": ["None."]},
         "Moderate": {"risk": "Moderate", "symptoms": "Mild fatigue.", "dos": ["Reduce long walks outside.", "Hydrate well."], "donts": ["Heavy exertion."]},
         "Poor": {"risk": "High", "symptoms": "Coughing, Fatigue.", "dos": ["Stay indoors.", "Use air purifier."], "donts": ["Outdoor parks/playgrounds."]},
         "Very Poor": {"risk": "Very High", "symptoms": "Breathing difficulty.", "dos": ["Strictly indoors.", "Consult doctor for any symptom."], "donts": ["Any outdoor exposure."]},
         "Severe": {"risk": "Critical", "symptoms": "High risk of complications.", "dos": ["Create clean room at home.", "Medical checkups."], "donts": ["Going out."]}
    }
}

def get_health_risks(category: str) -> dict:
    """
    Get health risks for the given AQI category.
    Returns a dictionary of diseases with their specific risk details.
    """
    # Map category names to keys in DISEASE_RISKS (Handle slight varieties if any)
    # Assuming exact match for now as categories are standard
    
    risk_report = {}
    for disease, categories in DISEASE_RISKS.items():
        details = categories.get(category, categories.get("Moderate")) # Fallback
        risk_report[disease] = details
        
    return risk_report
