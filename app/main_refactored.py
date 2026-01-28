"""
Refactored main.py - Clean UI/Trading separation
Version: 2.0 - Jan 28, 2026

Structure:
- UI setup and rendering (this file)
- Trading loop (app/trading/trading_loop.py) - SEPARATE
- Pages (app/ui/pages/*.py)
- Components (app/ui/components/)

This file: ~500 lines (down from 1,273)
Focus: UI only, clean routing, modular
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============= IMPORTS =============
# Core modules
from app.core.config import get_config, reload_config
from app.core.state import get_state_manager
from app.core.scheduler import TradingScheduler
from app.core.logger import setup_logger

# Trading modules (lazy loaded when needed)
from app.trading.mt5_client import get_mt5_client

# UI Pages
from app.ui.pages_dashboard import render_dashboard
from app.ui.pages_config import render_config
from app.ui.pages_strategy import render_strategy
from app.ui.pages_risk import render_risk
from app.ui.pages_news import render_news
from app.ui.pages_logs import render_logs
from app.ui.pages_analysis import render_analysis_logs

# Optional: Integrated analysis page
try:
    from app.ui.pages_integrated_analysis import render_integrated_analysis
    HAS_INTEGRATED_ANALYSIS = True
except ImportError:
    HAS_INTEGRATED_ANALYSIS = False

# Logging
logger = setup_logger("main_ui")

# ============= PAGE CONFIG =============
st.set_page_config(
    page_title="AI Forex Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= SESSION STATE INITIALIZATION =============
def _init_session_state():
    """Initialize session state variables"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.scheduler = None
        st.session_state.mt5_connected = False
        st.session_state.last_refresh = datetime.now()

_init_session_state()

# ============= SIDEBAR COMPONENTS =============
def render_connection_status():
    """Display connection status"""
    mt5 = get_mt5_client()
    config = get_config()
    
    col1, col2 = st.sidebar.columns([2, 1])
    
    if mt5.is_connected():
        col1.success("✅ MT5 Connected")
        account_info = mt5.get_account_info()
        if account_info:
            col2.metric("Equity", f"${account_info.get('equity', 0):,.0f}")
    else:
        col1.warning("⚠️ MT5 Disconnected")
        if col2.button("Connect"):
            with st.spinner("Connecting..."):
                mt5.connect()
                st.rerun()
    
    st.sidebar.divider()


def render_mode_indicator():
    """Display trading mode"""
    config = get_config()
    mode = config.trading.mode
    
    if mode == "LIVE":
        st.sidebar.error(f"🔴 LIVE MODE")
    elif mode == "PAPER":
        st.sidebar.warning(f"🟡 PAPER MODE")
    else:
        st.sidebar.info(f"🟢 {mode} MODE")


def render_kill_switch():
    """Display and manage kill switch"""
    state = get_state_manager()
    
    st.sidebar.subheader("🛑 Kill Switch")
    
    if state.is_kill_switch_active():
        st.sidebar.error("**ACTIVE** - All trading stopped")
        if st.sidebar.button("Deactivate", key="deactivate_kill"):
            state.deactivate_kill_switch()
            st.rerun()
    else:
        st.sidebar.success("Inactive")
        if st.sidebar.button("Activate", key="activate_kill", type="primary"):
            state.activate_kill_switch()
            st.rerun()
    
    st.sidebar.divider()


def render_trading_loop_control():
    """Display trading loop status and controls"""
    scheduler = st.session_state.get("scheduler")
    is_running = scheduler and scheduler.is_running() if scheduler else False
    
    st.sidebar.subheader("⚙️ Trading Loop")
    
    col1, col2 = st.sidebar.columns([2, 1])
    
    if is_running:
        col1.success("🟢 Running")
        if col2.button("Stop", key="stop_loop"):
            scheduler.stop()
            st.session_state.scheduler = None
            st.rerun()
    else:
        col1.info("⚪ Stopped")
        if col2.button("Start", key="start_loop"):
            try:
                # Lazy import to avoid circular dependencies
                from app.trading.trading_loop import main_trading_loop
                
                scheduler = TradingScheduler(main_trading_loop)
                scheduler.start()
                st.session_state.scheduler = scheduler
                st.rerun()
            except ImportError:
                st.error("Trading loop module not found")
    
    st.sidebar.divider()


def render_trading_symbols():
    """Display active trading symbols"""
    config = get_config()
    symbols = config.trading.default_symbols
    
    st.sidebar.subheader(f"📊 Symbols ({len(symbols)})")
    
    # Compact display
    cols = st.sidebar.columns(3)
    for i, symbol in enumerate(symbols):
        cols[i % 3].text(f"• {symbol}")


def render_sidebar():
    """Main sidebar rendering"""
    st.sidebar.title("🤖 AI Forex Trading Bot")
    
    # Status section
    render_connection_status()
    render_mode_indicator()
    render_kill_switch()
    
    # Trading section
    render_trading_loop_control()
    render_trading_symbols()
    
    # Footer
    st.sidebar.divider()
    st.sidebar.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")


# ============= PAGE NAVIGATION =============
def get_available_pages():
    """Get list of available pages"""
    pages = [
        "📊 Dashboard",
        "📋 Analysis Logs",
        "⚙️ Configuration",
        "📈 Strategy",
        "⚠️ Risk Management",
        "📰 News",
        "🔍 Logs & Audit",
    ]
    
    # Add integrated analysis if available
    if HAS_INTEGRATED_ANALYSIS:
        pages.insert(1, "🔗 Integrated Analysis")
    
    return pages


def render_page(page_name):
    """Render selected page"""
    try:
        if page_name == "📊 Dashboard":
            render_dashboard()
        elif page_name == "🔗 Integrated Analysis":
            if HAS_INTEGRATED_ANALYSIS:
                render_integrated_analysis()
        elif page_name == "📋 Analysis Logs":
            render_analysis_logs()
        elif page_name == "⚙️ Configuration":
            render_config()
        elif page_name == "📈 Strategy":
            render_strategy()
        elif page_name == "⚠️ Risk Management":
            render_risk()
        elif page_name == "📰 News":
            render_news()
        elif page_name == "🔍 Logs & Audit":
            render_logs()
        else:
            st.error(f"Unknown page: {page_name}")
    except Exception as e:
        st.error(f"Error rendering page: {e}")
        logger.error(f"Page render error: {e}", exc_info=True)


# ============= MAIN APP =============
def main():
    """Main Streamlit application"""
    
    # Render sidebar
    render_sidebar()
    
    # Page selection
    pages = get_available_pages()
    
    st.sidebar.divider()
    page = st.sidebar.radio(
        "📑 Navigation",
        pages,
        key="page_select"
    )
    
    # Page title
    st.title(page)
    
    # Render selected page
    render_page(page)


if __name__ == "__main__":
    main()
