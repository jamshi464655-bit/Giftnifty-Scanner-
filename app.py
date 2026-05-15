import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Ultra-Pro Index Scanner", layout="wide")

# --- DARK UI STYLE ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .card {
        background-color: #161b22; padding: 15px; border-radius: 12px;
        border: 1px solid #30363d; text-align: center; margin-bottom: 10px;
    }
    .buy-zone { border-top: 5px solid #238636; background-color: #1c2a1e; }
    .sell-zone { border-top: 5px solid #da3633; background-color: #2a1c1c; }
    .wait-zone { border-top: 5px solid #8b949e; }
    .indicator-text { font-size: 12px; color: #8b949e; }
    .strike-info { color: #58a6ff; font-weight: bold; font-size: 22px; background: #0d1117; padding: 8px; border-radius: 5px; margin-top: 5px; }
    .gift-nifty { background-color: #1c2128; padding: 10px; border-radius: 10px; border: 1px solid #444c56; text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

def fetch_gift_nifty():
    """Gift Nifty ഡാറ്റ ഫെച്ച് ചെയ്യുന്നു, എറർ വന്നാൽ NoneType unpack എറർ ഒഴിവാക്കാൻ 3 വാല്യൂസ് റിട്ടേൺ ചെയ്യുന്നു."""
    try:
        gift = yf.download("GIFTY=F", period="2d", interval="5m", progress=False)
        if not gift.empty and len(gift) >= 2:
            last_price = round(gift['Close'].iloc[-1], 2)
            prev_close = gift['Close'].iloc[-2]
            change = round(last_price - prev_close, 2)
            color = "#238636" if change >= 0 else "#da3633"
            return last_price, change, color
        return None, None, None
    except:
        return None, None, None

def fetch_analysis(args):
    ticker, name = args
    try:
        # Weekend support - ഓഫ്‌ലൈൻ മോഡിൽ 1 ദിവസത്തെ കാൻഡിൽ
        is_weekend = datetime.now().weekday() >= 5
        interval = "1d" if is_weekend else "5m"
        period = "30d" 
        
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty or len(df) < 55: return None
        
        # Indicators: EMA 8, 13, 21, 55
        df['EMA8'] = ta.ema(df['Close'], length=8)
        df['EMA13'] = ta.ema(df['Close'], length=13)
        df['EMA21'] = ta.ema(df['Close'], length=21)
        df['EMA55'] = ta.ema(df['Close'], length=55)
        
        # VWAP, Supertrend, ADX, CCI
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        sti = ta.supertrend(df['High'], df['Low'], df['Close'], length=7, multiplier=3)
        df['ST_DIR'] = sti['SUPERTd_7_3.0'] 
        
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        df['ADX'] = adx_df['ADX_14']
        df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=14)
        
        last = df.iloc[-1]
        price = round(float(last['Close']), 2)
        
        # Strike Logic (ATM)
        strike_gap = 50 if "NIFTY 50" in name or "MIDCAP" in name else 100
        atm_strike = round(price / strike_gap) * strike_gap
        
        # Signal Logic
        bullish = (price > last['EMA8'] > last['EMA13'] > last['EMA21'] > last['EMA55'] and 
                   last['ST_DIR'] == 1 and last['CCI'] > 100)
        bearish = (price < last['EMA8'] < last['EMA13'] < last['EMA21'] < last['EMA55'] and 
                   last['ST_DIR'] == -1 and last['CCI'] < -100)
        
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

def main():
    st.markdown("<h2 style='text-align: center; color: #58a6ff;'>🎯 Ultra-Pro Strategy Scanner</h2>", unsafe_allow_html=True)
    
    # Gift Nifty Section - TypeError പരിഹരിച്ചു
    gn_price, gn_change, gn_color = fetch_gift_nifty()
    
    if gn_price is not None:
        st.markdown(f"""
            <div class="gift-nifty">
                <span style="color: #8b949e;">GIFT NIFTY: </span>
                <b style="font-size: 20px;">{gn_price}</b>
                <span style="color: {gn_color};"> ({'+' if gn_change > 0 else ''}{gn_change})</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Gift Nifty data is currently unavailable.")

    if st.button("🔄 START REAL-TIME SCAN"):
        indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY"), ("NIFTY_FIN_SERVICE.NS", "FINNIFTY"), ("NIFTY_MID_SELECT.NS", "MIDCAP")]
        
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(fetch_analysis, idx) for idx in indices]
            for f in as_completed(futures):
                res = f.result()
                if res: results.append(res)

        if results:
            cols = st.columns(4)
            for i, data in enumerate(results):
                with cols[i]:
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
        else:
            st.error("Market data unavailable. Please check your internet connection.")

if __name__ == "__main__":
    main()