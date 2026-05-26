import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

st.set_page_config(page_title="SOL Predictor", layout="wide")
st.title("🚀 Solana (SOL) Price Predictor")
st.warning("⚠️ Educational tool only. Not financial advice.")

# Live price
ticker = yf.Ticker("SOL-USD")
data = ticker.history(period="2d")
current_price = data['Close' -1]
st.metric("Current SOL Price", f"${current_price:,.2f}")

# Historical data
df = ticker.history(period="2y").reset_index()
df = df.rename(columns={'Date': 'ds', 'Close': 'y'})

# Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['ds'], y=df , name='SOL Price', line=dict(color='#00ff9d')))
fig.update_layout(title="Historical Price (Last 2 Years)", height=400, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.caption("Data from Yahoo Finance • Updated live")
