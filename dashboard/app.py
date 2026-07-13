import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from databricks import sql
import os

st.set_page_config(page_title="Market Analytics", layout="wide")

@st.cache_resource
def get_connection():
    return sql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"].replace("https://", ""),
        http_path=st.secrets["DATABRICKS_WAREHOUSE_HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"],
    )

@st.cache_data(ttl=3600)
def load_data(ticker: str) -> pd.DataFrame:
    conn = get_connection()
    query = f"""
        SELECT * FROM market_analytics.gold.market_analytics_daily
        WHERE ticker = '{ticker}'
        ORDER BY trade_date
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall_arrow().to_pandas()

st.title("📊 Hybrid Market Analytics Dashboard")

ticker = st.sidebar.selectbox("Select ticker", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
df = load_data(ticker)

if df.empty:
    st.warning("No data yet for this ticker — run the pipeline first.")
else:
    col1, col2, col3 = st.columns(3)
    latest = df.iloc[-1]
    col1.metric("Close Price", f"${latest['close_price']:.2f}")
    col2.metric("RSI (14)", f"{latest['rsi_14']:.1f}" if pd.notna(latest["rsi_14"]) else "n/a")
    col3.metric("Avg Sentiment (VADER)", f"{latest['avg_vader_compound']:.2f}" if pd.notna(latest["avg_vader_compound"]) else "n/a")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["trade_date"], y=df["close_price"], name="Close"))
    fig.add_trace(go.Scatter(x=df["trade_date"], y=df["sma_20"], name="SMA 20"))
    fig.add_trace(go.Scatter(x=df["trade_date"], y=df["bollinger_upper"], name="Bollinger Upper", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=df["trade_date"], y=df["bollinger_lower"], name="Bollinger Lower", line=dict(dash="dot")))
    fig.update_layout(title=f"{ticker} Price & Technicals", height=500)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df["trade_date"], y=df["avg_vader_compound"], name="Daily Sentiment"))
    fig2.update_layout(title="Daily News Sentiment (VADER compound)", height=300)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Underlying data")
    st.dataframe(df, use_container_width=True)