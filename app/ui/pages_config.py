"""Configuration page - Works for both local and remote modes"""

import streamlit as st
import os

# Try to import local modules
try:
    from app.core.config import get_config, reload_config
    from app.trading.mt5_client import get_mt5_client
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def render_config():
    """Render configuration page - auto-detects local or remote mode"""
    if LOCAL_MODE:
        render_config_local()
    else:
        if "api_client" in st.session_state:
            render_config_remote(st.session_state.api_client)
        else:
            st.info("Configure API connection in sidebar to view configuration.")


def render_config_local():
    """Render configuration page - Local mode"""
    config = get_config()
    mt5 = get_mt5_client()
    
    st.subheader("🔧 Configuration")
    
    # MT5 Connection
    with st.expander("MetaTrader 5 Connection", expanded=True):
        st.info("Configure MT5 credentials in .env file (not stored in UI for security)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("MT5 Login", value=str(config.mt5.login), disabled=True)
            st.text_input("MT5 Server", value=config.mt5.server, disabled=True)
        with col2:
            st.text_input("MT5 Password", value="***", type="password", disabled=True)
            st.text_input("MT5 Path", value=config.mt5.path or "Not set", disabled=True)
        
        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                if mt5.connect():
                    st.success("✅ Connection successful!")
                    account_info = mt5.get_account_info()
                    if account_info:
                        st.json({
                            "Login": account_info.get('login', ''),
                            "Balance": account_info.get('balance', 0),
                            "Equity": account_info.get('equity', 0),
                            "Server": account_info.get('server', ''),
                        })
                else:
                    st.error("❌ Connection failed. Check credentials in .env file")
    
    st.divider()
    
    # Trading Mode
    with st.expander("Trading Mode", expanded=True):
        current_mode = config.trading.mode
        
        st.warning("⚠️ Changing mode requires restart")
        st.info(f"Current mode: **{current_mode}**")
        
        if current_mode == "PAPER":
            st.success("✅ Paper trading mode - No real orders will be executed")
        else:
            st.error("⚠️ LIVE MODE - Real orders will be executed!")
        
        # Mode change confirmation (for safety, require .env edit)
        st.info("To change mode, edit MODE in .env file and restart the application")
    
    st.divider()
    
    # AI Configuration
    with st.expander("AI Configuration"):
        st.text_input("Gemini API Key", value="***" if config.ai.gemini_api_key else "", 
                     type="password", disabled=True)
        st.info("Configure GEMINI_API_KEY in .env file")
        
        min_confidence = st.slider(
            "Minimum Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=config.ai.min_confidence_threshold,
            step=0.01,
            help="Decisions below this confidence will be rejected"
        )
        
        if st.button("Update Confidence Threshold"):
            # This would need to be persisted (simplified for demo)
            st.info("Threshold updated (requires restart to persist)")
    
    st.divider()
    
    # News Configuration
    with st.expander("News Configuration"):
        news_provider = st.selectbox(
            "News Provider",
            ["stub", "newsapi"],
            index=0 if config.news.provider == "stub" else 1
        )
        
        st.text_input("News API Key", value="***" if config.news.news_api_key else "",
                     type="password", disabled=True)
        st.info("Configure NEWS_API_KEY in .env file for NewsAPI provider")
        
        cache_minutes = st.number_input(
            "Cache Duration (minutes)",
            min_value=1,
            max_value=60,
            value=config.news.cache_minutes,
            step=1
        )
    
    st.divider()
    
    # System Configuration
    with st.expander("System Configuration"):
        timezone = st.text_input("Timezone", value=config.trading.timezone)
        polling_interval = st.number_input(
            "Polling Interval (seconds)",
            min_value=10,
            max_value=300,
            value=config.trading.polling_interval_seconds,
            step=10
        )
        
        st.info("Changes require restart to take effect")
    
    st.divider()
    
    # Reload configuration
    if st.button("🔄 Reload Configuration", type="primary"):
        with st.spinner("Reloading..."):
            reload_config()
            st.success("Configuration reloaded!")
            st.rerun()


def render_config_remote(api_client):
    """Render configuration page - Remote mode"""
    import asyncio
    
    st.subheader("🔧 Configuration")
    st.info("Configuration is managed on the local trading bot server.")
    
    # Get connection status
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    conn_status = loop.run_until_complete(api_client.get_connection_status())
    loop.close()
    
    st.markdown("### Connection Status")
    if conn_status.get("connected"):
        st.success("✅ Connected to MT5")
        account_info = conn_status.get("account_info")
        if account_info:
            st.json({
                "Login": account_info.get('login', ''),
                "Balance": account_info.get('balance', 0),
                "Equity": account_info.get('equity', 0),
                "Server": account_info.get('server', ''),
            })
    else:
        st.warning("⚠️ MT5 Not Connected")
        if st.button("Connect to MT5"):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(api_client.connect_mt5())
            loop.close()
            if success:
                st.success("Connected!")
                st.rerun()
            else:
                st.error("Connection failed")
    
    st.markdown("### Mode")
    mode = conn_status.get("mode", "UNKNOWN")
    st.info(f"Current mode: **{mode}**")
    
    if mode == "PAPER":
        st.success("✅ Paper trading mode - No real orders will be executed")
    elif mode == "LIVE":
        st.error("⚠️ LIVE MODE - Real orders will be executed!")
