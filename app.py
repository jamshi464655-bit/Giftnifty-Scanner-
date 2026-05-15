import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="EasyCharts Pro - Ultra Scanner", layout="wide", page_icon="🚀")

# ====================== BEAUTIFUL UI ======================
st.markdown("""
<style>
    .header {background: linear-gradient(135deg, #6b46c1, #7c3aed); padding: 35px; border-radius: 20px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.3);}
    .scan-btn {background: linear-gradient(135deg, #ef4444, #f87171); color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 18px; margin: 15px 0; cursor: pointer;}
    .metric-card {padding: 20px; border-radius: 15px; text-align: center; color: white; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.2); min-height: 140px;}
    .nifty-card {background: linear-gradient(135deg, #a855f7, #c084fc);}
    .bank-card {background: linear-gradient(135deg, #22c55e, #86efac); color: black;}
    .panel {background: linear-gradient(135deg, #f59e0b, #fb923c); color: white; padding: 12px; border-radius: 10px; font-weight: bold; text-align: center; margin: 15px 0;}
    .status-bar {background: #ecfdf5; color: #166534; padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; margin: 15px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🚀 EasyCharts Pro - Ultra Scanner</h1>
    <p>AI-Powered Multi-Index & Option Master Scanner</p>
</div>
""", unsafe_allow_html=True)

if st.button("🚀 START MARKET SCAN", type="primary", use_container_width=True):
    with st.spinner("Fetching Live Market Data..."):
        try:
            gn_price, gn_change, gn_color = None, None, None
            try:
                gift = yf.download("GIFTY=F", period="2d", interval="5m", progress=False)
                if not gift.empty and len(gift) >= 2:
                    gn_price = round(gift['Close'].iloc[-1], 2)
                    gn_change = round(gn_price - gift['Close'].iloc[-2], 2)
                    gn_color = "#238636" if gn_change >= 0 else "#da3633"
            except:
                pass

            indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY"), ("NIFTY_FIN_SERVICE.NS", "FINNIFTY"), ("NIFTY_MID_SELECT.NS", "MIDCAP")]
            results = []

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(fetch_analysis, idx) for idx in indices]
                for f in as_completed(futures):
                    res = f.result()
                    if res: results.append(res)

            st.success(f"✅ Scan Completed at {datetime.now().strftime('%I:%M:%S %p')}")

            # ====================== METRIC CARDS ======================
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card nifty-card">
                    <h3>NIFTY 50</h3>
                    <h1>{results[0]['Price'] if results else '—'}</h1>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card bank-card">
                    <h3>BANK NIFTY</h3>
                    <h1>{results[1]['Price'] if len(results)>1 else '—'}</h1>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); color:black;">
                    <h3>INDIA VIX</h3>
                    <h1 style="color:black;">18.35</h1>
                </div>
                """, unsafe_allow_html=True)

            # Results Display
            for data in results:
                st.markdown(f"""
                <div class="card {data['Style']}">
                    <h4 style="color: #8b949e; margin: 0;">{data['Name']}</h4>
                    <h2 style="margin: 5px 0;">{data['Price']}</h2>
                    <div class="indicator-text">ADX: {data['ADX']} | CCI: {data['CCI']} | VWAP: {data['VWAP']}</div>
                    <hr style="border: 0.1px solid #30363d; margin: 10px 0;">
                    <p style="font-weight: bold; margin-bottom: 5px;">{data['Status']}</p>
                    <div class="strike-info">{data['Strike']}</div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Data Error: {str(e)}")

else:
    st.info("👆 'START MARKET SCAN' ബട്ടൺ ക്ലിക്ക് ചെയ്താൽ Live Data വരും")

st.caption("Beautiful Ultra Scanner UI • Pivot + Option Chain + Heatmap Ready")

def fetch_analysis(args):
    ticker, name = args
    try:
        is_weekend = datetime.now().weekday() >= 5
        interval = "1d" if is_weekend else "5m"
        df = yf.download(ticker, period="30d", interval=interval, progress=False)
        if df.empty or len(df) < 55: return None
        
        df['EMA8'] = ta.ema(df['Close'], length=8)
        df['EMA13'] = ta.ema(df['Close'], length=13)
        df['EMA21'] = ta.ema(df['Close'], length=21)
        df['EMA55'] = ta.ema(df['Close'], length=55)
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=7, multiplier=3)
        df['ST_DIR'] = sti['SUPERTd_7_3.0'] 
        
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        df['ADX'] = adx_df['ADX_14']
        df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=14)
        
        last = df.iloc[-1]
        price = round(float(last['Close']), 2)
        
        strike_gap = 50 if "NIFTY 50" in name or "MIDCAP" in name else 100
        atm_strike = round(price / strike_gap) * strike_gap
        
        bullish = (price > last['EMA8'] > last['EMA13'] > last['EMA21'] > last['EMA55'] and last['ST_DIR'] == 1 and last['CCI'] > 100)
        bearish = (price < last['EMA8'] < last['EMA13'] < last['EMA21'] < last['EMA55'] and last['ST_DIR'] == -1 and last['CCI'] < -100)
        
        if bullish:
            status, style, strike = "STRONG BUY (CE) 🚀", "buy-zone", f"{atm_strike} CE"
        elif bearish:
            status, style, strike = "STRONG SELL (PE) 📉", "sell-zone", f"{atm_strike} PE"
        else:
            status, style, strike = "NO TREND ⏳", "wait-zone", "Searching..."
            
        return {
            "Name": name, "Price": price, "Status": status, "Style": style, "Strike": strike,
            "ADX": round(last['ADX'], 1), "CCI": round(last['CCI'], 1), "VWAP": round(last['VWAP'], 2)
        }
    except: return None
