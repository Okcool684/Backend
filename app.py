
import datetime
import requests
import os
os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"
# Create the cache directory for yfinance
os.makedirs("/tmp/.cache/py-yfinance", exist_ok=True)

import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Replace with your NewsAPI key (https://newsapi.org/)
NEWSAPI_KEY = "161644ecac3746edbf8da10031aa6c70"

USER_DATA = {
    "favorites": set(),
    "recent_searches": []
}

# Load company list (S&P 500) once on startup, from Wikipedia
import pandas as pd

def load_companies():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        companies = []
        for _, row in df.iterrows():
            companies.append({
                "symbol": row["Symbol"],
                "name": row["Security"],
                "category": row.get("GICS Sector", "Unknown")
            })
        return companies
    except Exception as e:
        print(f"Error loading companies: {e}")
        return []

COMPANY_LIST = load_companies()

@app.route("/api/companies")
def companies():
    query = request.args.get("search", "").lower()
    if query == "":
        filtered = COMPANY_LIST[:50]
    else:
        filtered = [c for c in COMPANY_LIST if query in c["symbol"].lower() or query in c["name"].lower()]

    symbols = [c["symbol"] for c in filtered[:50]]
    prices = {}
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for symbol in symbols:
            info = tickers.tickers[symbol].info
            price = info.get("regularMarketPrice")
            prices[symbol] = round(price, 2) if price else None
    except Exception:
        prices = {s: None for s in symbols}

    # Append live price
    for c in filtered[:50]:
        c["livePrice"] = prices.get(c["symbol"])

    # Track recent searches
    q_upper = query.upper()
    if query and q_upper not in USER_DATA["recent_searches"]:
        USER_DATA["recent_searches"].append(q_upper)
        if len(USER_DATA["recent_searches"]) > 20:
            USER_DATA["recent_searches"].pop(0)

    return jsonify(filtered[:50])

@app.route("/api/favorites", methods=["GET", "POST"])
def favorites():
    if request.method == "GET":
        return jsonify(list(USER_DATA["favorites"]))
    else:
        data = request.get_json()
        favs = data.get("favorites", [])
        USER_DATA["favorites"] = set(favs)
        return jsonify({"success": True, "favorites": list(USER_DATA["favorites"])})

def get_news_for_symbol(symbol):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": symbol,
        "apiKey": NEWSAPI_KEY,
        "pageSize": 10,
        "sortBy": "publishedAt",
        "language": "en"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        print(f"News fetch error for {symbol}: {e}")
        return []

@app.route("/api/news")
def news():
    news_list = []
    for symbol in USER_DATA["favorites"]:
        articles = get_news_for_symbol(symbol)
        for item in articles:
            news_list.append({
                "newsId": item.get("url"),
                "company": symbol,
                "headline": item.get("title"),
                "content": item.get("description") or "",
                "timestamp": item.get("publishedAt"),
                "url": item.get("url"),
                "category": "News"
            })
    news_list = sorted(news_list, key=lambda x: x["timestamp"] or "", reverse=True)
    return jsonify(news_list[:50])

@app.route("/api/alerts")
def alerts():
    alerts_list = []
    for symbol in USER_DATA["favorites"]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price_change = info.get("regularMarketChangePercent") or 0
            volume = info.get("volume") or 0
            if abs(price_change) >= 3:
                alerts_list.append({
                    "alertId": f"{symbol}_alert",
                    "company": symbol,
                    "priceChange": price_change,
                    "volume": volume,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })
        except Exception as e:
            print(f"Error getting alert for {symbol}: {e}")
    return jsonify(alerts_list)

@app.route("/api/recent-searches")
def recent_searches():
    return jsonify(USER_DATA["recent_searches"][-5:])

@app.route("/api/recommendations")
def recommendations():
    exclude = USER_DATA["favorites"].union(set(USER_DATA["recent_searches"]))
    recs = [c for c in COMPANY_LIST if c["symbol"] not in exclude and "Technology" in c["category"]]
    return jsonify(recs[:5])

@app.route("/api/company-details/<symbol>")
def company_details(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        details = {
            "symbol": info.get("symbol"),
            "shortName": info.get("shortName"),
            "regularMarketPrice": info.get("regularMarketPrice"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "trailingEps": info.get("trailingEps"),
            "dividendYield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "website": info.get("website"),
            "longBusinessSummary": info.get("longBusinessSummary"),
        }
        return jsonify(details)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
