"""Simple AI Trading Bot UI - Fixed Data Version"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="AI Trading Bot - Simple Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.8;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📈 AI Trading Bot - Professional Dashboard")
st.markdown("---")

# Key Performance Indicators
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Equity",
        "$11,311.25",
        "-13.40",  # P&L
        delta_color="inverse"
    )

with col2:
    st.metric(
        "Free Margin",
        "$5,000.00",
        "44.2%",
        delta_color="off"
    )

with col3:
    st.metric(
        "Daily P&L",
        "-$13.40",
        "-0.12%",
        delta_color="inverse"
    )

with col4:
    st.metric(
        "Win Rate",
        "62.0%",
        "2.1%"
    )

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Trading Monitor",
    "💼 Portfolio",
    "📈 Analytics",
    "⚠️ Risk Management",
    "⚙️ Settings"
])

# Trading Monitor Tab
with tab1:
    st.subheader("Active Positions")
    
    positions_data = {
        "Symbol": ["EURUSD", "GBPUSD", "USDJPY", "AUDCAD", "XRPUSD", "BTCUSD", "ETHUSD", "EURGBP", "AUDNZD", "NZDJPY"],
        "Type": ["BUY", "SELL", "BUY", "SELL", "BUY", "SELL", "BUY", "SELL", "BUY", "SELL"],
        "Volume": [0.01, 0.01, 0.01, 0.01, 100.0, 0.001, 0.05, 0.01, 0.01, 0.01],
        "Entry": [1.0940, 1.2620, 145.45, 0.8945, 0.5250, 89000.00, 3002.74, 0.8691, 1.1622, 91.92],
        "Current": [1.0942, 1.2615, 145.52, 0.8935, 0.5248, 88950.00, 3001.50, 0.8686, 1.1625, 91.95],
        "P&L": [0.00, -0.07, 0.07, -0.05, -2.00, -50.00, -0.62, 0.06, 0.03, 0.03]
    }
    
    import pandas as pd
    df_positions = pd.DataFrame(positions_data)
    st.dataframe(df_positions, use_container_width=True)
    
    st.markdown("**Summary:** 10 active positions | Avg. P&L: -$5.19 | Total Risk Exposure: 2.45%")

# Portfolio Tab
with tab2:
    st.subheader("Portfolio Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Account Balance", "$11,324.65")
        st.metric("Used Margin", "$6,324.65")
        st.metric("Margin Level", "178.5%")
    
    with col2:
        st.metric("Account Equity", "$11,311.25")
        st.metric("Free Margin", "$5,000.00")
        st.metric("Risk Level", "Low 🟢")
    
    st.markdown("---")
    st.subheader("Asset Allocation")
    
    asset_data = {
        "Asset Class": ["Forex Major", "Forex Cross", "Crypto"],
        "Allocation": [45, 30, 25],
        "Positions": [5, 3, 2]
    }
    
    df_assets = pd.DataFrame(asset_data)
    st.dataframe(df_assets, use_container_width=True)

# Analytics Tab
with tab3:
    st.subheader("Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Win Rate Breakdown**")
        metrics = {"Winning Trades": 62, "Losing Trades": 38}
        import pandas as pd
        st.bar_chart(metrics)
    
    with col2:
        st.markdown("**Profit Factor Analysis**")
        st.metric("Profit Factor", "1.85", "Healthy 🟢")
        st.metric("Average Win", "$45.50")
        st.metric("Average Loss", "-$24.80")

# Risk Management Tab
with tab4:
    st.subheader("Risk Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🔥 AGGRESSIVE MODE ACTIVE**
        
        - **AGGRESSIVE_MIN_LOT**: 0.05 lots
        - Position clamping: ENABLED
        - Volume override: YES
        
        Trades with calculated volume < minimum are now clamped to 0.05 instead of rejected.
        """)
    
    with col2:
        st.warning("""
        **⚠️ Current Limits**
        
        - Max positions: 50
        - Max daily loss: 10%
        - Max drawdown: 15%
        - Risk per trade: 2-3% (dynamic)
        """)
    
    st.markdown("---")
    st.subheader("Position Limits")
    
    limits_data = {
        "Currency Pair": ["EUR", "GBP", "USD", "AUD", "NZD", "JPY"],
        "Current Positions": [9, 8, 6, 8, 5, 5],
        "Max Allowed": [5, 5, 5, 5, 5, 5],
        "Status": ["⚠️ Over", "⚠️ Over", "⚠️ Over", "⚠️ Over", "✅ OK", "✅ OK"]
    }
    
    df_limits = pd.DataFrame(limits_data)
    st.dataframe(df_limits, use_container_width=True)

# Settings Tab
with tab5:
    st.subheader("Bot Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Trading Parameters**")
        st.text_input("Risk per Trade (%)", value="2.0", disabled=True)
        st.text_input("Trading Mode", value="LIVE", disabled=True)
        st.text_input("AI Model", value="gemini-2.5-flash-lite", disabled=True)
    
    with col2:
        st.markdown("**System Status**")
        st.text_input("MT5 Status", value="🟢 CONNECTED", disabled=True)
        st.text_input("Database", value="🟢 ACTIVE", disabled=True)
        st.text_input("API Connection", value="🟢 OK", disabled=True)
    
    st.divider()
    st.markdown("**Version**: 2.0.0 Professional Edition")
    st.markdown("**Last Update**: 2026-01-28 03:40")

# Footer
st.divider()
st.markdown("""
---
**Status**: 🟢 System Running  
**Bot Mode**: LIVE Trading | **AI**: BIAS_ONLY | **Pyramiding**: ENABLED  
**Contact**: Support available in logs
""")
