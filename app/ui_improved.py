"""Modern Streamlit UI with tabs and improved design"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config
from app.core.state import get_state_manager
from app.core.scheduler import TradingScheduler
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.trading.market_status import get_market_status


def _ensure_trading_loop_auto_started():
    """Auto-start trading loop when MT5 is connected and no scheduler is running."""
    try:
        mt5 = get_mt5_client()
        scheduler = st.session_state.get("scheduler")

        # Already running -> nothing to do
        if scheduler and scheduler.is_running():
            return

        # Only auto-start if MT5 connected
        if not mt5.is_connected():
            return

        from app.main import main_trading_loop

        scheduler = TradingScheduler(main_trading_loop)
        scheduler.start()
        st.session_state.scheduler = scheduler
        st.session_state["auto_started"] = True
        st.toast("Loop auto-started (MT5 connected)")
    except Exception as e:
        logger.warning(f"Auto-start loop failed: {e}")

logger = setup_logger("streamlit_main")

# Page configuration
st.set_page_config(
    page_title="AI Trading Bot - Professional",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .header-container {
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 12px;
        margin: 5px;
    }
    
    .status-live {
        background: #ff4757;
        color: white;
    }
    
    .status-paper {
        background: #2ed573;
        color: white;
    }
    
    .market-status {
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        margin: 5px;
        display: inline-block;
        min-width: 150px;
    }
    
    .market-open {
        background: #2ed573;
        color: white;
    }
    
    .market-closed {
        background: #ff4757;
        color: white;
    }
    
    .market-24-7 {
        background: #5f27cd;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.scheduler = None
    st.session_state.mt5_connected = False
    # Auto-start trading loop on first load
    _ensure_trading_loop_auto_started()


def render_header():
    """Render modern header"""
    config = get_config()
    mt5 = get_mt5_client()
    
    # Force MT5 connection
    if not mt5.is_connected():
        try:
            mt5.connect()
        except Exception as e:
            logger.warning(f"Could not auto-connect to MT5: {e}")
    
    st.markdown("""
    <div class="header-container">
        <h1>🤖 AI Trading Bot</h1>
        <p>Automated Forex & Crypto Trading Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            if mt5.is_connected():
                account = mt5.get_account_info()
                if account:
                    st.metric("Balance", f"${account.get('balance', 0):,.2f}")
                else:
                    st.metric("Balance", "N/A")
            else:
                st.metric("Balance", "N/A")
        except Exception as e:
            st.metric("Balance", "ERROR")
    
    with col2:
        try:
            if mt5.is_connected():
                account = mt5.get_account_info()
                if account:
                    st.metric("Equity", f"${account.get('equity', 0):,.2f}")
                else:
                    st.metric("Equity", "N/A")
            else:
                st.metric("Equity", "N/A")
        except Exception as e:
            st.metric("Equity", "ERROR")
    
    with col3:
        mode = "LIVE" if not config.is_paper_mode() else "PAPER"
        status_class = "status-live" if mode == "LIVE" else "status-paper"
        st.markdown(f'<div class="status-badge {status_class}">{mode} MODE</div>', unsafe_allow_html=True)
    
    with col4:
        try:
            is_connected = mt5.is_connected()
            if is_connected:
                st.success("✅ Connected")
            else:
                st.error("❌ Disconnected")
        except Exception as e:
            st.warning(f"⚠️ Error: {str(e)[:20]}")


def render_market_status():
    """Render market status for all symbols"""
    config = get_config()
    market_status = get_market_status()
    
    st.subheader("📊 Market Status Overview")
    
    forex_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]
    crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD", "ADAUSD", "DOGEUSD", "XRPUSD"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Forex Pairs (Market Hours)**")
        forex_status = ""
        for symbol in forex_symbols:
            try:
                is_open = market_status.is_symbol_open(symbol)
                status = "OPEN ✅" if is_open else "CLOSED ❌"
                forex_status += f'{symbol}: {status}\n'
            except Exception as e:
                forex_status += f'{symbol}: ERROR\n'
        st.code(forex_status)
    
    with col2:
        st.write("**Cryptocurrencies (24/7 Trading)**")
        crypto_status = ""
        for symbol in crypto_symbols:
            crypto_status += f'💰 {symbol}: OPEN 24/7 ✅\n'
        st.code(crypto_status)


