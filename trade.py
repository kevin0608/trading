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

# ----- Cache fetching functions for Summary page -----
@st.cache_data(ttl=3600)
def fetch_stock_data(tickers):
    all_data = []
    for ticker in tickers:
        data = yf.download(ticker, period="60d", interval="1d", progress=False)
        if data.empty:
            continue
        data['RSI'] = calculate_rsi(data)
        data['SMA'] = calculate_sma(data)
        data['EMA'] = calculate_ema(data)
        latest = data.iloc[-1]
        signal = signal_generator(data)
        all_data.append({
            "Ticker": ticker,
            "Current Price": latest['Close'],
            "RSI": latest['RSI'],
            "SMA(20)": latest['SMA'],
            "EMA(20)": latest['EMA'],
            "Signal": signal
        })
    return pd.DataFrame(all_data)

@st.cache_data(ttl=3600)
def fetch_crypto_data(coins):
    all_data = []
    for coin_id in coins:
        df = get_crypto_data(coin_id, days=60)
        if df.empty:
            continue
        df['RSI'] = calculate_rsi(df)
        df['SMA'] = calculate_sma(df)
        df['EMA'] = calculate_ema(df)
        latest = df.iloc[-1]
        signal = signal_generator(df)
        all_data.append({
            "Coin": coin_id,
            "Current Price": latest['Close'],
            "RSI": latest['RSI'],
            "SMA(20)": latest['SMA'],
            "EMA(20)": latest['EMA'],
            "Signal": signal
        })
    return pd.DataFrame(all_data)

# ----- Main App -----

# Login Screen
st.title("Login")
password = st.text_input("Enter password:", type="password")
if password != "2121":
    st.stop()

# Sidebar Page Selector
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Stocks", "Crypto", "Summary"])

# Dictionaries extended up to ~50 companies & cryptos for summary page demo
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
    "PayPal (PYPL)": "PYPL",
    # extra tickers examples (add more if you want)
    "Intel (INTC)": "INTC",
    "Cisco (CSCO)": "CSCO",
    "IBM (IBM)": "IBM",
    "Qualcomm (QCOM)": "QCOM",
    "Salesforce (CRM)": "CRM",
    "Adobe (ADBE)": "ADBE",
    "Square (SQ)": "SQ",
    "Shopify (SHOP)": "SHOP",
    "Boeing (BA)": "BA",
    "Chevron (CVX)": "CVX",
    "Coca-Cola (KO)": "KO",
    "PepsiCo (PEP)": "PEP",
    "Walmart (WMT)": "WMT",
    "Visa (V)": "V",
    "Mastercard (MA)": "MA",
    "Disney (DIS)": "DIS",
    "Johnson & Johnson (JNJ)": "JNJ",
    "McDonald's (MCD)": "MCD",
    "Procter & Gamble (PG)": "PG",
    "Verizon (VZ)": "VZ",
    "ExxonMobil (XOM)": "XOM",
    "Bank of America (BAC)": "BAC",
    "JPMorgan Chase (JPM)": "JPM",
    "AT&T (T)": "T",
    "Pfizer (PFE)": "PFE",
}

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
    "Avalanche": "avalanche-2",
    # extra cryptos
    "Shiba Inu": "shiba-inu",
    "Chainlink": "chainlink",
    "Polygon": "matic-network",
    "Stellar": "stellar",
    "VeChain": "vechain",
    "Cosmos": "cosmos",
    "Tron": "tron",
    "EOS": "eos",
    "Monero": "monero",
    "Algorand": "algorand",
    "Tezos": "tezos",
    "IOTA": "iota",
    "NEO": "neo",
    "Zcash": "zcash",
    "Dash": "dash",
    "Waves": "waves",
    "Maker": "maker",
    "Kusama": "kusama",
    "Compound": "compound-governance-token",
    "Terra": "terra-luna",
}

if page == "Stocks":
    st.title("Stock Tracker")
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

    selected_names = st.multiselect("🔍 Select companies to track:", options=list(company_dict.keys()), default=list(company_dict.keys())[:10])
    companies = [company_dict[name] for name in selected_names]
    capital = st.number_input("💰 Enter your starting capital (£):", min_value=1, value=500)

    for ticker in companies:
        st.subheader(f"📊 Stock: {ticker}")
        data = yf.download(ticker, period="60d", interval="1d", progress=False)
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
        col3.metric("📉 SMA(20)", f"${data['SMA'].iloc[-1]:.2f}")
        col4.metric("⚡ EMA(20)", f"${data['EMA'].iloc[-1]:.2f}")
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
    st.title("Cryptocurrency Tracker")
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

    selected_coins = st.multiselect("🔍 Select cryptocurrencies to track:", options=list(crypto_dict.keys()), default=list(crypto_dict.keys())[:10])
    capital = st.number_input("💰 Enter your starting capital (£):", min_value=1, value=500)

    for coin_name in selected_coins:
        coin_id = crypto_dict[coin_name]
        df = get_crypto_data(coin_id)
        if df.empty:
            st.warning("⚠️ Error fetching data for " + coin_name)
            continue

        df['RSI'] = calculate_rsi(df)
        df['SMA'] = calculate_sma(df)
        df['EMA'] = calculate_ema(df)

        signal = signal_generator(df)
        current_price = float(df['Close'].dropna().iloc[-1])

        st.subheader(f"📊 Crypto: {coin_name}")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💵 Current Price", f"${current_price:.2f}")
        col2.metric("📈 RSI", f"{df['RSI'].iloc[-1]:.2f}")
        col3.metric("📉 SMA(20)", f"${df['SMA'].iloc[-1]:.2f}")
        col4.metric("⚡ EMA(20)", f"${df['EMA'].iloc[-1]:.2f}")
        col5.markdown(f"📌 **Signal:** {signal}")

        if signal == "Buy":
            position_size = capital * 0.25
            quantity = position_size / current_price
            st.info(f"🛍 Suggested Buy: £{position_size:.2f} (~{quantity:.4f} coins)")
        elif signal == "Sell":
            st.warning("📤 Consider selling your position.")
        else:
            st.write("⏸ Hold – no action recommended.")

        price_df = df[['Close', 'SMA', 'EMA']].dropna().reset_index()
        price_chart = (
            alt.Chart(price_df)
            .transform_fold(['Close', 'SMA', 'EMA'], as_=['Type', 'Price'])
            .mark_line()
            .encode(x='Date:T', y='Price:Q', color='Type:N')
            .properties(title=f"{coin_name} Close Price, SMA(20) & EMA(20)")
        )
        st.altair_chart(price_chart, use_container_width=True)

elif page == "Summary":
    st.title("Summary Dashboard")

    # Use all or slice to limit to 50 items max
    stock_tickers = list(company_dict.values())[:50]
    crypto_ids = list(crypto_dict.values())[:50]

    with st.spinner("Fetching stocks data..."):
        stock_df = fetch_stock_data(stock_tickers)

    with st.spinner("Fetching crypto data..."):
        crypto_df = fetch_crypto_data(crypto_ids)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Stocks Summary")
        st.dataframe(stock_df.style.format({
            "Current Price": "${:,.2f}",
            "RSI": "{:.2f}",
            "SMA(20)": "${:,.2f}",
            "EMA(20)": "${:,.2f}"
        }))

    with col2:
        st.subheader("💰 Cryptocurrencies Summary")
        st.dataframe(crypto_df.style.format({
            "Current Price": "${:,.2f}",
            "RSI": "{:.2f}",
            "SMA(20)": "${:,.2f}",
            "EMA(20)": "${:,.2f}"
        }))
