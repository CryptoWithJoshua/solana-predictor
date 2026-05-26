import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from datetime import datetime
import time

st.set_page_config(page_title="SOL Predictor", layout="wide")
st.title("🚀 Solana (SOL) Price Predictor")
st.markdown("**Real-time price + 3-week forecast**")

# =============================================
# DISCLAIMER
# =============================================
st.warning("⚠️ **Disclaimer**: Educational tool only. Crypto is highly volatile. Predictions are NOT financial advice. Do not trade based on this app.")

# =============================================
# LIVE PRICE + 24H CHANGE
# =============================================
def get_live_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "solana",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()["solana"]
        return data["usd"], data["usd_24h_change"]
    except Exception:
        return None, None

col1, col2 = st.columns([3, 1])
with col1:
    price, change_24h = get_live_price()
    if price is not None:
        delta_str = f"{change_24h:+.2f}%" if change_24h is not None else "N/A"
        st.metric("Current SOL Price (USD)", f"${price:,.2f}", delta=delta_str)
    else:
        st.error("Could not fetch live price. Please try refreshing.")

with col2:
    st.caption("📡 Powered by CoinGecko • 24/7 market")

if st.button("🔄 Refresh Live Price"):
    st.rerun()

# =============================================
# HISTORICAL DATA
# =============================================
@st.cache_data(ttl=3600)  # cache 1 hour
def get_historical(days=730):
    try:
        url = "https://api.coingecko.com/api/v3/coins/solana/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        prices = r.json()["prices"]
        df = pd.DataFrame(prices, columns=["ds", "y"])
        df["ds"] = pd.to_datetime(df["ds"], unit="ms")
        return df
    except Exception as e:
        st.error(f"Historical data error: {e}")
        return pd.DataFrame()

df_hist = get_historical()

if not df_hist.empty:
    st.subheader("Historical Price Chart (Last \~2 years)")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=df_hist["ds"], y=df_hist["y"], mode="lines", name="SOL Price", line=dict(color="#00ff9d")))
    fig_hist.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        height=400,
        template="plotly_dark"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# =============================================
# PROPHET FORECAST (3 WEEKS)
# =============================================
st.subheader("🔮 3-Week Price Forecast")
if st.button("Generate Forecast (Prophet model)"):
    with st.spinner("Training Prophet model on historical data... (takes \~5-10 seconds)"):
        if df_hist.empty or len(df_hist) < 30:
            st.error("Not enough historical data.")
        else:
            try:
                # Prepare data for Prophet
                model = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=False,
                    seasonality_mode="multiplicative"   # better for price data
                )
                model.fit(df_hist)

                # Forecast next 21 days
                future = model.make_future_dataframe(periods=21)
                forecast = model.predict(future)

                # Plotly forecast chart
                fig_fc = go.Figure()
                # Historical
                fig_fc.add_trace(go.Scatter(
                    x=df_hist["ds"], y=df_hist["y"],
                    mode="lines", name="Historical Price",
                    line=dict(color="#00ff9d")
                ))
                # Forecast line
                fig_fc.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat"],
                    mode="lines", name="Forecast",
                    line=dict(dash="dash", color="#ffa500")
                ))
                # Uncertainty band
                fig_fc.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat_upper"],
                    mode="lines", line_color="rgba(0,0,0,0)", showlegend=False
                ))
                fig_fc.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat_lower"],
                    fill="tonexty", mode="lines",
                    fillcolor="rgba(255, 165, 0, 0.25)",
                    line_color="rgba(0,0,0,0)",
                    name="Uncertainty Range"
                ))
                fig_fc.update_layout(
                    title="Historical + 3-Week Forecast with Uncertainty",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    height=500,
                    template="plotly_dark"
                )
                st.plotly_chart(fig_fc, use_container_width=True)

                # Forecast table
                st.subheader("Daily Forecast Table (Next 21 Days)")
                table = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(21).copy()
                table["ds"] = table["ds"].dt.date
                table.columns = ["Date", "Predicted Price (\( )", "Lower Bound ( \))", "Upper Bound ($)"]
                table = table.round(2)
                st.dataframe(table, use_container_width=True, hide_index=True)

                st.info("The orange shaded area shows the model's uncertainty range.")

            except Exception as e:
                st.error(f"Forecast error: {e}")

# Footer
st.caption("Built with Streamlit • CoinGecko API • Facebook Prophet • ❤️ by Grok")
st.caption("Refresh the page or click the refresh button for the latest price.")
