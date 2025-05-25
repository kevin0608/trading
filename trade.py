import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
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
    try:
        rsi = float(df['RSI'].dropna().iloc[-1])
        sma = float(df['SMA'].dropna().iloc[-1])
        ema = float(df['EMA'].dropna().iloc[-1])
        close = float(df['Close'].dropna().iloc[-1])
    except IndexError:
        return "Hold"

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

# Safe formatting functions
def safe_currency_format(x):
    try:
        return f"${x:,.2f}"
    except (ValueError, TypeError):
        return ""

def safe_float_format(x):
    try:
        return f"{x:.2f}"
    except (ValueError, TypeError):
        return ""

# ----- Login Screen -----
st.title("Login")
password = st.text_input("Enter password:", type="password")
if password != "2121":
    st.stop()

# Sidebar Page Selector
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Stocks", "Crypto", "Summary"])

# Expanded Company Dictionary (50 popular stocks)
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
    "Visa (V)": "V",
    "JPMorgan Chase (JPM)": "JPM",
    "Johnson & Johnson (JNJ)": "JNJ",
    "Walmart (WMT)": "WMT",
    "Procter & Gamble (PG)": "PG",
    "Mastercard (MA)": "MA",
    "Disney (DIS)": "DIS",
    "Intel (INTC)": "INTC",
    "Coca-Cola (KO)": "KO",
    "PepsiCo (PEP)": "PEP",
    "ExxonMobil (XOM)": "XOM",
    "Berkshire Hathaway (BRK-B)": "BRK-B",
    "Chevron (CVX)": "CVX",
    "McDonald's (MCD)": "MCD",
    "AbbVie (ABBV)": "ABBV",
    "Salesforce (CRM)": "CRM",
    "Adobe (ADBE)": "ADBE",
    "Oracle (ORCL)": "ORCL",
    "Cisco (CSCO)": "CSCO",
    "Toyota (TM)": "TM",
    "IBM (IBM)": "IBM",
    "Qualcomm (QCOM)": "QCOM",
    "Nike (NKE)": "NKE",
    "Starbucks (SBUX)": "SBUX",
    "Costco (COST)": "COST",
    "Paychex (PAYX)": "PAYX",
    "Ford (F)": "F",
    "General Motors (GM)": "GM",
    "Lockheed Martin (LMT)": "LMT",
    "Honeywell (HON)": "HON",
    "3M (MMM)": "MMM",
    "Delta Air Lines (DAL)": "DAL",
    "Boeing (BA)": "BA",
    "Goldman Sachs (GS)": "GS",
    "Morgan Stanley (MS)": "MS",
    "American Express (AXP)": "AXP",
    "Verizon (VZ)": "VZ",
    "AT&T (T)": "T",
    "eBay (EBAY)": "EBAY",
    "Snap (SNAP)": "SNAP"
}

# Expanded Crypto Dictionary (50 popular cryptocurrencies)
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
    "Shiba Inu": "shiba-inu",
    "Chainlink": "chainlink",
    "Polygon": "matic-network",
    "Stellar": "stellar",
    "VeChain": "vechain",
    "Tron": "tron",
    "EOS": "eos",
    "Monero": "monero",
    "Algorand": "algorand",
    "Tezos": "tezos",
    "Cosmos": "cosmos",
    "Filecoin": "filecoin",
    "Bitcoin Cash": "bitcoin-cash",
    "NEO": "neo",
    "IOTA": "iota",
    "Dash": "dash",
    "Zcash": "zcash",
    "Maker": "maker",
    "Kusama": "kusama",
    "Theta Network": "theta-token",
    "Elrond": "elrond-erd-2",
    "Compound": "compound-governance-token",
    "Aave": "aave",
    "SushiSwap": "sushi",
    "Yearn Finance": "yearn-finance",
    "Terra": "terra-luna",
    "Fantom": "fantom",
    "Harmony": "harmony",
    "Hedera": "hedera-hashgraph",
    "Celo": "celo",
    "Enjin Coin": "enjincoin",
    "Basic Attention Token": "basic-attention-token",
    "Decentraland": "decentraland",
    "The Graph": "the-graph",
    "Loopring": "loopring",
    "Bitcoin SV": "bitcoin-cash-sv",
    "Qtum": "qtum",
    "Zilliqa": "zilliqa",
    "Waves": "waves"
}


