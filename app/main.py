"""
Modern trading bot interface.
Simplified, clean, value-driven Streamlit app entry point.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config
from app.core.logger import setup_logger
from app.core.database import get_database_manager
from app.ui.modern_dashboard import (
    apply_ui_theme,
    render_header,
    render_sidebar,
    render_dashboard_tab,
    render_positions_tab,
    render_analysis_tab,
    render_settings_tab,
    render_logs_tab,
    render_statement_tab,
)

logger = setup_logger("modern_ui_main")

# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="T",
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


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    apply_ui_theme()
    
    # Render header with status
    render_header()
    render_sidebar()
    
    # Main navigation
    st.markdown("---")
    
    # Create tabs for main sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Dashboard",
        "Positions",
        "Analysis",
        "Settings",
        "Logs",
        "Statement",
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
    
    with tab6:
        render_statement_tab()


if __name__ == "__main__":
    main()
    
    # Auto-refresh every 5 seconds
    import time
    placeholder = st.empty()
    with placeholder:
        st.caption(f"🔄 Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    time.sleep(5)
    st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 15px; font-size: 0.9em;'>
        <p>AI Trading Bot Dashboard | v1.0.0</p>
        <p>MetaTrader5 Integration | Advanced Risk Management</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
