import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet

st.set_page_config(page_title="SOL Predictor", layout="wide")
st.title("🚀 Solana (SOL) Price Predictor")
st.warning("⚠️ Educational tool only. Not financial advice.")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# LIVE PRICE
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

# HISTORICAL CHART (CryptoCompare)
@st.cache_data(ttl=3600)
def get_historical():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/histoday"
        params = {"fsym": "SOL", "tsym": "USD", "limit": 730}
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

df_hist = get_historical()

if not df_hist.empty:
    st.subheader("Historical Price (Last \~2 Years)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist["ds"], y=df_hist["y"], mode="lines", name="SOL Price", line=dict(color="#00ff9d")))
    fig.update_layout(height=450, template="plotly_dark", xaxis_title="Date", yaxis_title="Price (USD)")
    st.plotly_chart(fig, use_container_width=True)

# 3-WEEK FORECAST
st.subheader("🔮 3-Week Price Forecast")
if st.button("Generate Forecast (takes \~10 seconds)"):
    with st.spinner("Training Prophet model..."):
        if df_hist.empty or len(df_hist) < 30:
            st.error("Not enough historical data.")
        else:
            try:
                model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False, seasonality_mode="multiplicative")
                model.fit(df_hist)
                future = model.make_future_dataframe(periods=21)
                forecast = model.predict(future)

                # Forecast chart
                fig_fc = go.Figure()
                fig_fc.add_trace(go.Scatter(x=df_hist["ds"], y=df_hist["y"], mode="lines", name="Historical", line=dict(color="#00ff9d")))
                fig_fc.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], mode="lines", name="Forecast", line=dict(dash="dash", color="#ffa500")))
                fig_fc.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_upper"], mode="lines", line_color="rgba(0,0,0,0)", showlegend=False))
                fig_fc.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_lower"], fill="tonexty", mode="lines", fillcolor="rgba(255,165,0,0.25)", line_color="rgba(0,0,0,0)", name="Uncertainty"))
                fig_fc.update_layout(title="Historical + 3-Week Forecast", height=500, template="plotly_dark", xaxis_title="Date", yaxis_title="Price (USD)")
                st.plotly_chart(fig_fc, use_container_width=True)

                # Table
                st.subheader("Daily Forecast (Next 21 Days)")
                table = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(21).copy()
                table["ds"] = table["ds"].dt.date
                table.columns = ["Date", "Predicted Price (\( )", "Lower Bound ( \))", "Upper Bound ($)"]
                st.dataframe(table.round(2), use_container_width=True, hide_index=True)

                st.info("Orange shaded area = uncertainty range")
            except Exception as e:
                st.error(f"Forecast error: {str(e)}")

st.caption("Live: CoinGecko • Chart: CryptoCompare • Forecast: Prophet")
