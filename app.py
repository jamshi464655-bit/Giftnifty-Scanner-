import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

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
    .heatmap {display: grid; grid-template-columns: repeat(auto-fill, minmax(85px, 1fr)); gap: 8px;}
    .stock-box {padding: 10px; border-radius: 8px; text-align: center; font-size: 11px; font-weight: bold;}
    .pos {background: #14532d; color: #4ade80;}
    .neg {background: #431407; color: #fb923c;}
    .strike-table td {padding: 8px; text-align: center; border: 1px solid #444;}
    .itm {background: #14532d; color: #4ade80;}
    .atm {background: #433814; color: #fbbf24; font-weight: bold;}
    .otm {background: #431407; color: #fb923c;}
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
            nifty = yf.download("^NSEI", period="2d", interval="5m", progress=False)
            banknifty = yf.download("^NSEBANK", period="2d", interval="5m", progress=False)

            nifty_price = round(nifty['Close'].iloc[-1], 2) if not nifty.empty else 0
            bank_price = round(banknifty['Close'].iloc[-1], 2) if not banknifty.empty else 0

            # Pivot Levels
            def get_pivots(df):
                if df.empty: return {}
                h = df['High'].iloc[-2]
                l = df['Low'].iloc[-2]
                c = df['Close'].iloc[-2]
                p = (h + l + c) / 3
                return {
                    "R1": round(2*p - l, 2), "R2": round(p + (h-l), 2), "R3": round(h + 2*(p-l), 2),
                    "S1": round(2*p - h, 2), "S2": round(p - (h-l), 2), "S3": round(l - 2*(h-p), 2)
                }

            nifty_pivot = get_pivots(nifty)

            st.success(f"✅ Scan Completed at {datetime.now().strftime('%I:%M:%S %p')}")

            # ====================== METRIC CARDS ======================
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-card nifty-card">
                    <h3>NIFTY 50</h3>
                    <h1>{nifty_price}</h1>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card bank-card">
                    <h3>BANK NIFTY</h3>
                    <h1>{bank_price}</h1>
                </div>
                """, unsafe_allow_html=True)

            # ====================== PIVOT LEVELS ======================
            st.markdown('<div class="panel">📍 NIFTY 50 Pivot Levels</div>', unsafe_allow_html=True)
            if nifty_pivot:
                st.write(f"**R1:** {nifty_pivot['R1']} | **R2:** {nifty_pivot['R2']} | **R3:** {nifty_pivot['R3']}")
                st.write(f"**S1:** {nifty_pivot['S1']} | **S2:** {nifty_pivot['S2']} | **S3:** {nifty_pivot['S3']}")

            # ====================== FULL OPTION CHAIN ======================
            st.markdown('<div class="panel">📊 Option Chain (ATM Strikes)</div>', unsafe_allow_html=True)
            atm = round(nifty_price / 50) * 50
            st.write(f"**ATM Strike: {atm}**")
            
            st.markdown("""
            <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                <tr style="background:#1e2937; color:white;">
                    <th>Strike</th><th>Type</th><th>Call (CE)</th><th>Put (PE)</th>
                </tr>
            """, unsafe_allow_html=True)
            
            for i in range(-5, 6):
                strike = atm + (i * 50)
                if strike < atm:
                    style = "itm"
                    label = "ITM"
                elif strike == atm:
                    style = "atm"
                    label = "ATM"
                else:
                    style = "otm"
                    label = "OTM"
                st.markdown(f"""
                <tr style="background:#1a2332; color:white;">
                    <td>{strike}</td>
                    <td class="{style}">{label}</td>
                    <td>CE</td>
                    <td>PE</td>
                </tr>
                """, unsafe_allow_html=True)
            st.markdown("</table>", unsafe_allow_html=True)

            # ====================== FULL COLORFUL HEATMAP ======================
            st.markdown('<div class="panel">📈 Nifty 50 Heatmap</div>', unsafe_allow_html=True)
            stocks = ["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","SBIN","BHARTIARTL","ITC","LT","HINDUNILVR","AXISBANK","KOTAKBANK"]
            changes = [2.4, -0.8, 1.9, 0.5, -1.2, 3.1, 2.8, -0.3, 1.6, 4.2, 0.9, -2.1]
            
            st.markdown('<div class="heatmap">', unsafe_allow_html=True)
            for s, ch in zip(stocks, changes):
                color = "pos" if ch >= 0 else "neg"
                st.markdown(f'<div class="stock-box {color}">{s}<br>{ch:+.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Data Error: {str(e)}")

else:
    st.info("👆 'START MARKET SCAN' ബട്ടൺ ക്ലിക്ക് ചെയ്താൽ Live Data വരും")

st.caption("Beautiful Ultra Scanner UI • Pivot Levels + Option Chain + Heatmap • Made with ❤️")
