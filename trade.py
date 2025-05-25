import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import requests
import datetime
import time
import requests

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

import requests
import pandas as pd
import time

def get_crypto_data(coin_id, days=60, max_retries=5):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": str(days),
        "interval": "daily"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "prices" in data and data["prices"]:
                    prices = data["prices"]
                    df = pd.DataFrame(prices, columns=["Timestamp", "Close"])
                    df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
                    df.set_index("Date", inplace=True)
                    df.drop("Timestamp", axis=1, inplace=True)
                    return df
                else:
                    # Data incomplete, retry after backoff
                    time.sleep(2 ** attempt)
            else:
                # Handle non-200 HTTP codes (rate limits, server errors)
                time.sleep(2 ** attempt)
        except requests.RequestException as e:
            # Network error, retry after backoff
            time.sleep(2 ** attempt)

    # After max retries, return empty DataFrame
    return pd.DataFrame()


# ----- Login Screen -----
st.title("Login")
password = st.text_input("Enter password:", type="password")
if password != "2121":
    st.stop()

# Sidebar Page Selector
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Stocks", "Crypto"])

if page == "Stocks":
    st.title("Stock Tracker")
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

    # List to hold summary info dicts
    summary_data = []

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

        rsi_df = data[['RSI']].dropna().reset_index()
        rsi_chart = (
            alt.Chart(rsi_df)
            .mark_line(color='orange')
            .encode(x='Date:T', y='RSI:Q')
            .properties(title=f"{ticker} RSI (14)").interactive()
        )
        threshold_30 = alt.Chart(rsi_df).mark_rule(strokeDash=[5,5], color='red').encode(y=alt.datum(30))
        threshold_70 = alt.Chart(rsi_df).mark_rule(strokeDash=[5,5], color='red').encode(y=alt.datum(70))
        st.altair_chart(rsi_chart + threshold_30 + threshold_70, use_container_width=True)

        # Append summary info for this ticker
        summary_data.append({
            "Ticker": ticker,
            "Current Price (£)": current_price,
            "RSI": round(data['RSI'].iloc[-1], 2),
            "SMA(20)": round(data['SMA'].iloc[-1], 2),
            "EMA(20)": round(data['EMA'].iloc[-1], 2),
            "Signal": signal
        })

    # After processing all tickers, display the summary table
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.subheader("📋 Overview Summary")
        st.dataframe(summary_df.style.format({
            "Current Price (£)": "£{:.2f}",
            "RSI": "{:.2f}",
            "SMA(20)": "£{:.2f}",
            "EMA(20)": "£{:.2f}"
        }))

elif page == "Crypto":
    st.title("Crypto Tracker")
    if st.button("🔄 Refresh Data"):
        st.rerun()

    crypto_dict = {
        "Bitcoin": "bitcoin",
        "Ethereum": "ethereum",
        "Binance Coin": "binancecoin",
        "Cardano": "cardano",
        "Dogecoin": "dogecoin",
        "Solana": "solana",
        "Polkadot": "polkadot",
        "Ripple": "ripple",
        "Litecoin": "litecoin",
        "Avalanche": "avalanche-2"
    }

    selected_coins = st.multiselect(
        "🔍 Select cryptocurrencies to track:",
        options=list(crypto_dict.keys()),
        default=list(crypto_dict.keys())
    )
    coins = [crypto_dict[name] for name in selected_coins]

    for coin_name in selected_coins:
        st.subheader(f"📊 Crypto: {coin_name}")
        coin_id = crypto_dict[coin_name]
        df = get_crypto_data(coin_id, days=60)

        if df.empty:
            st.warning("⚠️ Error fetching data.")
            continue

        # Calculate indicators: SMA, EMA, RSI
        df['SMA'] = calculate_sma(df)
        df['EMA'] = calculate_ema(df)
        df['RSI'] = calculate_rsi(df)

        # Generate buy/sell/hold signal
        signal = signal_generator(df)

        current_price = float(df['Close'].dropna().iloc[-1])

        # Display key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 Current Price", f"${current_price:.2f}")
        col2.metric("📈 RSI", f"{df['RSI'].iloc[-1]:.2f}")
        col3.metric("📉 SMA(20)", f"${df['SMA'].iloc[-1]:.2f}")
        col4.metric("⚡ EMA(20)", f"${df['EMA'].iloc[-1]:.2f}")

        st.markdown(f"📌 **Signal:** {signal}")

        if signal == "Buy":
            st.info("🛍 Suggested: Consider Buying.")
        elif signal == "Sell":
            st.warning("📤 Suggested: Consider Selling.")
        else:
            st.write("⏸ Hold – no action recommended.")

        # Price chart with Close, SMA, EMA
        price_df = df.reset_index()
        price_chart = (
            alt.Chart(price_df)
            .transform_fold(['Close', 'SMA', 'EMA'], as_=['Type', 'Price'])
            .mark_line()
            .encode(x='Date:T', y='Price:Q', color='Type:N')
            .properties(title=f"{coin_name} Close Price, SMA(20) & EMA(20)")
        )
        st.altair_chart(price_chart, use_container_width=True)

        # RSI chart with scale domain [0, 100]
        rsi_df = df.reset_index()
        rsi_chart = (
            alt.Chart(rsi_df)
            .mark_line(color='orange')
            .encode(
                x='Date:T',
                y=alt.Y('RSI:Q', scale=alt.Scale(domain=[0, 100]))
            )
            .properties(title=f"{coin_name} RSI (14-day)")
        )
        st.altair_chart(rsi_chart, use_container_width=True)


