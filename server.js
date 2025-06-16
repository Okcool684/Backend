const express = require("express");
const cors = require("cors");
const fetch = require("node-fetch");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;
const FINNHUB_API_KEY = "d18643pr01ql1b4m1sqgd18643pr01ql1b4m1sr0";

// Static company list with categories - extend as needed
const COMPANY_LIST = [
  { symbol: "AAPL", name: "Apple Inc.", category: "Technology" },
  { symbol: "TSLA", name: "Tesla, Inc.", category: "Automotive" },
  { symbol: "MSFT", name: "Microsoft Corporation", category: "Technology" },
  { symbol: "JNJ", name: "Johnson & Johnson", category: "Healthcare" },
  { symbol: "JPM", name: "JPMorgan Chase & Co.", category: "Financial" },
  { symbol: "PFE", name: "Pfizer Inc.", category: "Healthcare" },
  { symbol: "GOOGL", name: "Alphabet Inc.", category: "Technology" },
  { symbol: "AMZN", name: "Amazon.com, Inc.", category: "Consumer Discretionary" },
  { symbol: "BAC", name: "Bank of America Corporation", category: "Financial" },
  { symbol: "NFLX", name: "Netflix, Inc.", category: "Communication Services" },
];

// In-memory user data (single user)
const USER_DATA = {
  favorites: new Set(["AAPL", "TSLA"]),
  recentSearches: [],
  notifications: {}, // symbol to boolean
};

// Mock news and alerts
const NEWS = [
  { newsId: "1", company: "AAPL", headline: "Apple Reports Record Earnings", content: "Apple Inc. reported a record revenue of $100 billion last quarter.", timestamp: "2023-10-01T12:00:00Z", category: "Finance" },
  { newsId: "2", company: "TSLA", headline: "Tesla Announces New Model", content: "Tesla has unveiled its latest electric vehicle with innovative features.", timestamp: "2023-10-02T14:00:00Z", category: "Technology" },
  { newsId: "3", company: "JNJ", headline: "Johnson & Johnson Expands Vaccine Research", content: "J&J is investing over $500 million in new vaccine technologies.", timestamp: "2023-10-03T10:15:00Z", category: "Healthcare" },
];

const ALERTS = [
  { alertId: "1", company: "AAPL", priceChange: 4.5, volume: 1500000, timestamp: "2023-10-01T12:00:00Z" },
  { alertId: "2", company: "TSLA", priceChange: 3.8, volume: 2000000, timestamp: "2023-10-02T15:30:00Z" },
];

// Helper: fetch real-time quote from Finnhub
async function fetchFinnhubQuote(symbol) {
  const url = `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(symbol)}&token=${FINNHUB_API_KEY}`;
  try {
    const response = await fetch(url);
    const data = await response.json();
    if (data && typeof data.c === "number") {
      // c: current price
      return data.c.toFixed(2);
    }
  } catch (err) {
    console.error("Error fetching quote:", err);
  }
  return null;
}

// Search companies autocomplete with live prices
app.get("/api/companies", async (req, res) => {
  const search = (req.query.search || "").toLowerCase().trim();
  if (!search) return res.json([]);

  // Filter companies by symbol or name includes search
  const filtered = COMPANY_LIST.filter(
    (c) => c.symbol.toLowerCase().startsWith(search) || c.name.toLowerCase().includes(search)
  ).slice(0, 10);

  // Fetch prices concurrently to avoid serial delay
  const prices = await Promise.all(filtered.map((c) => fetchFinnhubQuote(c.symbol)));

  // Build response with live prices included
  const result = filtered.map((c, idx) => ({
    symbol: c.symbol,
    name: c.name,
    category: c.category,
    livePrice: prices[idx],
  }));

  // Update recent searches (keep max 10)
  if (!USER_DATA.recentSearches.includes(search.toUpperCase())) {
    USER_DATA.recentSearches.push(search.toUpperCase());
    if (USER_DATA.recentSearches.length > 10) USER_DATA.recentSearches.shift();
  }

  res.json(result);
});

// Get user's favorite stock symbols
app.get("/api/favorites", (req, res) => {
  res.json(Array.from(USER_DATA.favorites));
});

// Update user's favorite stock symbols
app.post("/api/favorites", (req, res) => {
  const { favorites } = req.body;
  if (!Array.isArray(favorites)) {
    return res.status(400).json({ success: false, message: "Favorites must be an array" });
  }
  USER_DATA.favorites = new Set(favorites);
  res.json({ success: true, favorites: Array.from(USER_DATA.favorites) });
});

// Get news for user's favorites
app.get("/api/news", (req, res) => {
  const favSet = USER_DATA.favorites;
  const filteredNews = NEWS.filter((n) => favSet.has(n.company));
  filteredNews.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  res.json(filteredNews);
});

// Get alerts for user's favorites (priceChange >=3%)
app.get("/api/alerts", (req, res) => {
  const favSet = USER_DATA.favorites;
  const filteredAlerts = ALERTS.filter((a) => favSet.has(a.company) && a.priceChange >= 3);
  filteredAlerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  res.json(filteredAlerts);
});

// Get recent searches (last 5)
app.get("/api/recent-searches", (req, res) => {
  res.json(USER_DATA.recentSearches.slice(-5));
});

// Get recommended stocks (companies not favorite nor recent, up to 5)
app.get("/api/recommendations", (req, res) => {
  const exclude = new Set([...USER_DATA.favorites, ...USER_DATA.recentSearches]);
  const recommended = COMPANY_LIST.filter((c) => !exclude.has(c.symbol) && c.category === "Technology").slice(0, 5);
  res.json(recommended);
});

app.listen(PORT, () => {
  console.log(`Backend running on port ${PORT}`);
});
