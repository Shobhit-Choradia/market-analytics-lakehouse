import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import os
import json
import logging
import time

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
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

OUTPUT_DIR = os.path.join(ROOT_DIR, "landing_data/prices")

def fetch_prices(tickers, period="5d", interval="1d"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    logger.info(f"Starting price ingestion for {len(tickers)} tickers.")

    for ticker in tickers:
        max_retries = 3
        df = pd.DataFrame()
        for attempt in range(max_retries):
            try:
                df = yf.download(ticker, period=period, interval=interval, progress=False)
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch data for {ticker} after {max_retries} attempts.")

        if df is None or df.empty:
            logger.warning(f"No data returned for {ticker}")
            continue

        df = df.reset_index()
        df["ticker"] = ticker
        df["ingested_at_utc"] = datetime.now(timezone.utc).isoformat()

        out_path = f"{OUTPUT_DIR}/{ticker}_{run_ts}.json"
        df.to_json(out_path, orient="records", date_format="iso")
        logger.info(f"Wrote {len(df)} rows for {ticker} -> {out_path}")

    logger.info("Finished price ingestion.")

if __name__ == "__main__":
    fetch_prices(TICKERS)