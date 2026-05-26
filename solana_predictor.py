import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="SOL Predictor", layout="wide")
st.title("🚀 Solana (SOL) Price Predictor")
st.warning("⚠️ Educational tool only. Not financial advice.")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

@st.cache_data(ttl=60)
def get_live_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "solana", "vs_currencies": "usd", "include_24hr_change": "true"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()["solana"]
        return data["usd"], data.get("usd_24h_change")
    except Exception as e:
        st.error(f"Live price error: {str(e)}")
        return None, None

price, change = get_live_price()

if price is not None:
    st.metric("Current SOL Price (USD)", f"${price:,.2f}", f"{change:+.2f}%" if change is not None else None)
else:
    st.warning("Could not load live price")

@st.cache_data(ttl=3600)
def get_historical():
    try:
        url = "https://api.coingecko.com/api/v3/coins/solana/market_chart"
        params = {"vs_currency": "usd", "days": "730", "interval": "daily"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        prices = r.json()["prices"]
        df = pd.DataFrame(prices, columns=["ds", "y"])
        df["ds"] = pd.to_datetime(df["ds"], unit="ms")
        return df
    except Exception as e:
        st.error(f"Historical data error: {str(e)}")
        return pd.DataFrame()

df = get_historical()

if not df.empty:
    st.subheader("Historical Price (Last 2 Years)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["ds"], y=df["y"], mode="lines", name="SOL Price", line=dict(color="#00ff9d")))
    fig.update_layout(height=450, template="plotly_dark", xaxis_title="Date", yaxis_title="Price (USD)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Could not load historical chart")

st.caption("Data from CoinGecko • Refreshes automatically")
