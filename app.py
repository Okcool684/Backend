from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import datetime

app = Flask(__name__)
CORS(app)

USER_DATA = {
    "favorites": set(),
    "recent_searches": []
}

COMPANY_LIST = []

def load_sp500_companies():
    import pandas as pd
    global COMPANY_LIST
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
        COMPANY_LIST = companies
    except Exception as e:
        print(f"Error loading companies: {e}")
        COMPANY_LIST = []

def get_date_n_days_ago(n):
    d = datetime.date.today() - datetime.timedelta(days=n)
    return d.isoformat()

def get_date_today():
    return datetime.date.today().isoformat()

@app.route("/api/companies")
def companies():
    search = request.args.get("search", "").lower()
    if not COMPANY_LIST:
        load_sp500_companies()
    filtered = []
    if search == "":
        filtered = COMPANY_LIST[:50]
    else:
        filtered = [c for c in COMPANY_LIST if search in c["symbol"].lower() or search in c["name"].lower()]

    symbols = [c["symbol"] for c in filtered[:50]]
    prices_map = {}
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            try:
                info = tickers.tickers[sym].info
                price = info.get("regularMarketPrice")
                prices_map[sym] = round(price, 2) if price else None
            except:
                prices_map[sym] = None
    except:
        prices_map = {}

    result = []
    for company in filtered[:50]:
        comp = company.copy()
        comp["livePrice"] = prices_map.get(comp["symbol"])
        result.append(comp)

    s_upper = search.upper()
    if search and s_upper not in USER_DATA["recent_searches"]:
        USER_DATA["recent_searches"].append(s_upper)
        if len(USER_DATA["recent_searches"]) > 20:
            USER_DATA["recent_searches"].pop(0)

    return jsonify(result)

@app.route("/api/favorites", methods=["GET", "POST"])
def favorites():
    if request.method == "GET":
        return jsonify(list(USER_DATA["favorites"]))
    else:
        data = request.get_json()
        favs = data.get("favorites", [])
        USER_DATA["favorites"] = set(favs)
        return jsonify({"success": True, "favorites": list(USER_DATA["favorites"])})

@app.route("/api/news")
def news():
    news_list = []
    for symbol in USER_DATA["favorites"]:
        ticker = yf.Ticker(symbol)
        try:
            news_data = ticker.news
            if not news_data:
                continue
            for item in news_data[:10]:
                news_list.append({
                    "newsId": item.get("uuid", "") or item.get("id", "") or str(item.get("datetime", "")),
                    "company": symbol,
                    "headline": item.get("title", ""),
                    "content": item.get("summary", ""),
                    "timestamp": datetime.datetime.utcfromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else "",
                    "url": item.get("link", ""),
                    "category": "News"
                })
        except:
            continue
    news_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify(news_list[:50])

@app.route("/api/alerts")
def alerts():
    alert_list = []
    for symbol in USER_DATA["favorites"]:
        ticker = yf.Ticker(symbol)
        try:
            change_pct = ticker.info.get("regularMarketChangePercent") or 0
            volume = ticker.info.get("volume") or 0
            if abs(change_pct) >= 3:
                alert_list.append({
                    "alertId": f"{symbol}_alert",
                    "company": symbol,
                    "priceChange": change_pct,
                    "volume": volume,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })
        except:
            continue
    return jsonify(alert_list)

@app.route("/api/recent-searches")
def recent_searches():
    return jsonify(USER_DATA["recent_searches"][-5:])

@app.route("/api/recommendations")
def recommendations():
    exclude = USER_DATA["favorites"].union(set(USER_DATA["recent_searches"]))
    recommended = [c for c in COMPANY_LIST if c["symbol"] not in exclude and c["category"] == "Technology"]
    return jsonify(recommended[:5])

if __name__ == "__main__":
    load_sp500_companies()
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
