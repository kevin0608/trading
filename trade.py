import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import requests
import datetime

# ----- Helper functions -----
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(data, window=20):
    return data['Close'].rolling(window=window).mean()

def calculate_ema(data, window=20):
    return data['Close'].ewm(span=window, adjust=False).mean()

def signal_generator(df):
    rsi = float(df['RSI'].dropna().iloc[-1])
    sma = float(df['SMA'].dropna().iloc[-1])
    ema = float(df['EMA'].dropna().iloc[-1])
    close = float(df['Close'].dropna().iloc[-1])

    if (rsi < 30) and (close > ema):
        return "Buy"
    elif (rsi > 70) and (close < ema):
        return "Sell"
    else:
        return "Hold"
    

def get_crypto_data(coin_id, days=60):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "prices" not in data:
        return pd.DataFrame()

    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["Timestamp", "Close"])
    df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
    df.set_index("Date", inplace=True)
    df.drop("Timestamp", axis=1, inplace=True)
    return df

# ----- Login Screen -----
st.title("Login")
password = st.text_input("Enter password:", type="password")
if password != "2121":
    st.stop()

# Sidebar Page Selector
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Stocks", "Crypto"])

if page == "Stocks":
    st.title("📈 Optimised Trading Assistant")
    if st.button("🔄 Refresh Data"):
        st.rerun()

    company_dict = {
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Microsoft (MSFT)": "MSFT",
        "Google (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "NVIDIA (NVDA)": "NVDA",
        "Meta (META)": "META",
        "Netflix (NFLX)": "NFLX",
        "AMD (AMD)": "AMD",
        "PayPal (PYPL)": "PYPL"
    }

    selected_names = st.multiselect("🔍 Select companies to track:", options=list(company_dict.keys()), default=list(company_dict.keys()))
    companies = [company_dict[name] for name in selected_names]
    capital = st.number_input("💰 Enter your starting capital (£):", min_value=1, value=500)

    for ticker in companies:
        st.subheader(f"📊 Stock: {ticker}")
        data = yf.download(ticker, period="60d", interval="1d")
        if data.empty:
            st.warning("⚠️ Error fetching data.")
            continue

        data['RSI'] = calculate_rsi(data)
        data['SMA'] = calculate_sma(data)
        data['EMA'] = calculate_ema(data)


        signal = signal_generator(data)
        current_price = float(data['Close'].dropna().iloc[-1])

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💵 Current Price", f"${current_price:.2f}")
        col2.metric("📈 RSI", f"{data['RSI'].iloc[-1]:.2f}")
        col3.metric("📉 SMA(20)", f"£{data['SMA'].iloc[-1]:.2f}")
        col4.metric("⚡ EMA(20)", f"£{data['EMA'].iloc[-1]:.2f}")
        col5.markdown(f"📌 **Signal:** {signal}")

        if signal == "Buy":
            position_size = capital * 0.25
            quantity = position_size / current_price
            st.info(f"🛍 Suggested Buy: £{position_size:.2f} (~{quantity:.2f} shares)")
        elif signal == "Sell":
            st.warning("📤 Consider selling your position.")
        else:
            st.write("⏸ Hold – no action recommended.")

        price_df = data[['Close', 'SMA', 'EMA']].dropna().reset_index()
        price_chart = (
            alt.Chart(price_df)
            .transform_fold(['Close', 'SMA', 'EMA'], as_=['Type', 'Price'])
            .mark_line()
            .encode(x='Date:T', y='Price:Q', color='Type:N')
            .properties(title=f"{ticker} Close Price, SMA(20) & EMA(20)")
        )
        st.altair_chart(price_chart, use_container_width=True)

elif page == "Crypto":
    st.title("💰 Crypto Tracker")

    crypto_dict = {
        "Bitcoin": "bitcoin",
        "Ethereum": "ethereum",
        "Binance Coin": "binancecoin",
        "Cardano": "cardano",
        "Dogecoin": "dogecoin"
    }

    selected_coins = st.multiselect("🔍 Select cryptocurrencies to track:", options=list(crypto_dict.keys()), default=list(crypto_dict.keys()))

    for coin_name in selected_coins:
        st.subheader(f"📊 Crypto: {coin_name}")
        coin_id = crypto_dict[coin_name]
        df = get_crypto_data(coin_id, days=60)

        if df.empty:
            st.warning("⚠️ Error fetching data.")
            continue

        # Calculate SMA and EMA for crypto Close price
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['EMA'] = df['Close'].ewm(span=20, adjust=False).mean()

        price_df = df.reset_index()
        price_chart = (
            alt.Chart(price_df)
            .transform_fold(['Close', 'SMA', 'EMA'], as_=['Type', 'Price'])
            .mark_line()
            .encode(x='Date:T', y='Price:Q', color='Type:N')
            .properties(title=f"{coin_name} Close Price, SMA(20) & EMA(20)")
        )
        st.altair_chart(price_chart, use_container_width=True)

elif page == "Crypto":
    st.title("₿ Real-Time Crypto Tracker (API Based)")

    crypto_dict = {
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Tether (USDT)": "tether",
        "BNB (BNB)": "binancecoin",
        "Solana (SOL)": "solana",
        "USD Coin (USDC)": "usd-coin",
        "XRP (XRP)": "ripple",
        "Dogecoin (DOGE)": "dogecoin",
        "Cardano (ADA)": "cardano",
        "Avalanche (AVAX)": "avalanche-2"
    }

    selected_cryptos = st.multiselect("🔍 Select cryptocurrencies to track:", options=list(crypto_dict.keys()), default=list(crypto_dict.keys()))
    capital = st.number_input("💰 Enter your crypto capital ($):", min_value=1, value=500)

    for name in selected_cryptos:
        coin_id = crypto_dict[name]
        df = get_crypto_data(coin_id)

        if df.empty or len(df) < 20:
            st.warning(f"⚠️ Not enough data for {name}.")
            continue

        df['SMA'] = calculate_sma(df)
        df['EMA'] = calculate_ema(df)
        df['RSI'] = calculate_rsi(df)

        signal = signal_generator(df)
        current_price = float(df['Close'].iloc[-1])

        st.subheader(f"💸 {name}")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💵 Price", f"${current_price:.2f}")
        col2.metric("📈 RSI", f"{df['RSI'].iloc[-1]:.2f}")
        col3.metric("📉 SMA(20)", f"${df['SMA'].iloc[-1]:.2f}")
        col4.metric("⚡ EMA(20)", f"${df['EMA'].iloc[-1]:.2f}")
        col5.markdown(f"📌 **Signal:** {signal}")

        if signal == "Buy":
            position_size = capital * 0.25
            quantity = position_size / current_price
            st.info(f"🛒 Suggested Buy: ${position_size:.2f} (~{quantity:.4f} units)")
        elif signal == "Sell":
            st.warning("📤 Consider selling your position.")
        else:
            st.write("⏸ Hold – no action recommended.")

        price_df = df[['Close', 'SMA', 'EMA']].dropna().reset_index()
        chart = (
            alt.Chart(price_df)
            .transform_fold(['Close', 'SMA', 'EMA'], as_=['Type', 'Price'])
            .mark_line()
            .encode(x='Date:T', y='Price:Q', color='Type:N')
            .properties(title=f"{name} Price & Indicators")
        )
        st.altair_chart(chart, use_container_width=True)
