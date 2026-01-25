"""Streamlit main entry point - Local version (full trading bot)"""

import streamlit as st
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config, reload_config
from app.core.state import get_state_manager
from app.core.scheduler import TradingScheduler
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.ui.pages_dashboard import render_dashboard
from app.ui.pages_config import render_config
from app.ui.pages_strategy import render_strategy
from app.ui.pages_risk import render_risk
from app.ui.pages_news import render_news
from app.ui.pages_logs import render_logs

# Configure page
st.set_page_config(
    page_title="AI Forex Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = setup_logger("streamlit_main")


# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.scheduler = None
    st.session_state.mt5_connected = False
    # Auto-connect in demo mode
    try:
        import app.trading.mt5_client as mt5_module
        if not getattr(mt5_module, 'MT5_AVAILABLE', True):
            mt5_client = get_mt5_client()
            mt5_client.connect()
    except Exception:
        pass


def main_trading_loop():
    """Main trading loop callback"""
    try:
        from app.core.state import get_state_manager
        from app.trading.mt5_client import get_mt5_client
        from app.trading.data import get_data_provider
        from app.trading.strategy import get_strategy
        from app.trading.risk import get_risk_manager
        from app.trading.execution import get_execution_manager
        from app.trading.portfolio import get_portfolio_manager
        from app.ai.decision_engine import DecisionEngine
        from datetime import datetime
        
        state = get_state_manager()
        mt5 = get_mt5_client()
        data = get_data_provider()
        strategy = get_strategy()
        risk = get_risk_manager()
        execution = get_execution_manager()
        portfolio = get_portfolio_manager()
        decision_engine = DecisionEngine()
        config = get_config()
        
        # Check kill switch
        if state.is_kill_switch_active():
            return
        
        # Check connection - warn if not connected but continue with technical fallback
        if not mt5.is_connected():
            logger.warning("⚠️ MT5 not connected - using technical signals only")
            # Continue with technical signal processing instead of returning
        else:
            logger.info("✅ MT5 connected - using live account data")
        
        # Update account info
        account_info = mt5.get_account_info()
        if account_info:
            state.current_equity = account_info.get('equity', 0)
            state.current_balance = account_info.get('balance', 0)
            if state.current_equity > state.max_equity:
                state.max_equity = state.current_equity
        
        # Get symbols to trade (from config or UI state)
        symbols = config.trading.default_symbols
        timeframe = config.trading.default_timeframe
        
        # Process each symbol
        for symbol in symbols:
            try:
                # Check if we already have a position
                if portfolio.has_position(symbol):
                    # Could implement trailing stop or exit logic here
                    continue
                
                # Get technical signal
                signal, indicators, error = strategy.get_signal(symbol, timeframe)
                if error or signal == "HOLD":
                    continue
                
                # Get AI decision
                decision, prompt_hash, decision_error = decision_engine.make_decision(
                    symbol, timeframe, signal, indicators
                )
                
                if decision_error or not decision:
                    logger.warning(f"Decision engine error for {symbol}: {decision_error}")
                    continue
                
                # Check if decision is actionable
                if decision.action == "HOLD" or not decision.is_valid_for_execution():
                    continue
                
                # Run risk checks
                if decision.action in ["BUY", "SELL"]:
                    volume = decision.order.volume_lots if decision.order else 0.01
                    risk_ok, failures = risk.check_all_risk_conditions(
                        symbol, decision.action, volume
                    )
                    
                    if not risk_ok:
                        logger.info(f"Risk checks failed for {symbol}: {failures}")
                        # Save decision audit
                        from app.core.state import DecisionAudit
                        audit = DecisionAudit(
                            timestamp=datetime.now().isoformat(),
                            symbol=symbol,
                            timeframe=timeframe,
                            signal=signal,
                            confidence=decision.confidence,
                            action="HOLD",
                            reason=decision.reason + [f"Risk check failed: {', '.join(failures)}"],
                            prompt_hash=prompt_hash,
                            gemini_response=decision.model_dump(),
                            risk_checks_passed=False,
                        )
                        state.save_decision(audit)
                        continue
                    
                    # Execute order
                    tick = data.get_current_tick(symbol)
                    if not tick:
                        continue
                    
                    entry_price = tick.get('ask', 0) if decision.action == "BUY" else tick.get('bid', 0)
                    success, order_result, exec_error = execution.place_market_order(
                        symbol=symbol,
                        order_type=decision.action,
                        volume=volume,
                        sl_price=decision.order.sl_price,
                        tp_price=decision.order.tp_price,
                        comment=f"AI Bot - Confidence: {decision.confidence:.2f}"
                    )
                    
                    # Save decision audit
                    audit = DecisionAudit(
                        timestamp=datetime.now().isoformat(),
                        symbol=symbol,
                        timeframe=timeframe,
                        signal=signal,
                        confidence=decision.confidence,
                        action=decision.action,
                        volume_lots=volume,
                        sl_price=decision.order.sl_price,
                        tp_price=decision.order.tp_price,
                        reason=decision.reason,
                        prompt_hash=prompt_hash,
                        gemini_response=decision.model_dump(),
                        risk_checks_passed=True,
                        execution_success=success,
                        error_message=exec_error,
                    )
                    state.save_decision(audit)
                    
                    if success:
                        logger.info(f"Order executed: {decision.action} {volume} lots of {symbol}")
                    else:
                        logger.error(f"Order execution failed: {exec_error}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in trading loop: {e}", exc_info=True)


def sidebar():
    """Render sidebar"""
    st.sidebar.title("🤖 AI Forex Trading Bot")
    
    # Connection status
    mt5 = get_mt5_client()
    config = get_config()
    state = get_state_manager()
    
    # Check if MT5 is available (import after mt5_client is loaded)
    try:
        # Import after the module is loaded to avoid circular issues
        import app.trading.mt5_client as mt5_module
        MT5_AVAILABLE = getattr(mt5_module, 'MT5_AVAILABLE', False)
    except (ImportError, AttributeError):
        MT5_AVAILABLE = False
    
    if mt5.is_connected():
        if MT5_AVAILABLE:
            st.sidebar.success("✅ MT5 Connected")
        else:
            st.sidebar.info("🔄 Demo Mode (MT5 not available)")
        account_info = mt5.get_account_info()
        if account_info:
            st.sidebar.metric("Equity", f"${account_info.get('equity', 0):,.2f}")
    else:
        if MT5_AVAILABLE:
            st.sidebar.error("❌ MT5 Disconnected")
            if st.sidebar.button("Connect to MT5"):
                with st.spinner("Connecting..."):
                    if mt5.connect():
                        st.rerun()
        else:
            st.sidebar.info("🔄 Demo Mode - Auto-connected")
    
    st.sidebar.divider()
    
    # Mode
    mode = config.trading.mode
    st.sidebar.markdown(f"**Mode:** {mode}")
    
    if mode == "LIVE":
        st.sidebar.warning("⚠️ LIVE MODE ACTIVE")
    
    st.sidebar.divider()
    
    # Kill switch
    st.sidebar.subheader("🛑 Kill Switch")
    if state.is_kill_switch_active():
        st.sidebar.error("**ACTIVE** - All trading stopped")
        if st.sidebar.button("Deactivate Kill Switch"):
            state.deactivate_kill_switch()
            st.rerun()
    else:
        st.sidebar.success("Inactive")
        if st.sidebar.button("Activate Kill Switch", type="primary"):
            state.activate_kill_switch()
            st.rerun()
    
    st.sidebar.divider()
    
    # Scheduler status
    scheduler = st.session_state.get("scheduler")
    if scheduler and scheduler.is_running():
        st.sidebar.success("🟢 Trading Loop Running")
        if st.sidebar.button("Stop Loop"):
            scheduler.stop()
            st.session_state.scheduler = None
            st.rerun()
    else:
        st.sidebar.info("⚪ Trading Loop Stopped")
        if st.sidebar.button("Start Loop"):
            scheduler = TradingScheduler(main_trading_loop)
            scheduler.start()
            st.session_state.scheduler = scheduler
            st.rerun()
    
    st.sidebar.divider()
    
    # Selected symbols
    st.sidebar.subheader("📊 Symbols")
    symbols = config.trading.default_symbols
    for symbol in symbols:
        st.sidebar.text(symbol)


def main():
    """Main Streamlit app"""
    sidebar()
    
    # Page selection
    page = st.selectbox(
        "Navigation",
        ["Dashboard", "Configuration", "Strategy", "Risk Management", "News", "Logs/Audit"],
        key="page_select"
    )
    
    st.title(f"📈 {page}")
    
    # Render selected page
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
