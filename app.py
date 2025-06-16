from flask import Flask, jsonify, request
import yfinance as yf
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

# In-memory favorites and recent searches (no DB for simplicity)
favorites = set()
recent_searches = []

# Company list for autocomplete (this can be extended)
COMPANY_LIST = [
    {"symbol": "AAPL", "name": "Apple Inc.", "category": "Technology"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "category": "Automotive"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "category": "Technology"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "category": "Healthcare"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "category": "Financial"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "category": "Healthcare"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "category": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "category": "Consumer Discretionary"},
    {"symbol": "BAC", "name": "Bank of America Corporation", "category": "Financial"},
    {"symbol": "NFLX", "name": "Netflix, Inc.", "category": "Communication Services"},
]

@app.route("/api/companies")
def companies():
    search = request.args.get("search", "").lower()
    filtered = [c for c in COMPANY_LIST if search in c["symbol"].lower() or search in c["name"].lower()]
    # Fetch prices with yfinance
    for c in filtered:
        ticker = yf.Ticker(c["symbol"])
        try:
            price = ticker.info.get("regularMarketPrice")
            c["livePrice"] = round(price, 2) if price else None
        except:
            c["livePrice"] = None
    # Update recent searches
    if search and search.upper() not in recent_searches:
        recent_searches.append(search.upper())
        if len(recent_searches) > 10:
            recent_searches.pop(0)
    return jsonify(filtered)

@app.route("/api/favorites", methods=["GET", "POST"])
def favorite_stocks():
    global favorites
    if request.method == "GET":
        return jsonify(list(favorites))
    else:
        data = request.get_json()
        new_favs = data.get("favorites", [])
        favorites = set(new_favs)
        return jsonify({"success": True, "favorites": list(favorites)})

@app.route("/api/news")
def news():
    # For demo, fetch latest news for each favorite using yfinance news attribute or mock news
    news_items = []
    for sym in favorites:
        ticker = yf.Ticker(sym)
        try:
            # yfinance does not provide news in all versions, so this is just a placeholder:
            # Use your own source or API for real news.
            info = ticker.info
            news_items.append({
                "newsId": sym + "_1",
                "company": sym,
                "headline": f"{info.get('shortName', sym)} latest update",
                "content": info.get('longBusinessSummary', 'No summary available.'),
                "timestamp": datetime.datetime.now().isoformat(),
                "category": info.get("sector", "General"),
                "url": info.get("website", "")
            })
        except:
            continue
    return jsonify(news_items)

@app.route("/api/alerts")
def alerts():
    # Generate mock alerts for favorites
    alerts_list = []
    for sym in favorites:
        ticker = yf.Ticker(sym)
        try:
            price_change = ticker.info.get("regularMarketChangePercent", 0)
            volume = ticker.info.get("volume", 0)
            if abs(price_change) >= 3:
                alerts_list.append({
                    "alertId": sym + "_alert",
                    "company": sym,
                    "priceChange": price_change,
                    "volume": volume,
                    "timestamp": datetime.datetime.now().isoformat()
                })
        except:
            continue
    return jsonify(alerts_list)

@app.route("/api/recent-searches")
def recent():
    return jsonify(recent_searches[-5:])

@app.route("/api/recommendations")
def recommendations():
    # Recommend stocks not in favorites or recent searches, in Technology category
    exclude = favorites.union(set(recent_searches))
    recs = [c for c in COMPANY_LIST if c["symbol"] not in exclude and c["category"] == "Technology"]
    return jsonify(recs[:5])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
