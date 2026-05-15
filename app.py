import streamlit as st
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

st.set_page_config(page_title="Ultra-Pro Index Scanner", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b0e14; color: #ffffff; }
.card {
    background:#161b22;
    padding:20px;
    border-radius:15px;
    text-align:center;
    border:1px solid #30363d;
}
.buy-zone { border-top:5px solid #16a34a; }
.sell-zone { border-top:5px solid #dc2626; }
.wait-zone { border-top:5px solid #6b7280; }
</style>
""", unsafe_allow_html=True)

# ---------- CUSTOM INDICATORS (No pandas_ta) ----------

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ---------- FETCH FUNCTION ----------

def fetch_analysis(args):
    ticker, name = args
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 50:
            return None

        df["EMA8"] = ema(df["Close"], 8)
        df["EMA21"] = ema(df["Close"], 21)
        df["EMA55"] = ema(df["Close"], 55)
        df["RSI"] = rsi(df["Close"])

        last = df.iloc[-1]
        price = round(float(last["Close"]), 2)

        strike_gap = 50 if "NIFTY" in name else 100
        atm_strike = round(price / strike_gap) * strike_gap

        bullish = price > last["EMA8"] > last["EMA21"] > last["EMA55"]
        bearish = price < last["EMA8"] < last["EMA21"] < last["EMA55"]

        if bullish:
            status, style, strike = "🟢 STRONG BUY (CE)", "buy-zone", f"{atm_strike} CE"
        elif bearish:
            status, style, strike = "🔴 STRONG SELL (PE)", "sell-zone", f"{atm_strike} PE"
        else:
            status, style, strike = "⚪ NO TREND", "wait-zone", "Searching..."

        return {
            "Name": name,
            "Price": price,
            "RSI": round(last["RSI"], 1),
            "Status": status,
            "Style": style,
            "Strike": strike
        }

    except:
        return None

# ---------- UI ----------

st.markdown("<h2 style='text-align:center;'>🚀 Ultra-Pro Strategy Scanner</h2>", unsafe_allow_html=True)

if st.button("🔄 START REAL-TIME SCAN"):

    indices = [
        ("^NSEI", "NIFTY 50"),
        ("^NSEBANK", "BANK NIFTY")
    ]

    results = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        for res in executor.map(fetch_analysis, indices):
            if res:
                results.append(res)

    if results:
        cols = st.columns(len(results))
        for i, data in enumerate(results):
            with cols[i]:
                st.markdown(f"""
                <div class="card {data['Style']}">
                    <h3>{data['Name']}</h3>
                    <h1>{data['Price']}</h1>
                    <p>{data['Status']}</p>
                    <small>RSI: {data['RSI']}</small>
                    <br>
                    <strong>{data['Strike']}</strong>
                </div>
                """, unsafe_allow_html=True)

        st.success(f"✅ Scan completed at {datetime.now().strftime('%I:%M:%S %p')}")
    else:
        st.warning("No data available.")
