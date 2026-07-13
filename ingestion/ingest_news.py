import requests
import os
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Find workspace root relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "ingestion.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Starting news ingestion for {len(company_map)} companies.")

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
        
        max_retries = 3
        articles = []
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, timeout=15)
                resp.raise_for_status()
                payload = resp.json()
                articles = payload.get("data", [])
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch news for {ticker} after {max_retries} attempts.")

        if not articles:
            logger.warning(f"No news returned for {ticker}")
            continue

        for a in articles:
            a["ticker"] = ticker
            a["ingested_at_utc"] = datetime.now(timezone.utc).isoformat()

        out_path = f"{OUTPUT_DIR}/{ticker}_{run_ts}.json"
        with open(out_path, "w") as f:
            json.dump(articles, f)
        logger.info(f"Wrote {len(articles)} articles for {ticker} -> {out_path}")
        
    logger.info("Finished news ingestion.")

if __name__ == "__main__":
    fetch_news(TICKERS_TO_QUERY)