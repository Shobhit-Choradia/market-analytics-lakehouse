import requests
import os
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
# Find workspace root relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

load_dotenv(os.path.join(ROOT_DIR, ".env"))
API_KEY = os.getenv("MARKETAUX_API_KEY")
OUTPUT_DIR = os.path.join(ROOT_DIR, "landing_data/news")
TICKERS_TO_QUERY = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google OR Alphabet",
    "AMZN": "Amazon", "TSLA": "Tesla"
}

def fetch_news(company_map):
    if not API_KEY or API_KEY.strip() == "" or API_KEY == "your_marketaux_api_key_here":
        raise ValueError(
            "MARKETAUX_API_KEY is not configured. Please set a valid Marketaux API key in your .env file."
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    from_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    for ticker, query in company_map.items():
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "symbols": ticker,
            "filter_entities": "true",
            "published_after": from_date,
            "language": "en",
            "limit": 25,
            "api_token": API_KEY,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        articles = payload.get("data", [])
        for a in articles:
            a["ticker"] = ticker
            a["ingested_at_utc"] = datetime.now(timezone.utc).isoformat()

        out_path = f"{OUTPUT_DIR}/{ticker}_{run_ts}.json"
        with open(out_path, "w") as f:
            json.dump(articles, f)
        print(f"[OK] Wrote {len(articles)} articles for {ticker} -> {out_path}")

if __name__ == "__main__":
    fetch_news(TICKERS_TO_QUERY)