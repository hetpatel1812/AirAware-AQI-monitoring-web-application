# 🌬️AirAware — India AQI Dashboard

A comprehensive **Air Quality Index (AQI) monitoring web application** for Indian cities. Built with Flask, AirAware provides pollutant data, weather information, an interactive map, AQI-related news, and an AI-powered chatbot — all wrapped in a modern, animated UI.
    
---  

## ✨ Features

### 🏠 AQI Dashboard (Home)

* Real-time AQI display with an animated gauge for any Indian city
* 6-pollutant breakdown: **PM2.5, PM10, NO₂, SO₂, CO, O₃**
* Dominant pollutant detection using CPCB India formula
* **Cigarette equivalence metric**
  *(Berkeley Earth estimate: 1 cigarette ≈ 22 µg/m³ PM2.5)*
* Health impact card with risk levels and smart solutions
  * Air purifier guidance
  * N95 mask suggestions
  * Car air filtration awareness
  * Stay-indoors recommendations
* 24-hour historical AQI trend chart
* Hourly weather forecast (temperature, humidity, wind, conditions)
* Dynamic AQI character visuals based on air quality level
* City search with autocomplete (fuzzy matching across 100+ cities)

---

### 🗺️ Live AQI Map

* Interactive India map with city-level AQI markers
* Color-coded AQI categories
* Powered by Leaflet.js

---

### 📰 AQI News

* Latest India air quality news feed
* NewsData.io integration with caching for performance

---

### 🤖 Chatbot — “Namaste Air”

* Intent-based chatbot trained with TF-IDF + LinearSVC
* Context-aware responses using city AQI state
* Natural response delay for conversational feel
* Click-away auto-close behavior

---

### 📄 Additional Pages

| Page             | Route             |
| ---------------- | ----------------- |
| About            | `/about`          |
| India Overview   | `/india-overview` |
| FAQ              | `/faq`            |
| Contact          | `/contact`        |
| Privacy Policy   | `/privacy`        |
| Terms of Service | `/terms`          |

---

### ⚡ Performance & UX

* Static asset caching (1-year max-age)
* In-memory API caching
* Ambient particle animation
* Scroll-reveal micro-interactions
* Fully responsive design

---

## 🛠️ Tech Stack

| Layer      | Technology                        |
| ---------- | --------------------------------- |
| Backend    | Python 3, Flask                   |
| AQI Data   | City demo dataset fallback        |
| News API   | NewsData.io                       |
| Chatbot ML | scikit-learn (TF-IDF + LinearSVC) |
| Frontend   | HTML, CSS, JavaScript             |
| Maps       | Leaflet.js                        |
| Charts     | Chart.js                          |
| Icons      | Google Material Symbols           |
| Fonts      | Google Fonts                      |

---

## 📁 Project Structure

```
AirAware/
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   └── states_cities.json
│
├── model/
│   ├── intents.json
│   ├── train_model.py
│   ├── chatbot_model.pkl
│   └── vectorizer.pkl
│
├── utils/
│   ├── __init__.py
│   ├── aqi_calculator.py
│   ├── data_fetcher.py
│   └── news_fetcher.py
│
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   ├── js/maps.js
│   ├── js/news.js
│   ├── js/particles.js
│   └── images/  (all your images)
│
├── templates/
│   └── (all .html files)
│
└── tests/
    ├── test_chatbot.py
    └── test_map_data.py

```

---

## 🚀 Setup & Installation

### 1. Clone the repository

```
git clone https://github.com/hetpatel1812/AirAware-AQI-monitoring-web-application.git
cd AirAware
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

If needed:

```
pip install scikit-learn
```

### 3. API Keys

Configure your NewsData.io API key inside:

```
utils/news_fetcher.py
```

### 4. (Optional) Retrain chatbot

```
python model/train_model.py
```

### 5. Run the app

```
python app.py
```

Visit:

```
http://localhost:5000
```

---

## 🔌 API Endpoints

| Method | Endpoint          | Description       |
| ------ | ----------------- | ----------------- |
| GET    | `/`               | Default dashboard |
| GET    | `/in/<city-slug>` | City AQI page     |
| GET    | `/maps`           | Live map          |
| GET    | `/news`           | AQI news          |
| GET    | `/india-overview` | India overview    |
| GET    | `/api/aqi/<city>` | AQI JSON          |
| GET    | `/api/search`     | City search       |
| GET    | `/api/map-data`   | Map AQI data      |
| POST   | `/api/chat`       | Chatbot response  |

Example chatbot payload:

```json
{
  "message": "What is the AQI in Delhi?",
  "context": {
    "city": "Delhi",
    "aqi": 312,
    "category": "Very Poor"
  }
}
```

---

## 🌆 Supported Cities

100+ Indian cities including NCR regions, metros, regional centers, and hill stations.

---

## 📊 AQI Categories (CPCB Standard)

| AQI Range | Category     |
| --------- | ------------ |
| 0–50      | Good         |
| 51–100    | Satisfactory |
| 101–200   | Moderate     |
| 201–300   | Poor         |
| 301–400   | Very Poor    |
| 401–500   | Severe       |

---

## 🙏 Acknowledgments

This project builds upon several open-source technologies:

* Flask — web framework
* scikit-learn — machine learning toolkit
* Leaflet.js — interactive maps
* Chart.js — visualization engine
* Google Fonts & Material Symbols — UI assets

Development and refinement were assisted by AI tools such as ChatGPT, Claude, and Gemini. These tools were used strictly as development aids; final design and implementation decisions remain with the project author.

---

## 📝 License

This project is licensed under the **MIT License**.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software, provided that the original copyright notice and permission notice are included in all copies or substantial portions of the software.

See the `LICENSE` file in this repository for the complete license text.




