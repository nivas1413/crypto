import streamlit as st
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime
import plotly.graph_objects as go

# ======================
# CONFIGURACIÓN APP
# ======================
st.set_page_config(page_title="Crypto Buy & Hold Backtest", layout="wide")
st.title("💰 Crypto Buy & Hold Backtest Dashboard")

# ======================
# INPUT DEL USUARIO
# ======================
st.sidebar.header("Backtest Settings")

symbol = st.sidebar.text_input("Enter Crypto Symbol (e.g. SOL/USDT)", "SOL/USDT")
year = st.sidebar.selectbox("Select Year for Backtest", list(range(2018, datetime.now().year + 1))[::-1])
exchange_id = "kucoin"

run = st.sidebar.button("Run Backtest")

# ======================
# FUNCIONES
# ======================
@st.cache_data
def fetch_data(exchange_id, symbol, start_date, end_date):
    exchange = getattr(ccxt, exchange_id)()
    since = exchange.parse8601(start_date + "T00:00:00Z")
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', since=since, limit=400)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    return df

# ======================
# BACKTEST
# ======================
if run:
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        df = fetch_data(exchange_id, symbol, start_date, end_date)

        if df.empty or len(df) < 2:
            st.error("No data available for the selected year.")
        else:
            # BUY & HOLD: invertir 1 unidad de capital
            df['returns'] = df['close'].pct_change()
            df['equity'] = (1 + df['returns']).cumprod()

            total_return = df['equity'].iloc[-1] - 1
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]

            # ======================
            # GRÁFICO DE PRECIO
            # ======================
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Close Price'))
            fig.update_layout(title=f"{symbol} Price - {year}", template="plotly_white", height=500)
            st.plotly_chart(fig, use_container_width=True)

            # ======================
            # MÉTRICAS
            # ======================
            st.subheader("📊 Buy & Hold Results")
            st.metric("Start Price", f"${start_price:.2f}")
            st.metric("End Price", f"${end_price:.2f}")
            st.metric("Total Return", f"{total_return*100:.2f}%")

            # ======================
            # GRÁFICO DE EQUITY
            # ======================
            st.line_chart(df[['equity']], height=250)

    except Exception as e:
        st.error(f"Error fetching data: {e}")