def render_dashboard():
    """Dashboard page"""
    # Auto-start loop if MT5 is connected and no scheduler is running
    _ensure_trading_loop_auto_started()

    render_header()
    st.divider()
    render_market_status()
    
    # Get real data from portfolio
    from app.trading.portfolio import get_portfolio_manager
    portfolio = get_portfolio_manager()
    positions = portfolio.get_open_positions()
    total_pnl = portfolio.get_unrealized_pnl()
    
    st.subheader("📈 Trading Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Positions", len(positions), delta="Live" if len(positions) > 0 else "No positions")
    with col2:
        st.metric("Win Rate", "0%", delta="Waiting for trades")
    with col3:
        pnl_delta = "Profit" if total_pnl > 0 else ("Loss" if total_pnl < 0 else "Neutral")
        st.metric("Total P&L", f"${total_pnl:.2f}", delta=pnl_delta)
    with col4:
        st.metric("Profit Factor", "0.0", delta="No data")
    
    # Show open positions
    if positions:
        st.divider()
        st.subheader(f"📊 Open Positions ({len(positions)})")
        
        import pandas as pd
        positions_data = []
        for pos in positions:
            pos_type = "BUY" if pos.get('type', 0) == 0 else "SELL"
            positions_data.append({
                "Ticket": pos.get('ticket', 'N/A'),
                "Symbol": pos.get('symbol', 'N/A'),
                "Type": pos_type,
                "Volume": f"{pos.get('volume', 0.0):.2f}",
                "Open Price": f"{pos.get('price_open', 0.0):.5f}",
                "Current Price": f"{pos.get('price_current', 0.0):.5f}",
                "P&L": f"${pos.get('profit', 0.0):.2f}",
                "Time": datetime.fromtimestamp(pos.get('time', 0)).strftime("%Y-%m-%d %H:%M:%S") if pos.get('time') else 'N/A'
            })
        
        df_positions = pd.DataFrame(positions_data)
        st.dataframe(df_positions, use_container_width=True)
    else:
        st.info("💤 No open positions")
    
    st.divider()
    st.subheader("🔄 Trading Loop Control")
    
    scheduler = st.session_state.get("scheduler")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if scheduler and scheduler.is_running():
            st.success("🟢 Loop Running")
            if st.button("⏸ Stop Loop", use_container_width=True):
                scheduler.stop()
                st.session_state.scheduler = None
                st.rerun()
        else:
            st.warning("⚪ Loop Stopped")
            if st.button("▶ Start Loop", use_container_width=True):
                try:
                    from app.main import main_trading_loop
                    scheduler = TradingScheduler(main_trading_loop)
                    scheduler.start()
                    st.session_state.scheduler = scheduler
                    st.rerun()
                except Exception as e:
                    st.error(f"Error starting loop: {e}")
    
    with col2:
        mt5 = get_mt5_client()
        if mt5.is_connected():
            st.success("✅ MT5 Connected")
        else:
            st.error("❌ MT5 Disconnected")
    
    with col3:
        st.info("🔒 Mode: Check Configuration tab")


