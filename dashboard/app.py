import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from databricks import sql
import os

st.set_page_config(page_title="Market Analytics", layout="wide")

@st.cache_resource
def get_connection():
    """Create cached Databricks SQL connection"""
    return sql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"].replace("https://", ""),
        http_path=st.secrets["DATABRICKS_WAREHOUSE_HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"],
    )

@st.cache_data(ttl=3600)
def load_data(ticker: str) -> pd.DataFrame:
    """Load market data for a specific ticker with parameterized query"""
    conn = get_connection()
    query = """
        SELECT * FROM market_analytics.gold.market_analytics_daily
        WHERE ticker = ?
        ORDER BY trade_date
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, [ticker])
            result = cursor.fetchall()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(result, columns=columns)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

st.title("📊 Hybrid Market Analytics Dashboard")

# Sidebar controls
ticker = st.sidebar.selectbox(
    "Select Ticker", 
    ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    help="Choose a stock ticker to analyze"
)

# Load data
df = load_data(ticker)

if df.empty:
    st.warning("⚠️ No data available for this ticker. Run the pipeline first.")
else:
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    latest = df.iloc[-1]
    
    col1.metric("Close Price", f"${latest['close_price']:.2f}")
    col2.metric(
        "RSI (14)", 
        f"{latest['rsi_14']:.1f}" if pd.notna(latest.get("rsi_14")) else "N/A"
    )
    col3.metric(
        "VADER Sentiment", 
        f"{latest['avg_vader_compound']:.2f}" if pd.notna(latest.get("avg_vader_compound")) else "N/A"
    )
    col4.metric(
        "Data Points", 
        f"{len(df):,}"
    )

    # Price & Technical Indicators Chart
    st.subheader(f"{ticker} Price & Technical Indicators")
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["trade_date"], 
        y=df["close_price"], 
        name="Close Price",
        line=dict(color="#1f77b4", width=2)
    ))
    
    if "sma_20" in df.columns and df["sma_20"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["trade_date"], 
            y=df["sma_20"], 
            name="SMA 20",
            line=dict(color="orange", width=1.5)
        ))
    
    if "bollinger_upper" in df.columns and df["bollinger_upper"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["trade_date"], 
            y=df["bollinger_upper"], 
            name="Bollinger Upper",
            line=dict(dash="dot", color="gray")
        ))
        fig.add_trace(go.Scatter(
            x=df["trade_date"], 
            y=df["bollinger_lower"], 
            name="Bollinger Lower",
            line=dict(dash="dot", color="gray")
        ))
    
    fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sentiment Chart
    if "avg_vader_compound" in df.columns and df["avg_vader_compound"].notna().any():
        st.subheader("Daily News Sentiment Analysis")
        fig2 = go.Figure()
        
        # Color bars based on sentiment
        colors = ["green" if x > 0 else "red" if x < 0 else "gray" 
                  for x in df["avg_vader_compound"]]
        
        fig2.add_trace(go.Bar(
            x=df["trade_date"], 
            y=df["avg_vader_compound"], 
            name="VADER Sentiment",
            marker_color=colors
        ))
        fig2.update_layout(
            height=300,
            xaxis_title="Date",
            yaxis_title="Sentiment Score",
            hovermode="x unified"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Raw data table
    with st.expander("📋 View Raw Data"):
        st.dataframe(df, use_container_width=True, height=400)