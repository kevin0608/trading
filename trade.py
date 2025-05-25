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

def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def signal_generator(df):
    try:
        print("Raw DataFrame tail:\n", df.tail())  # See the last few rows

        rsi = float(df['RSI'].dropna().iloc[-1])
        sma = float(df['SMA'].dropna().iloc[-1])
        ema = float(df['EMA'].dropna().iloc[-1])
        close = float(df['Close'].dropna().iloc[-1])
        macd = float(df['MACD'].dropna().iloc[-1])
        macd_signal = float(df['MACD Signal'].dropna().iloc[-1])
        
    except Exception as e:
        print("Error:", e)
        return "Stop"

    print(f"RSI: {rsi}, SMA: {sma}, EMA: {ema}, Close: {close}, MACD: {macd}, MACD Signal: {macd_signal}")

    if rsi < 60:
        return "Buy"
    elif rsi >= 60:
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

company_dict = {
    # Tech & IT
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
    "Mastercard (MA)": "MA",
    "Intel (INTC)": "INTC",
    "Salesforce (CRM)": "CRM",
    "Adobe (ADBE)": "ADBE",
    "Oracle (ORCL)": "ORCL",
    "Cisco (CSCO)": "CSCO",
    "Qualcomm (QCOM)": "QCOM",
    "IBM (IBM)": "IBM",
    "Snap (SNAP)": "SNAP",
    "eBay (EBAY)": "EBAY",
    "Twitter (TWTR)": "TWTR",
    "Zoom (ZM)": "ZM",
    "Shopify (SHOP)": "SHOP",
    "Snowflake (SNOW)": "SNOW",
    "Palantir (PLTR)": "PLTR",
    "Dropbox (DBX)": "DBX",
    
    # Consumer Goods
    "Coca-Cola (KO)": "KO",
    "PepsiCo (PEP)": "PEP",
    "Procter & Gamble (PG)": "PG",
    "McDonald's (MCD)": "MCD",
    "Nike (NKE)": "NKE",
    "Starbucks (SBUX)": "SBUX",
    "Costco (COST)": "COST",
    "Colgate-Palmolive (CL)": "CL",
    "Mondelez (MDLZ)": "MDLZ",
    "Kraft Heinz (KHC)": "KHC",
    "General Mills (GIS)": "GIS",
    "L'Oreal (OR)": "OR",
    "Unilever (UL)": "UL",
    "Nestle (NSRGY)": "NSRGY",
    "Kimberly-Clark (KMB)": "KMB",
    "Estee Lauder (EL)": "EL",
    
    # Finance & Banks
    "JPMorgan Chase (JPM)": "JPM",
    "Goldman Sachs (GS)": "GS",
    "Morgan Stanley (MS)": "MS",
    "Bank of America (BAC)": "BAC",
    "Citigroup (C)": "C",
    "Wells Fargo (WFC)": "WFC",
    "American Express (AXP)": "AXP",
    "Visa (V)": "V",
    "Mastercard (MA)": "MA",
    "Charles Schwab (SCHW)": "SCHW",
    
    # Healthcare & Pharma
    "Johnson & Johnson (JNJ)": "JNJ",
    "AbbVie (ABBV)": "ABBV",
    "Pfizer (PFE)": "PFE",
    "Merck (MRK)": "MRK",
    "Moderna (MRNA)": "MRNA",
    "Gilead Sciences (GILD)": "GILD",
    "Bristol-Myers Squibb (BMY)": "BMY",
    "Eli Lilly (LLY)": "LLY",
    "Amgen (AMGN)": "AMGN",
    "Biogen (BIIB)": "BIIB",
    
    # Energy & Industrials
    "ExxonMobil (XOM)": "XOM",
    "Chevron (CVX)": "CVX",
    "ConocoPhillips (COP)": "COP",
    "Schlumberger (SLB)": "SLB",
    "Boeing (BA)": "BA",
    "Caterpillar (CAT)": "CAT",
    "3M (MMM)": "MMM",
    "Honeywell (HON)": "HON",
    "General Electric (GE)": "GE",
    "Lockheed Martin (LMT)": "LMT",
    "Raytheon (RTX)": "RTX",
    "FedEx (FDX)": "FDX",
    "United Parcel Service (UPS)": "UPS",
    
    # Telecom
    "Verizon (VZ)": "VZ",
    "AT&T (T)": "T",
    "T-Mobile (TMUS)": "TMUS",
    
    # Retail
    "Walmart (WMT)": "WMT",
    "Target (TGT)": "TGT",
    "Lowe's (LOW)": "LOW",
    "Home Depot (HD)": "HD",
    "Dollar General (DG)": "DG",
    
    # Automotive
    "Ford (F)": "F",
    "General Motors (GM)": "GM",
    "Toyota (TM)": "TM",
    "Honda (HMC)": "HMC",
    "Tesla (TSLA)": "TSLA",
    
    # Others & Misc
    "Disney (DIS)": "DIS",
    "Booking Holdings (BKNG)": "BKNG",
    "Airbnb (ABNB)": "ABNB",
    "Uber (UBER)": "UBER",
    "Lyft (LYFT)": "LYFT",
    "Netflix (NFLX)": "NFLX",
    "Spotify (SPOT)": "SPOT",
    "Zoom Video (ZM)": "ZM",
    "Slack (WORK)": "WORK",
    "Intel (INTC)": "INTC",
    
    # International Large Caps
    "Samsung (005930.KS)": "005930.KS",
    "Alibaba (BABA)": "BABA",
    "BHP Group (BHP)": "BHP",
    "Toyota (TM)": "TM",
    "Shell (SHEL)": "SHEL",
    "Siemens (SIE.DE)": "SIE.DE",
    "Nestle (NSRGY)": "NSRGY",
    "Novartis (NVS)": "NVS",
    "Roche (RHHBY)": "RHHBY",
    "Sony (SONY)": "SONY",
    
    # Additional Popular US Stocks
    "Twitter (TWTR)": "TWTR",
    "Square (SQ)": "SQ",
    "Intel (INTC)": "INTC",
    "Dropbox (DBX)": "DBX",
    "eBay (EBAY)": "EBAY",
    "Zillow (Z)": "Z",
    "Peloton (PTON)": "PTON",
    "Wayfair (W)": "W",
    "Xilinx (XLNX)": "XLNX",
    "Western Digital (WDC)": "WDC",
    
    # More Big Names
    "Twitter (TWTR)": "TWTR",
    "Facebook (META)": "META",
    "Zoom Video (ZM)": "ZM",
    "Slack (WORK)": "WORK",
    "Pinterest (PINS)": "PINS",
    "Square (SQ)": "SQ",
    "Shopify (SHOP)": "SHOP",
    "Atlassian (TEAM)": "TEAM",
    "DocuSign (DOCU)": "DOCU",
    "CrowdStrike (CRWD)": "CRWD",

    # Additional Tech & IT
    "ZoomInfo Technologies (ZI)": "ZI",
    "Snowflake Inc. (SNOW)": "SNOW",
    "Datadog (DDOG)": "DDOG",
    "Twilio (TWLO)": "TWLO",
    "Workday (WDAY)": "WDAY",
    "ServiceNow (NOW)": "NOW",
    "CrowdStrike (CRWD)": "CRWD",
    "Okta (OKTA)": "OKTA",
    "Atlassian (TEAM)": "TEAM",

    # More Consumer Goods
    "Clorox (CLX)": "CLX",
    "Church & Dwight (CHD)": "CHD",
    "Dollar Tree (DLTR)": "DLTR",
    "Hasbro (HAS)": "HAS",

    # More Finance & Banks
    "BlackRock (BLK)": "BLK",
    "Visa Europe (V)": "V",
    "American International Group (AIG)": "AIG",
    "CME Group (CME)": "CME",

    # More Healthcare & Pharma
    "Regeneron Pharmaceuticals (REGN)": "REGN",
    "Vertex Pharmaceuticals (VRTX)": "VRTX",
    "Novo Nordisk (NVO)": "NVO",
    "Sanofi (SNY)": "SNY",

    # Energy & Industrials
    "NextEra Energy (NEE)": "NEE",
    "Dominion Energy (D)": "D",
    "Deere & Company (DE)": "DE",
    "Eaton Corporation (ETN)": "ETN",
    "Tesla (TSLA)": "TSLA",

    # Telecom & Media
    "Comcast (CMCSA)": "CMCSA",
    "Charter Communications (CHTR)": "CHTR",
    "Spotify (SPOT)": "SPOT",

    # International
    "Tencent Holdings (0700.HK)": "0700.HK",
    "Baidu (BIDU)": "BIDU",
    "SAP (SAP)": "SAP",
    "Volkswagen (VWAGY)": "VWAGY",
    "LVMH (LVMUY)": "LVMUY",

    # Consumer Services / Travel
    "Expedia Group (EXPE)": "EXPE",
    "Carnival Corporation (CCL)": "CCL",
    "Marriott International (MAR)": "MAR",

    # Real Estate & REITs
    "Prologis (PLD)": "PLD",
    "American Tower (AMT)": "AMT",
    "Digital Realty (DLR)": "DLR",

    # Others
    "Adobe (ADBE)": "ADBE",
    "NVIDIA (NVDA)": "NVDA",
    "Micron Technology (MU)": "MU",
    "Square (SQ)": "SQ",
    "Pinterest (PINS)": "PINS",
    
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

# Summary Page with Signal Summary and Detailed DataFrames
elif page == "Summary":
    st.title("Summary: Stocks & Crypto Overview")

    # --- Select Companies ---
    with st.expander("🔍 Select companies for summary (click to expand)"):
        selected_names = st.multiselect(
            "Select companies:",
            options=list(company_dict.keys()),
            default=list(company_dict.keys())[:200]
        )
    companies = [company_dict[name] for name in selected_names]

    ticker_to_name = {v: k for k, v in company_dict.items()}  # Map tickers to names once

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
            "Company": ticker_to_name.get(ticker, "Unknown"),
            "Current Price": current_price,
            "RSI": data['RSI'].iloc[-1],
            "SMA(20)": data['SMA'].iloc[-1],
            "EMA(20)": data['EMA'].iloc[-1],
            "Signal": signal
        })
    stock_df = pd.DataFrame(stock_rows)

    # --- Select Cryptocurrencies ---
    with st.expander("🔍 Select cryptocurrencies for summary (click to expand)"):
        selected_coins = st.multiselect(
            "Select cryptocurrencies:",
            options=list(crypto_dict.keys()),
            default=list(crypto_dict.keys())[:50]
        )
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

    # --- Signal Summary ---
    st.subheader("🔔 Signal Summary")

    stock_signal_counts = stock_df['Signal'].value_counts() if not stock_df.empty else {}
    crypto_signal_counts = crypto_df['Signal'].value_counts() if not crypto_df.empty else {}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Stocks Signals**")
        for signal in ["Buy", "Hold", "Sell"]:
            count = stock_signal_counts.get(signal, 0)
            st.write(f"{signal}: {count}")

    with col2:
        st.markdown("**Crypto Signals**")
        for signal in ["Buy", "Hold", "Sell"]:
            count = crypto_signal_counts.get(signal, 0)
            st.write(f"{signal}: {count}")

    # --- Detailed DataFrames inside expanders ---
    with st.expander("📈 Stocks Overview (detailed)"):
        st.dataframe(stock_df.style.format({
            "Current Price": safe_currency_format,
            "RSI": safe_float_format,
            "SMA(20)": safe_currency_format,
            "EMA(20)": safe_currency_format,
        }))

    with st.expander("🪙 Crypto Overview (detailed)"):
        st.dataframe(crypto_df.style.format({
            "Current Price": safe_currency_format,
            "RSI": safe_float_format,
            "SMA(20)": safe_currency_format,
            "EMA(20)": safe_currency_format,
        }))