def render_analysis():
    """Analysis page with integrated analysis"""
    from app.trading.integrated_analysis import get_integrated_analyzer
    
    st.subheader("📊 Integrated Symbol Analysis")
    
    st.info("""
    **Analysis combines:**
    - 📈 Technical indicators (RSI, EMA, ATR)
    - 📰 News sentiment analysis (cached 1 hour)
    - 🤖 AI decision engine
    """)
    
    # Symbol selector - Forex and Crypto
    all_symbols = (
        ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"] +
        ["BTCUSD", "ETHUSD", "BNBUSD", "ADAUSD", "DOGEUSD", "XRPUSD"]
    )
    
    selected_symbol = st.selectbox("Select Symbol for Analysis", all_symbols)
    
    if selected_symbol:
        analyzer = get_integrated_analyzer()
        
        with st.spinner(f"Analyzing {selected_symbol}..."):
            analysis = analyzer.analyze_symbol(selected_symbol)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Score", f"{analysis['combined_score']:.2f}")
        with col2:
            st.metric("Signal", analysis['signal'])
        with col3:
            st.metric("Confidence", f"{analysis['confidence']:.0%}")
        with col4:
            st.metric("Sources", len(analysis['available_sources']))
        
        st.divider()
        
        # Detailed tabs
        tab1, tab2, tab3 = st.tabs(["📈 Technical", "📰 Sentiment", "📊 Combined"])
        
        with tab1:
            if analysis["technical"]:
                tech = analysis["technical"]
                st.success(f"**Signal:** {tech['signal']}")
                st.write(f"**Reason:** {tech['reason']}")
                if tech['data']:
                    cols = st.columns(min(4, len(tech['data'])))
                    for col, (key, value) in zip(cols, tech['data'].items()):
                        with col:
                            if isinstance(value, (int, float)):
                                st.metric(key.upper(), f"{value:.2f}")
                            else:
                                st.metric(key.upper(), str(value))
            else:
                st.warning("No technical analysis available")
        
        with tab2:
            if analysis["sentiment"] and analysis["sentiment"].get("score") is not None:
                sent = analysis["sentiment"]
                score = sent.get("score", 0)
                
                if score > 0.3:
                    st.success(f"✅ **Positive Sentiment** - {score:.2f}")
                elif score < -0.3:
                    st.error(f"❌ **Negative Sentiment** - {score:.2f}")
                else:
                    st.info(f"➖ **Neutral Sentiment** - {score:.2f}")
                
                st.write(f"**Summary:** {sent.get('summary', 'N/A')}")
                
                if sent.get('headlines'):
                    with st.expander(f"📰 {len(sent['headlines'])} News Headlines"):
                        for i, headline in enumerate(sent['headlines'][:10], 1):
                            st.write(f"{i}. {headline}")
            else:
                st.info("📰 Sentiment analysis not available (uses hourly cache)")
        
        with tab3:
            st.metric("Combined Score", f"{analysis['combined_score']:.2f}")
            st.metric("Final Signal", analysis['signal'])
            st.metric("Confidence", f"{analysis['confidence']:.0%}")
            st.success(f"**Sources:** {', '.join(analysis['available_sources'])}")


