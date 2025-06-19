# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import os
import google.generativeai as genai
from agno.agent import Agent
from agno.tools.yfinance import YFinanceTools

app = Flask(__name__)
CORS(app)

# ========== GEMINI SETUP ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-pro")

# ========== AGNO SETUP ==========
yf_tools = YFinanceTools(stock_price=True, company_info=True)
agent = Agent(model=gemini_model, tools=[yf_tools])

# ========== UTILS ==========
FAVORITES = set()
RECENT_SEARCHES = []

# Helper function for Gemini summary
def get_news_summary(company_name):
    prompt = f"Provide a real-time summary of the latest news and market sentiment for {company_name}."
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not fetch summary: {str(e)}"

# ========== API ROUTES ==========
@app.route("/api/companies")
def get_companies():
    query = request.args.get("search", "").lower()
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    names = ["Apple Inc.", "Alphabet Inc.", "Microsoft Corp.", "Amazon.com", "Tesla Inc."]
    categories = ["Technology"] * 5
    companies = [
        {"symbol": s, "name": n, "category": c} for s, n, c in zip(symbols, names, categories)
    ]
    if query:
        companies = [c for c in companies if query in c["symbol"].lower() or query in c["name"].lower()]
    return jsonify(companies)

@app.route("/api/favorites", methods=["GET", "POST"])
def handle_favorites():
    global FAVORITES
    if request.method == "POST":
        FAVORITES = set(request.json.get("favorites", []))
        return jsonify({"success": True, "favorites": list(FAVORITES)})
    return jsonify(list(FAVORITES))

@app.route("/api/recent-searches")
def recent_searches():
    return jsonify(RECENT_SEARCHES[-10:])

@app.route("/api/recommendations")
def recommendations():
    return jsonify(["AAPL", "MSFT", "GOOGL"])  # Dummy list

@app.route("/api/company-details/<symbol>")
def company_details(symbol):
    try:
        result = agent.run(f"Get financial details for {symbol}")
        if symbol not in RECENT_SEARCHES:
            RECENT_SEARCHES.append(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/news")
def get_news():
    if not FAVORITES:
        return jsonify([])
    return jsonify([
        {
            "company": symbol,
            "headline": f"Latest update on {symbol}",
            "content": get_news_summary(symbol),
            "timestamp": str(request.args.get("timestamp", "2025-06-19T12:00:00Z")),
            "newsId": f"news-{symbol}"
        }
        for symbol in FAVORITES
    ])

@app.route("/api/alerts")
def alerts():
    return jsonify([
        {
            "company": s,
            "priceChange": round(2.5, 2),
            "volume": 1250000,
            "timestamp": "2025-06-19T12:00:00Z",
            "alertId": f"alert-{s}"
        }
        for s in FAVORITES
    ])

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
