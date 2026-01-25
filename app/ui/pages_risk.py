"""Risk management page - Works for both local and remote modes"""

import streamlit as st

# Try to import local modules
try:
    from app.trading.risk import get_risk_manager
    from app.core.config import get_config
    from app.trading.mt5_client import get_mt5_client
    from app.trading.portfolio import get_portfolio_manager
    from app.core.state import get_state_manager
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def render_risk():
    """Render risk management page - auto-detects local or remote mode"""
    if LOCAL_MODE:
        render_risk_local()
    else:
        st.info("Risk management is configured on the local trading bot server.")
        st.info("Use the local UI or API to configure risk parameters.")


def render_risk_local():
    """Render risk management page - Local mode"""
    risk = get_risk_manager()
    config = get_config()
    
    st.subheader("🛡️ Risk Management")
    
    # Risk parameters
    st.markdown("### Risk Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        risk_per_trade = st.number_input(
            "Risk per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=risk.risk_per_trade_pct,
            step=0.1,
            help="Percentage of equity to risk per trade"
        )
        
        max_daily_loss = st.number_input(
            "Max Daily Loss (%)",
            min_value=0.5,
            max_value=10.0,
            value=risk.max_daily_loss_pct,
            step=0.1,
            help="Maximum daily loss percentage before stopping"
        )
    
    with col2:
        max_drawdown = st.number_input(
            "Max Drawdown (%)",
            min_value=1.0,
            max_value=20.0,
            value=risk.max_drawdown_pct,
            step=0.5,
            help="Maximum drawdown percentage"
        )
        
        max_positions = st.number_input(
            "Max Positions",
            min_value=1,
            max_value=10,
            value=risk.max_positions,
            step=1,
            help="Maximum number of simultaneous positions"
        )
    
    if st.button("Update Risk Parameters"):
        risk.risk_per_trade_pct = risk_per_trade
        risk.max_daily_loss_pct = max_daily_loss
        risk.max_drawdown_pct = max_drawdown
        risk.max_positions = max_positions
        st.success("Risk parameters updated!")
    
    st.divider()
    
    # Spread and slippage
    st.markdown("### Spread & Slippage Limits")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        max_spread_forex = st.number_input(
            "Max Spread Forex (pips)",
            min_value=1.0,
            max_value=50.0,
            value=risk.FOREX_MAX_SPREAD_PIPS,
            step=0.5
        )
    with col2:
        max_spread_crypto = st.number_input(
            "Max Spread Crypto (pips)",
            min_value=10.0,
            max_value=500.0,
            value=risk.CRYPTO_MAX_SPREAD_PIPS,
            step=10.0
        )
    with col3:
        max_slippage = st.number_input(
            "Max Slippage (pips)",
            min_value=0.1,
            max_value=5.0,
            value=risk.max_slippage_pips,
            step=0.1
        )
    
    if st.button("Update Spread/Slippage"):
        risk.FOREX_MAX_SPREAD_PIPS = max_spread_forex
        risk.CRYPTO_MAX_SPREAD_PIPS = max_spread_crypto
        risk.max_slippage_pips = max_slippage
        st.success("Spread/slippage limits updated!")
    
    st.divider()
    
    # Trading hours
    st.markdown("### Trading Hours")
    
    col1, col2 = st.columns(2)
    with col1:
        start_hour = st.number_input("Start Hour", min_value=0, max_value=23, 
                                     value=risk.trading_hours_start.hour, step=1)
        start_minute = st.number_input("Start Minute", min_value=0, max_value=59, 
                                      value=risk.trading_hours_start.minute, step=1)
    with col2:
        end_hour = st.number_input("End Hour", min_value=0, max_value=23, 
                                   value=risk.trading_hours_end.hour, step=1)
        end_minute = st.number_input("End Minute", min_value=0, max_value=59, 
                                     value=risk.trading_hours_end.minute, step=1)
    
    from datetime import time
    if st.button("Update Trading Hours"):
        risk.trading_hours_start = time(start_hour, start_minute)
        risk.trading_hours_end = time(end_hour, end_minute)
        st.success("Trading hours updated!")
    
    st.divider()
    
    # Stop Loss / Take Profit
    st.markdown("### Stop Loss & Take Profit")
    
    col1, col2 = st.columns(2)
    with col1:
        sl_atr_mult = st.number_input(
            "Stop Loss (ATR multiplier)",
            min_value=0.5,
            max_value=5.0,
            value=1.5,
            step=0.1
        )
    with col2:
        tp_atr_mult = st.number_input(
            "Take Profit (ATR multiplier)",
            min_value=1.0,
            max_value=10.0,
            value=2.5,
            step=0.1
        )
    
    st.info("SL/TP multipliers are applied to ATR for dynamic stop levels")
    
    st.divider()
    
    # Current risk status
    st.markdown("### Current Risk Status")
    
    mt5 = get_mt5_client()
    portfolio = get_portfolio_manager()
    state = get_state_manager()
    
    account_info = mt5.get_account_info()
    if account_info:
        equity = account_info.get('equity', 0)
        balance = account_info.get('balance', 0)
        
        # Calculate current drawdown
        if state.max_equity > 0:
            drawdown_pct = ((state.max_equity - equity) / state.max_equity) * 100
        else:
            drawdown_pct = 0.0
        
        # Daily loss
        daily_loss_pct = (state.daily_pnl / balance * 100) if balance > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Drawdown", f"{drawdown_pct:.2f}%", 
                     delta=f"Max: {risk.max_drawdown_pct}%")
        with col2:
            st.metric("Daily PnL", f"${state.daily_pnl:.2f}", 
                     delta=f"{daily_loss_pct:.2f}%")
        with col3:
            st.metric("Open Positions", portfolio.get_open_positions_count(), 
                     delta=f"Max: {risk.max_positions}")
        with col4:
            risk_status = "✅ OK"
            if drawdown_pct > risk.max_drawdown_pct:
                risk_status = "❌ Drawdown exceeded"
            elif daily_loss_pct < -risk.max_daily_loss_pct:
                risk_status = "❌ Daily loss exceeded"
            elif portfolio.get_open_positions_count() >= risk.max_positions:
                risk_status = "⚠️ Max positions"
            st.metric("Risk Status", risk_status)