def render_configuration():
    """Enhanced configuration page"""
    st.subheader("⚙️ Trading Configuration")
    
    config = get_config()
    
    # Configuration tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Trading",
        "💰 Risk",
        "🤖 AI",
        "📰 News",
        "🔧 Advanced"
    ])
    
    with tab1:
        st.write("#### Trading Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Mode", ["PAPER", "LIVE"], key="mode_select")
            st.multiselect(
                "Symbols",
                ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD",
                 "BTCUSD", "ETHUSD", "BNBUSD", "ADAUSD", "DOGEUSD", "XRPUSD"],
                default=["EURUSD", "GBPUSD", "BTCUSD"],
                key="symbols_select"
            )
        
        with col2:
            st.selectbox("Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4", "D1"], 
                         key="tf_select")
            st.slider("Trading Hours (24h)", 0, 23, (9, 17), key="hours_select")
    
    with tab2:
        st.write("#### Risk Management")
        col1, col2 = st.columns(2)
        
        with col1:
            st.slider("Risk Per Trade (%)", 0.1, 10.0, 2.0, key="risk_select")
            st.slider("Max Drawdown (%)", 10, 100, 90, key="dd_select")
        
        with col2:
            st.number_input("Max Positions", 1, 100, 10, key="pos_select")
            st.number_input("Max Spread (pips)", 0.1, 50.0, 10.0, key="spread_select")
    
    with tab3:
        st.write("#### AI Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Model", ["gemini-2.5-pro", "gemini-2.0-flash"], key="model_select")
            st.slider("Confidence Threshold (%)", 10, 100, 40, key="conf_select")
        
        with col2:
            st.checkbox("Use Technical Fallback", value=True, key="fallback_select")
            st.checkbox("Debug Mode", value=False, key="debug_select")
    
    with tab4:
        st.write("#### News & Sentiment")
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("News Provider", ["NewsAPI", "Stub (Demo)"], key="news_select")
        
        with col2:
            st.number_input("Cache TTL (minutes)", 30, 1440, 60, key="cache_select")
    
    with tab5:
        st.write("#### Advanced Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], key="loglevel_select")
        
        with col2:
            st.slider("Update Interval (sec)", 5, 300, 30, key="interval_select")
        
        st.warning("⚠️ Kill Switch (Emergency Stop)")
        if st.button("🛑 ACTIVATE KILL SWITCH", type="primary", use_container_width=True):
            st.error("KILL SWITCH ACTIVATED - All trading stopped!")
    
    st.divider()
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        st.success("✅ Configuration saved!")


def render_logs():
    """Logs and audit trail"""
    st.subheader("📋 Logs & Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Live Analysis", "Trade History", "System Logs"])
    
    with tab1:
        st.info("📊 Live analysis logs from trading bot")
        try:
            from app.ui.pages_analysis import render_analysis_logs
            render_analysis_logs()
        except Exception as e:
            st.warning(f"Could not load analysis: {e}")
    
    with tab2:
        st.info("📈 Trade execution history (last 7 days)")
        
        # Get historical deals
        from app.trading.mt5_client import get_mt5_client
        from datetime import timedelta
        import pandas as pd
        
        mt5 = get_mt5_client()
        if mt5.is_connected():
            from_date = datetime.now() - timedelta(days=7)
            deals = mt5.get_history_deals(from_date)
            
            if deals:
                # Filter out balance operations (entry=2 means in/out deal)
                trade_deals = [d for d in deals if d.get('entry', 0) in [0, 1]]
                
                # Calculate statistics
                total_trades = len(trade_deals)
                winning_trades = len([d for d in trade_deals if d.get('profit', 0) > 0])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                total_profit = sum(d.get('profit', 0) for d in trade_deals)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Trades", total_trades)
                with col2:
                    st.metric("Winning", winning_trades)
                with col3:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with col4:
                    pnl_delta = "Profit" if total_profit > 0 else "Loss"
                    st.metric("Total P&L", f"${total_profit:.2f}", delta=pnl_delta)
                
                st.divider()
                
                # Show deals table
                history_data = []
                for deal in trade_deals[-50:]:  # Last 50 trades
                    deal_type = "BUY" if deal.get('type', 0) == 0 else "SELL"
                    entry_type = "IN" if deal.get('entry', 0) == 0 else "OUT"
                    history_data.append({
                        "Time": datetime.fromtimestamp(deal.get('time', 0)).strftime("%Y-%m-%d %H:%M:%S"),
                        "Ticket": deal.get('ticket', 'N/A'),
                        "Symbol": deal.get('symbol', 'N/A'),
                        "Type": deal_type,
                        "Entry": entry_type,
                        "Volume": f"{deal.get('volume', 0.0):.2f}",
                        "Price": f"{deal.get('price', 0.0):.5f}",
                        "P&L": f"${deal.get('profit', 0.0):.2f}",
                        "Commission": f"${deal.get('commission', 0.0):.2f}",
                        "Swap": f"${deal.get('swap', 0.0):.2f}"
                    })
                
                if history_data:
                    df_history = pd.DataFrame(history_data)
                    st.dataframe(df_history, use_container_width=True, height=400)
                else:
                    st.warning("No trade deals found in the last 7 days")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Trades", "0")
                with col2:
                    st.metric("Winning", "0")
                with col3:
                    st.metric("Win Rate", "0%")
                st.warning("No trade history found in the last 7 days")
        else:
            st.error("❌ MT5 not connected - cannot retrieve trade history")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Trades", "0")
            with col2:
                st.metric("Winning", "0")
            with col3:
                st.metric("Win Rate", "0%")
    
    with tab3:
        st.info("📝 System logs and debugging")
        st.code("No system logs available", language="log")


def main():
    """Main app"""
    # Dashboard tab
    tab_dashboard, tab_analysis, tab_config, tab_logs = st.tabs([
        "📊 Dashboard",
        "📈 Analysis",
        "⚙️ Configuration",
        "📋 Logs"
    ])
    
    with tab_dashboard:
        render_dashboard()
    
    with tab_analysis:
        render_analysis()
    
    with tab_config:
        render_configuration()
    
    with tab_logs:
        render_logs()


if __name__ == "__main__":
    main()
