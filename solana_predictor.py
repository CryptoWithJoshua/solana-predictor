import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="SOL Price", layout="wide")
st.title("🚀 Solana (SOL) Price")

ticker = yf.Ticker("SOL-USD")
hist = ticker.history(period="2d")
current_price = hist .iloc[-1]

st.metric("Current SOL Price", f"${current_price:,.2f}")

df = ticker.history(period="1y")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df , name="SOL Price"))
fig.update_layout(title="SOL Price - Last Year", height=500)
st.plotly_chart(fig, use_container_width=True)

st.caption("Data from Yahoo Finance")
