"""Strategy configuration page - Works for both local and remote modes"""

import streamlit as st

# Try to import local modules
try:
    from app.core.config import get_config
    from app.trading.strategy import get_strategy
    from app.trading.data import get_data_provider
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def render_strategy():
    """Render strategy configuration page - auto-detects local or remote mode"""
    if LOCAL_MODE:
        render_strategy_local()
    else:
        st.info("Strategy configuration is managed on the local trading bot server.")
        st.info("Use the local UI or API to configure strategy parameters.")


def render_strategy_local():
    """Render strategy configuration page - Local mode"""
    config = get_config()
    strategy = get_strategy()
    data = get_data_provider()
    
    st.subheader("📈 Trading Strategy")
    
    # Symbol selection
    st.markdown("### Symbols")
    available_symbols = data.mt5.get_symbols()[:20] if data.mt5.is_connected() else config.trading.default_symbols
    
    # Ensure default symbols are in available symbols
    default_symbols = [s for s in config.trading.default_symbols if s in available_symbols]
    if not default_symbols:
        default_symbols = available_symbols[:1] if available_symbols else []
    
    selected_symbols = st.multiselect(
        "Select symbols to trade",
        options=available_symbols,
        default=default_symbols
    )
    
    if st.button("Update Symbols"):
        st.info("Symbol selection updated (requires restart to persist)")
    
    st.divider()
    
    # Timeframe
    st.markdown("### Timeframe")
    timeframe = st.selectbox(
        "Trading timeframe",
        options=["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
        index=2 if config.trading.default_timeframe == "M15" else 0
    )
    
    st.divider()
    
    # Technical indicators
    st.markdown("### Technical Indicators")
    
    col1, col2 = st.columns(2)
    with col1:
        ema_fast = st.number_input("EMA Fast Period", min_value=5, max_value=100, 
                                   value=strategy.ema_fast_period, step=1)
        rsi_period = st.number_input("RSI Period", min_value=5, max_value=50, 
                                     value=strategy.rsi_period, step=1)
    with col2:
        ema_slow = st.number_input("EMA Slow Period", min_value=10, max_value=200, 
                                   value=strategy.ema_slow_period, step=1)
        atr_period = st.number_input("ATR Period", min_value=5, max_value=50, 
                                     value=strategy.atr_period, step=1)
    
    st.divider()
    
    # Signal parameters
    st.markdown("### Signal Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        rsi_oversold = st.number_input("RSI Oversold", min_value=0, max_value=50, 
                                       value=strategy.rsi_oversold, step=1)
        rsi_neutral_low = st.number_input("RSI Neutral Low", min_value=0, max_value=50, 
                                          value=strategy.rsi_neutral_low, step=1)
    with col2:
        rsi_overbought = st.number_input("RSI Overbought", min_value=50, max_value=100, 
                                        value=strategy.rsi_overbought, step=1)
        rsi_neutral_high = st.number_input("RSI Neutral High", min_value=50, max_value=100, 
                                          value=strategy.rsi_neutral_high, step=1)
    
    st.divider()
    
    # AI Decision
    st.markdown("### AI Decision Engine")
    use_ai = st.checkbox("Enable AI Decision Engine (Gemini)", value=True)
    
    if use_ai:
        st.info("✅ AI decisions will override technical signals when enabled")
    else:
        st.warning("⚠️ Only technical signals will be used")
    
    st.divider()
    
    # Test signal
    st.markdown("### Test Signal")
    test_symbol = st.selectbox("Test symbol", options=selected_symbols or ["EURUSD"])
    
    if st.button("Get Signal"):
        with st.spinner("Calculating signal..."):
            signal, indicators, error = strategy.get_signal(test_symbol, timeframe)
            
            if error:
                st.error(f"Error: {error}")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Signal", signal)
                with col2:
                    st.metric("RSI", f"{indicators.get('rsi', 0):.2f}")
                with col3:
                    st.metric("ATR", f"{indicators.get('atr', 0):.5f}")
                
                st.json({
                    "EMA Fast": indicators.get('ema_fast', 0),
                    "EMA Slow": indicators.get('ema_slow', 0),
                    "Trend": "Bullish" if indicators.get('trend_bullish') else "Bearish",
                    "RSI": indicators.get('rsi', 0),
                    "ATR": indicators.get('atr', 0),
                    "Reasons": indicators.get('signal_reasons', []),
                })