# Stocks Page
if page == "Stocks":
    st.title("Stock Tracker")
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

    selected_names = st.multiselect("🔍 Select companies to track:", options=list(company_dict.keys()), default=list(company_dict.keys())[:10])
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

# Crypto Page
elif page == "Crypto":
    st.title("Crypto Tracker")
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

    selected_coins = st.multiselect("🔍 Select cryptocurrencies to track:", options=list(crypto_dict.keys()), default=list(crypto_dict.keys())[:10])
    coins = [crypto_dict[name] for name in selected_coins]

    for coin_name in selected_coins:
        st.subheader(f"📊 Crypto: {coin_name}")
        coin_id = crypto_dict[coin_name]
        df = get_crypto_data(coin_id, days=60)

        if df.empty:
            st.warning("⚠️ Error fetching data.")
            continue

        df['SMA'] = calculate_sma(df)
        df['EMA'] = calculate_ema(df)
        df['RSI'] = calculate_rsi(df)

        signal = signal_generator(df)
        current_price = float(df['Close'].dropna().iloc[-1])

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

        price_df = df.reset_index()
        price_chart = (
            alt.Chart(price_df)
            .transform_fold(['Close', 'SMA', 'EMA'], as_=['Type', 'Price'])
            .mark_line()
            .encode(x='Date:T', y='Price:Q', color='Type:N')
            .properties(title=f"{coin_name} Close Price, SMA(20) & EMA(20)")
        )
        st.altair_chart(price_chart, use_container_width=True)

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

# Summary Page with both DataFrames
elif page == "Summary":
    st.title("Summary: Stocks & Crypto Overview")
    capital = st.number_input("💰 Enter your starting capital (£):", min_value=1, value=500)

    # Stocks summary dataframe
    selected_names = st.multiselect("🔍 Select companies for summary:", options=list(company_dict.keys()), default=list(company_dict.keys())[:50])
    companies = [company_dict[name] for name in selected_names]

    stock_rows = []
    for ticker in companies:
        data = yf.download(ticker, period="60d", interval="1d", progress=False)
        if data.empty:
            continue
        data['RSI'] = calculate_rsi(data)
        data['SMA'] = calculate_sma(data)
        data['EMA'] = calculate_ema(data)
        signal = signal_generator(data)
        current_price = float(data['Close'].dropna().iloc[-1])

        stock_rows.append({
            "Ticker": ticker,
            "Current Price": current_price,
            "RSI": data['RSI'].iloc[-1],
            "SMA(20)": data['SMA'].iloc[-1],
            "EMA(20)": data['EMA'].iloc[-1],
            "Signal": signal
        })
    stock_df = pd.DataFrame(stock_rows)

    st.subheader("📈 Stocks Overview")
    st.dataframe(stock_df.style.format({
        "Current Price": safe_currency_format,
        "RSI": safe_float_format,
        "SMA(20)": safe_currency_format,
        "EMA(20)": safe_currency_format,
    }))

    # Crypto summary dataframe
    selected_coins = st.multiselect("🔍 Select cryptocurrencies for summary:", options=list(crypto_dict.keys()), default=list(crypto_dict.keys())[:50])
    coins = [crypto_dict[name] for name in selected_coins]

    crypto_rows = []
    for coin_name in selected_coins:
        df = get_crypto_data(crypto_dict[coin_name], days=60)
        if df.empty:
            continue
        df['RSI'] = calculate_rsi(df)
        df['SMA'] = calculate_sma(df)
        df['EMA'] = calculate_ema(df)
        signal = signal_generator(df)
        current_price = float(df['Close'].dropna().iloc[-1])

        crypto_rows.append({
            "Coin": coin_name,
            "Current Price": current_price,
            "RSI": df['RSI'].iloc[-1],
            "SMA(20)": df['SMA'].iloc[-1],
            "EMA(20)": df['EMA'].iloc[-1],
            "Signal": signal
        })
    crypto_df = pd.DataFrame(crypto_rows)

    st.subheader("🪙 Crypto Overview")
    st.dataframe(crypto_df.style.format({
        "Current Price": safe_currency_format,
        "RSI": safe_float_format,
        "SMA(20)": safe_currency_format,
        "EMA(20)": safe_currency_format,
    }))

