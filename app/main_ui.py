"""Streamlit UI - Cloud version (connects to local API)"""

import streamlit as st
import sys
from pathlib import Path
import asyncio

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api_client.client import get_api_client
from app.ui.pages_dashboard import render_dashboard
from app.ui.pages_config import render_config
from app.ui.pages_strategy import render_strategy
from app.ui.pages_risk import render_risk
from app.ui.pages_news import render_news
from app.ui.pages_logs import render_logs

# Configure page
st.set_page_config(
    page_title="AI Forex Trading Bot - Remote UI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "api_client" not in st.session_state:
    # Get API URL from environment or use default
    import os
    api_url = os.getenv("TRADING_BOT_API_URL", "http://localhost:8000")
    st.session_state.api_client = get_api_client(api_url)
    st.session_state.api_available = False

# Make api_client available to pages
import streamlit as st
if "api_client" in st.session_state:
    # Pages will detect remote mode via this
    pass


def check_api_connection():
    """Check if API is available"""
    if "api_available" not in st.session_state:
        st.session_state.api_available = False
    
    try:
        # Use asyncio to check connection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        st.session_state.api_available = loop.run_until_complete(
            st.session_state.api_client.is_available()
        )
        loop.close()
    except Exception:
        st.session_state.api_available = False


def sidebar():
    """Render sidebar"""
    st.sidebar.title("🤖 AI Forex Trading Bot")
    st.sidebar.markdown("**Remote UI Mode**")
    
    # Check API connection
    check_api_connection()
    
    if st.session_state.api_available:
        st.sidebar.success("✅ Connected to Trading Bot")
        
        # Get connection status
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            conn_status = loop.run_until_complete(
                st.session_state.api_client.get_connection_status()
            )
            loop.close()
            
            if conn_status.get("connected"):
                st.sidebar.success("✅ MT5 Connected")
                account_info = conn_status.get("account_info")
                if account_info:
                    st.sidebar.metric("Equity", f"${account_info.get('equity', 0):,.2f}")
            else:
                st.sidebar.warning("⚠️ MT5 Disconnected")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")
    else:
        st.sidebar.error("❌ Not Connected to Trading Bot")
        st.sidebar.info("Start the local trading bot API server to connect")
        st.sidebar.code("python -m app.api.server")
    
    st.sidebar.divider()
    
    # API URL configuration
    st.sidebar.subheader("🔧 API Configuration")
    api_url = st.sidebar.text_input(
        "API URL",
        value=st.session_state.api_client.base_url,
        help="URL of the local trading bot API server"
    )
    
    if st.sidebar.button("Update API URL"):
        st.session_state.api_client = get_api_client(api_url)
        st.rerun()
    
    st.sidebar.divider()
    
    # Kill switch (if connected)
    if st.session_state.api_available:
        st.sidebar.subheader("🛑 Kill Switch")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trading_status = loop.run_until_complete(
                st.session_state.api_client.get_trading_status()
            )
            loop.close()
            
            if trading_status.get("kill_switch_active"):
                st.sidebar.error("**ACTIVE** - All trading stopped")
                if st.sidebar.button("Deactivate Kill Switch"):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        st.session_state.api_client.deactivate_kill_switch()
                    )
                    loop.close()
                    st.rerun()
            else:
                st.sidebar.success("Inactive")
                if st.sidebar.button("Activate Kill Switch", type="primary"):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        st.session_state.api_client.activate_kill_switch()
                    )
                    loop.close()
                    st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")


def main():
    """Main Streamlit app"""
    sidebar()
    
    if not st.session_state.api_available:
        st.warning("⚠️ **Not Connected to Trading Bot**")
        st.info("""
        This is the **Remote UI** mode. To use this interface:
        
        1. **Start the local trading bot API server** on your machine:
           ```bash
           python -m app.api.server
           ```
        
        2. **Ensure the API is accessible** from Streamlit Cloud:
           - If running locally: Use `http://localhost:8000`
           - If using a tunnel (ngrok, etc.): Use the tunnel URL
        
        3. **Configure the API URL** in the sidebar
        
        The trading bot must run locally with MetaTrader 5 installed.
        """)
        return
    
    # Page selection
    page = st.selectbox(
        "Navigation",
        ["Dashboard", "Configuration", "Strategy", "Risk Management", "News", "Logs/Audit"],
        key="page_select"
    )
    
    st.title(f"📈 {page}")
    
    # Render selected page (pages auto-detect remote mode via api_client in session_state)
    if page == "Dashboard":
        render_dashboard()
    elif page == "Configuration":
        render_config()
    elif page == "Strategy":
        render_strategy()
    elif page == "Risk Management":
        render_risk()
    elif page == "News":
        render_news()
    elif page == "Logs/Audit":
        render_logs()


if __name__ == "__main__":
    main()
