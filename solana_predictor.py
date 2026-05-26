import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="SOL Predictor", layout="wide")
st.title("🚀 Solana (SOL) Price Predictor")
st.warning("⚠️ Educational tool only. Not financial advice.")

# Live price (CoinGecko - already working)
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=60)
def get_live_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "solana", "vs_currencies": "usd", "include_24hr_change": "true"},
            headers=HEADERS,
            timeout=15
        )
        r.raise_for_status()
        data = r.json()["solana"]
        return data["usd"], data.get("usd_24h_change")
    except Exception as e:
        st.error(f"Live price error: {str(e)}")
        return None, None

price, change = get_live_price()
if price is not None:
    st.metric("Current SOL Price (USD)", f"${price:,.2f}", f"{change:+.2f}%" if change is not None else None)

# Historical chart using CryptoCompare (works in US)
@st.cache_data(ttl=3600)
def get_historical():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/histoday"
        params = {
            "fsym": "SOL",
            "tsym": "USD",
            "limit": 730
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["time"], unit="s")
        df["y"] = pd.to_numeric(df["close"])
        return df[["ds", "y"]]
    except Exception as e:
        st.error(f"Historical data error: {str(e)}")
        return pd.DataFrame()

df = get_historical()

if not df.empty:
    st.subheader("Historical Price (Last \~2 Years)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["ds"], y=df["y"], mode="lines", name="SOL Price", line=dict(color="#00ff9d")))
    fig.update_layout(height=450, template="plotly_dark", xaxis_title="Date", yaxis_title="Price (USD)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Could not load historical chart")

st.caption("Live price: CoinGecko • Chart: CryptoCompare • Refreshes automatically")
