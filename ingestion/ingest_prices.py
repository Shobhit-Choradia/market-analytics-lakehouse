import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import os
import json

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
OUTPUT_DIR = os.path.join(ROOT_DIR, "landing_data/news")

def fetch_prices(tickers, period="5d", interval="1d"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    for ticker in tickers:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            print(f"[WARN] No data returned for {ticker}")
            continue

        df = df.reset_index()
        df["ticker"] = ticker
        df["ingested_at_utc"] = datetime.now(timezone.utc).isoformat()

        out_path = f"{OUTPUT_DIR}/{ticker}_{run_ts}.json"
        df.to_json(out_path, orient="records", date_format="iso")
        print(f"[OK] Wrote {len(df)} rows for {ticker} -> {out_path}")

if __name__ == "__main__":
    fetch_prices(TICKERS)