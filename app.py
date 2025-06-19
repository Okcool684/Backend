# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from agno import Agent, Tool
import yfinance as yf
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# ========== AGNO TOOL for Financials ==========
def get_financials(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "symbol": symbol,
        "shortName": info.get("shortName"),
        "regularMarketPrice": info.get("regularMarketPrice"),
        "marketCap": info.get("marketCap"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
        "trailingPE": info.get("trailingPE"),
        "trailingEps": info.get("trailingEps"),
        "dividendYield": info.get("dividendYield"),
        "sector": info.get("sector")
    }

financials_tool = Tool(
    name="StockFinancials",
    func=get_financials,
    description="Get financial data for a stock by symbol."
)

agent = Agent(tools=[financials_tool])

# ========== GEMINI SETUP (News Summary) ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

def get_news_summary(company_name):
    prompt = f"Provide a real-time summary of the latest news and market sentiment for {company_name}."
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not fetch summary: {str(e)}"

# ========== API ROUTES ==========
FAVORITES = set()
RECENT_SEARCHES = []

@app.route("/api/companies")
def get_companies():
    query = request.args.get("search", "").lower()
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    company_names = ["Apple Inc.", "Alphabet Inc.", "Microsoft Corp.", "Amazon.com", "Tesla Inc."]
    categories = ["Technology"] * 5
    companies = [
        {"symbol": s, "name": n, "category": c} for s, n, c in zip(symbols, company_names, categories)
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
    details = get_financials(symbol)
    if symbol not in RECENT_SEARCHES:
        RECENT_SEARCHES.append(symbol)
    return jsonify(details)

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

