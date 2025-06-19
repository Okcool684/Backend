# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve
from agno import Agent
from agno.tools.yfinance import YFinanceTools
import os
import datetime

app = Flask(__name__)
CORS(app)

# Initialize Agno agent with YFinanceTools
agent = Agent(tools=[YFinanceTools()])

# In-memory user data (replace with DB for production)
USER_DATA = {
    "favorites": set(),
    "recent_searches": [],
}

# Gemini news API key (set in env variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_gemini_news(symbols):
    # Dummy example, replace with real Gemini API call
    # Example: call Gemini with your API key and symbols to get news
    # Return list of dicts with news data
    # For demo, return mock data:
    news = []
    for sym in symbols:
        news.append({
            "newsId": f"{sym}-1",
            "company": sym,
            "headline": f"Latest news headline for {sym}",
            "content": f"News content about {sym} ...",
            "timestamp": datetime.datetime.utcnow().isoformat(),
        })
    return news

def fetch_gemini_alerts(symbols):
    # Dummy example, replace with real Gemini alerts API call
    alerts = []
    for sym in symbols:
        alerts.append({
            "alertId": f"{sym}-1",
            "company": sym,
            "priceChange": 1.2,
            "volume": 123456,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        })
    return alerts

@app.route("/api/companies")
def get_companies():
    # Use YFinanceTools agent to fetch company list
    # The YFinanceTools agent supports get_companies
    try:
        response = agent.query("list_companies")  # 'list_companies' is Agno's command for company list
        # Response parsing might depend on Agno's exact return format
        companies = response.get("companies") or response.get("data") or []
        # companies expected as list of dicts: {symbol, name, category}
        return jsonify(companies)
    except Exception as e:
        print("Error fetching companies:", e)
        return jsonify([]), 500

@app.route("/api/company-details/<symbol>")
def get_company_details(symbol):
    # Use agent to fetch detailed financial info
    try:
        query = f"get_company_financials:{symbol}"
        response = agent.query(query)
        # Parse and return relevant details (depends on Agno output format)
        details = response.get("financials") or response.get("data") or {}
        if not details:
            return jsonify({"error": "Details not found"}), 404
        return jsonify(details)
    except Exception as e:
        print(f"Error fetching details for {symbol}:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/favorites", methods=["GET", "POST"])
def favorites():
    if request.method == "GET":
        return jsonify(list(USER_DATA["favorites"]))
    if request.method == "POST":
        data = request.get_json()
        favorites = set(data.get("favorites", []))
        USER_DATA["favorites"] = favorites
        return jsonify({"success": True, "favorites": list(favorites)})

@app.route("/api/recent-searches")
def recent_searches():
    return jsonify(USER_DATA["recent_searches"])

@app.route("/api/news")
def news():
    favs = USER_DATA["favorites"]
    if not favs:
        return jsonify([])
    try:
        news_items = fetch_gemini_news(favs)
        return jsonify(news_items)
    except Exception as e:
        print("Error fetching news:", e)
        return jsonify([]), 500

@app.route("/api/alerts")
def alerts():
    favs = USER_DATA["favorites"]
    if not favs:
        return jsonify([])
    try:
        alert_items = fetch_gemini_alerts(favs)
        return jsonify(alert_items)
    except Exception as e:
        print("Error fetching alerts:", e)
        return jsonify([]), 500

if __name__ == "__main__":
    # For local dev:
    # app.run(host="0.0.0.0", port=5000, debug=True)

    # For production with waitress:
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
