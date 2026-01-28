"""
🎨 MODERN TRADING BOT INTERFACE
Simplified, clean, value-driven Streamlit app entry point
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import MetaTrader5 as mt5

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config
from app.core.logger import setup_logger
from app.core.database import get_database_manager
from app.trading.mt5_client import get_mt5_client
from app.ui.modern_dashboard import (
    render_header,
    render_dashboard_tab,
    render_positions_tab,
    render_analysis_tab,
    render_settings_tab,
    render_logs_tab
)

logger = setup_logger("modern_ui_main")

# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="🤖 Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/amaury0839/metatradecursor",
        "About": "AI-Powered Forex Trading Bot"
    }
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.config = get_config()
    st.session_state.db = get_database_manager()
    st.session_state.mt5_connected = False
    try:
        mt5_client = get_mt5_client()
        st.session_state.mt5_connected = mt5_client.is_connected()
    except Exception as e:
        logger.error(f"Failed to initialize MT5: {e}")
        st.session_state.mt5_connected = False


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    # Render header with status
    render_header()
    
    # Main navigation
    st.markdown("---")
    
    # Create tabs for main sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🔓 Positions",
        "📉 Analysis",
        "⚙️ Settings",
        "📋 Logs"
    ])
    
    with tab1:
        render_dashboard_tab()
    
    with tab2:
        render_positions_tab()
    
    with tab3:
        render_analysis_tab()
    
    with tab4:
        render_settings_tab()
    
    with tab5:
        render_logs_tab()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 15px; font-size: 0.9em;'>
        <p>🤖 AI Trading Bot Dashboard | v1.0.0</p>
        <p>MetaTrader5 Integration | Advanced Risk Management</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
