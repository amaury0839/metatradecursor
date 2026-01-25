"""Simple Streamlit UI - connects to local API without async issues"""

import streamlit as st
import requests
import os
from datetime import datetime
import time

# Configure page
st.set_page_config(
    page_title="AI Forex Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API URL
API_URL = os.getenv("TRADING_BOT_API_URL", "http://localhost:8000")

# Cache API client
@st.cache_resource
def get_api():
    """Get API client instance"""
    return API_URL

api_url = get_api()

# Title
st.title("🤖 AI Forex Trading Bot")
st.markdown(f"**API Endpoint:** {api_url}")

# Check API connection
try:
    response = requests.get(f"{api_url}/", timeout=2)
    if response.status_code == 200:
        st.success("✅ API Connected", icon="✅")
    else:
        st.error("❌ API Error", icon="❌")
except Exception as e:
    st.error(f"❌ Cannot connect to API: {str(e)}", icon="❌")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page:", 
                   ["Dashboard", "Configuration", "Strategy", "Risk Management", "News", "Logs"],
                   index=0)

# Main content based on page selection
if page == "Dashboard":
    st.header("📊 Dashboard")
    
    # Get both connection and trading status
    connection_data = None
    trading_data = None
    
    try:
        # Get MT5 connection status
        resp_conn = requests.get(f"{api_url}/status/connection", timeout=2)
        if resp_conn.status_code == 200:
            connection_data = resp_conn.json()
        
        # Get trading status
        resp_trade = requests.get(f"{api_url}/status/trading", timeout=2)
        if resp_trade.status_code == 200:
            trading_data = resp_trade.json()
        
        if connection_data and trading_data:
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                balance = trading_data.get('balance', 0)
                st.metric("Account Balance", f"${balance:.2f}")
            
            with col2:
                equity = trading_data.get('equity', 0)
                st.metric("Equity", f"${equity:.2f}")
            
            with col3:
                open_pos = trading_data.get('open_positions', 0)
                st.metric("Open Positions", open_pos)
            
            with col4:
                is_connected = connection_data.get('connected', False)
                status = "🟢 Online" if is_connected else "🔴 Offline"
                st.metric("MT5 Status", status)
            
            st.divider()
            
            # Trading state
            is_trading_active = not trading_data.get('kill_switch_active', True)
            if is_connected and is_trading_active:
                st.success("🟢 **Trading is ACTIVE** - Bot is monitoring markets", icon="✅")
            elif is_connected and not is_trading_active:
                st.warning("🟡 **Trading is PAUSED** - Kill switch is active", icon="⚠️")
            elif not is_connected:
                st.error("🔴 **MT5 DISCONNECTED** - Cannot trade", icon="❌")
            
            st.divider()
            
            # Account info
            if connection_data.get('account_info'):
                account = connection_data['account_info']
                st.subheader("📋 Account Details")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.write(f"**Login:** {account.get('login', 'N/A')}")
                    st.write(f"**Mode:** {account.get('trade_mode', 'N/A')}")
                
                with col_info2:
                    st.write(f"**Leverage:** {account.get('leverage', 'N/A')}:1")
                    st.write(f"**Margin Mode:** {account.get('margin_so_mode', 'N/A')}")
                
                with col_info3:
                    st.write(f"**Currency:** {account.get('currency', 'N/A')}")
                    st.write(f"**Server:** {connection_data.get('mode', 'N/A')}")
                
    except Exception as e:
        st.error(f"Error fetching dashboard: {str(e)}")

elif page == "Configuration":
    st.header("⚙️ Configuration")
    st.info("Configuration management coming soon...")
    
elif page == "Strategy":
    st.header("📈 Strategy")
    st.info("Strategy settings coming soon...")
    
elif page == "Risk Management":
    st.header("⚠️ Risk Management")
    st.info("Risk management settings coming soon...")
    
elif page == "News":
    st.header("📰 News & Sentiment")
    st.info("News feed coming soon...")
    
elif page == "Logs":
    st.header("📋 Logs")
    st.info("System logs coming soon...")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
