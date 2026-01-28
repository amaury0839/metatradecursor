"""Simple Streamlit UI - connects to local API without async issues"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json
import os

import requests
import streamlit as st

# Configure page
st.set_page_config(
    page_title="AI Forex Trading Bot",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Basic styling (kept lightweight for Streamlit)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    .stApp { font-family: 'IBM Plex Sans', sans-serif; }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.2px; }
    .metric-label { font-size: 0.9rem; opacity: 0.8; }
    .status-pill { padding: 4px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .pill-ok { background: #0f766e20; color: #0f766e; border: 1px solid #0f766e60; }
    .pill-warn { background: #b4530920; color: #b45309; border: 1px solid #b4530960; }
    .pill-bad { background: #b91c1c20; color: #b91c1c; border: 1px solid #b91c1c60; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Get API URL
API_URL = os.getenv("TRADING_BOT_API_URL", "http://localhost:8000")


@st.cache_resource
def get_api_url() -> str:
    """Get API URL"""
    return API_URL


api_url = get_api_url()


def api_get(path: str, timeout: int = 2) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """GET helper for API"""
    try:
        response = requests.get(f"{api_url}{path}", timeout=timeout)
        if response.status_code == 200:
            return response.json(), None
        return None, f"HTTP {response.status_code}"
    except Exception as exc:
        return None, str(exc)


def api_post(path: str, timeout: int = 4) -> Tuple[bool, str]:
    """POST helper for API"""
    try:
        response = requests.post(f"{api_url}{path}", timeout=timeout)
        if response.status_code == 200:
            return True, "OK"
        return False, f"HTTP {response.status_code}"
    except Exception as exc:
        return False, str(exc)


def load_local_services() -> Dict[str, Any]:
    """Try to load local services (optional)."""
    try:
        from app.core.config import get_config, reload_config
        from app.trading.strategy import get_strategy
        from app.trading.data import get_data_provider
        from app.trading.risk import get_risk_manager
        from app.trading.mt5_client import get_mt5_client
        from app.trading.portfolio import get_portfolio_manager
        from app.core.state import get_state_manager

        return {
            "ok": True,
            "get_config": get_config,
            "reload_config": reload_config,
            "get_strategy": get_strategy,
            "get_data_provider": get_data_provider,
            "get_risk_manager": get_risk_manager,
            "get_mt5_client": get_mt5_client,
            "get_portfolio_manager": get_portfolio_manager,
            "get_state_manager": get_state_manager,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_ai_client() -> Tuple[Optional[Any], Optional[str]]:
    """Try to create the Gemini client."""
    try:
        from app.ai.gemini_client import get_gemini_client

        return get_gemini_client(), None
    except Exception as exc:
        return None, str(exc)


def status_pill(label: str, status: str) -> None:
    """Render a small status pill."""
    class_name = "pill-ok" if status == "ok" else "pill-warn" if status == "warn" else "pill-bad"
    st.markdown(
        f"<span class='status-pill {class_name}'>{label}</span>",
        unsafe_allow_html=True,
    )


# Header
st.title("AI Forex Trading Bot")
st.caption(f"API: {api_url}")

# Connection check
api_root, api_error = api_get("/")
if api_root and api_root.get("status") == "ok":
    status_pill("API connected", "ok")
else:
    status_pill("API offline", "bad")
    if api_error:
        st.error(f"API error: {api_error}")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        [
            "Dashboard",
            "Configuration",
            "Strategy",
            "Risk Management",
            "AI Assistant",
            "News",
            "Logs",
        ],
        index=0,
    )

    st.divider()
    st.subheader("Quick actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connect MT5", width="stretch"):
            ok, msg = api_post("/connection/connect")
            st.success("Connected") if ok else st.error(f"Connect failed: {msg}")
    with col2:
        if st.button("Disconnect", width="stretch"):
            ok, msg = api_post("/connection/disconnect")
            st.success("Disconnected") if ok else st.error(f"Disconnect failed: {msg}")

    col3, col4 = st.columns(2)
    with col3:
        if st.button("Start scheduler", width="stretch"):
            ok, msg = api_post("/control/scheduler/start")
            st.success("Scheduler started") if ok else st.error(f"Start failed: {msg}")
    with col4:
        if st.button("Stop scheduler", width="stretch"):
            ok, msg = api_post("/control/scheduler/stop")
            st.success("Scheduler stopped") if ok else st.error(f"Stop failed: {msg}")

    col5, col6 = st.columns(2)
    with col5:
        if st.button("Kill switch on", width="stretch"):
            ok, msg = api_post("/control/kill-switch/activate")
            st.success("Kill switch active") if ok else st.error(f"Failed: {msg}")
    with col6:
        if st.button("Kill switch off", width="stretch"):
            ok, msg = api_post("/control/kill-switch/deactivate")
            st.success("Kill switch disabled") if ok else st.error(f"Failed: {msg}")

    st.divider()
    if st.button("Refresh", width="stretch"):
        st.rerun()


# Helpers for data tables

def normalize_decisions(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for dec in decisions:
        rows.append(
            {
                "timestamp": dec.get("timestamp"),
                "symbol": dec.get("symbol"),
                "timeframe": dec.get("timeframe"),
                "signal": dec.get("signal"),
                "action": dec.get("action"),
                "confidence": dec.get("confidence"),
                "risk_ok": dec.get("risk_ok"),
                "execution_ok": dec.get("execution_success"),
                "reason": ", ".join(dec.get("reason", []) or []),
            }
        )
    return rows


def normalize_trades(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for trade in trades:
        rows.append(
            {
                "timestamp": trade.get("timestamp"),
                "symbol": trade.get("symbol"),
                "type": trade.get("order_type"),
                "volume": trade.get("volume"),
                "price": trade.get("price"),
                "profit": trade.get("profit"),
                "comment": trade.get("comment"),
            }
        )
    return rows


# Page: Dashboard
if page == "Dashboard":
    st.header("Dashboard")

    connection_data, conn_error = api_get("/status/connection")
    trading_data, trade_error = api_get("/status/trading")

    if connection_data and trading_data:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            balance = trading_data.get("balance") or 0
            st.metric("Account balance", f"${balance:.2f}")
        with col2:
            equity = trading_data.get("equity") or 0
            st.metric("Equity", f"${equity:.2f}")
        with col3:
            open_pos = trading_data.get("open_positions") or 0
            st.metric("Open positions", open_pos)
        with col4:
            is_connected = connection_data.get("connected", False)
            st.metric("MT5 status", "Online" if is_connected else "Offline")

        st.divider()
        is_trading_active = not trading_data.get("kill_switch_active", True)
        if is_connected and is_trading_active:
            st.success("Trading is ACTIVE - Bot is monitoring markets")
        elif is_connected and not is_trading_active:
            st.warning("Trading is PAUSED - Kill switch is active")
        else:
            st.error("MT5 DISCONNECTED - Cannot trade")

        if connection_data.get("account_info"):
            st.divider()
            account = connection_data["account_info"]
            st.subheader("Account details")
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.write(f"Login: {account.get('login', 'N/A')}")
                st.write(f"Mode: {account.get('trade_mode', 'N/A')}")
            with col_info2:
                st.write(f"Leverage: {account.get('leverage', 'N/A')}:1")
                st.write(f"Margin mode: {account.get('margin_so_mode', 'N/A')}")
            with col_info3:
                st.write(f"Currency: {account.get('currency', 'N/A')}")
                st.write(f"Server: {connection_data.get('mode', 'N/A')}")
    else:
        st.error(f"Could not load dashboard. {conn_error or trade_error}")

    st.divider()
    st.subheader("Open positions")
    positions_data, pos_error = api_get("/positions")
    if positions_data and positions_data.get("positions"):
        st.dataframe(positions_data["positions"], width="stretch")
    else:
        st.info("No open positions") if not pos_error else st.warning(f"Positions error: {pos_error}")

    st.divider()
    st.subheader("Recent decisions")
    decisions_data, dec_error = api_get("/decisions")
    if decisions_data and decisions_data.get("decisions"):
        st.dataframe(normalize_decisions(decisions_data["decisions"])[-10:], width="stretch")
    else:
        st.info("No decisions yet") if not dec_error else st.warning(f"Decisions error: {dec_error}")

    st.divider()
    st.subheader("Recent trades")
    trades_data, trade_list_error = api_get("/trades")
    if trades_data and trades_data.get("trades"):
        st.dataframe(normalize_trades(trades_data["trades"])[-10:], width="stretch")
    else:
        st.info("No trades yet") if not trade_list_error else st.warning(f"Trades error: {trade_list_error}")


# Page: Configuration
elif page == "Configuration":
    st.header("Configuration")
    local = load_local_services()

    if local.get("ok"):
        get_config = local["get_config"]
        reload_config = local["reload_config"]
        config = get_config()

        st.subheader("MT5")
        with st.expander("Connection", expanded=True):
            st.info("Edit .env for credentials. Values are hidden here for security.")
            st.text_input("Login", value=str(config.mt5.login), disabled=True)
            st.text_input("Server", value=config.mt5.server, disabled=True)
            st.text_input("Password", value="***", type="password", disabled=True)
            st.text_input("Path", value=config.mt5.path or "Not set", disabled=True)

        st.subheader("Trading")
        with st.expander("Mode and defaults", expanded=True):
            st.write(f"Mode: {config.trading.mode}")
            st.write(f"Timezone: {config.trading.timezone}")
            st.write(f"Polling interval: {config.trading.polling_interval_seconds} sec")
            st.write(f"Default symbols: {', '.join(config.trading.default_symbols)}")
            st.write(f"Default timeframe: {config.trading.default_timeframe}")

        st.subheader("Tickers")
        with st.expander("Symbols configuration", expanded=True):
            st.caption("Edit .env to persist. Here you can draft a custom list.")
            current_symbols = ", ".join(config.trading.default_symbols)
            draft_symbols = st.text_area(
                "Symbols (comma-separated)",
                value=current_symbols,
                placeholder="EURUSD, GBPUSD, USDJPY",
                height=80,
            )
            if st.button("Preview symbols"):
                parsed = [s.strip().upper() for s in draft_symbols.split(",") if s.strip()]
                st.write(f"{len(parsed)} symbols: {', '.join(parsed) if parsed else 'None'}")
                st.info("To persist, update DEFAULT_SYMBOLS in .env and restart.")

        st.subheader("AI")
        with st.expander("Gemini", expanded=True):
            st.text_input("Gemini API key", value="***", type="password", disabled=True)
            st.slider(
                "Min confidence threshold",
                min_value=0.0,
                max_value=1.0,
                value=float(config.ai.min_confidence_threshold),
                step=0.01,
                disabled=True,
            )
            st.caption("Edit .env and restart to change AI settings.")

        st.subheader("News")
        with st.expander("Provider", expanded=False):
            st.write(f"Provider: {config.news.provider}")
            st.write(f"Cache minutes: {config.news.cache_minutes}")

        st.subheader("System")
        with st.expander("Logging", expanded=False):
            st.write(f"Log level: {config.logging.log_level}")
            st.write(f"Log file: {config.logging.log_file}")

        if st.button("Reload configuration"):
            reload_config()
            st.success("Config reloaded")
            st.rerun()
    else:
        st.info("Local configuration not available. Connect to the bot host to view settings.")


# Page: Strategy
elif page == "Strategy":
    st.header("Strategy")
    local = load_local_services()

    if local.get("ok"):
        config = local["get_config"]()
        strategy = local["get_strategy"]()
        data = local["get_data_provider"]()

        st.subheader("Symbols")
        available_symbols = (
            data.mt5.get_symbols()[:20]
            if data.mt5.is_connected()
            else config.trading.default_symbols
        )
        selected_symbols = st.multiselect(
            "Symbols to monitor",
            options=available_symbols,
            default=config.trading.default_symbols,
        )
        st.caption("Symbol updates require restart to persist.")

        st.divider()
        st.subheader("Timeframe")
        timeframe = st.selectbox(
            "Timeframe",
            options=["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
            index=2 if config.trading.default_timeframe == "M15" else 0,
        )

        st.divider()
        st.subheader("Indicators")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("EMA fast", min_value=5, max_value=100, value=strategy.ema_fast_period)
            st.number_input("RSI period", min_value=5, max_value=50, value=strategy.rsi_period)
        with col2:
            st.number_input("EMA slow", min_value=10, max_value=200, value=strategy.ema_slow_period)
            st.number_input("ATR period", min_value=5, max_value=50, value=strategy.atr_period)

        st.divider()
        st.subheader("Signal test")
        test_symbol = st.selectbox("Test symbol", options=selected_symbols or ["EURUSD"])
        if st.button("Get signal"):
            with st.spinner("Calculating signal..."):
                signal, indicators, error = strategy.get_signal(test_symbol, timeframe)
            if error:
                st.error(f"Signal error: {error}")
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric("Signal", signal)
                col2.metric("RSI", f"{indicators.get('rsi', 0):.2f}")
                col3.metric("ATR", f"{indicators.get('atr', 0):.5f}")
                st.json(
                    {
                        "ema_fast": indicators.get("ema_fast", 0),
                        "ema_slow": indicators.get("ema_slow", 0),
                        "trend": "bullish" if indicators.get("trend_bullish") else "bearish",
                        "rsi": indicators.get("rsi", 0),
                        "atr": indicators.get("atr", 0),
                        "reasons": indicators.get("signal_reasons", []),
                    }
                )
    else:
        symbols_data, sym_error = api_get("/symbols")
        st.info("Strategy config is managed on the bot host. Showing remote symbols if available.")
        if symbols_data and symbols_data.get("symbols"):
            st.write(", ".join(symbols_data["symbols"][:20]))
        else:
            st.warning(f"Symbols unavailable: {sym_error or 'No data'}")


# Page: Risk Management
elif page == "Risk Management":
    st.header("Risk Management")
    local = load_local_services()

    if local.get("ok"):
        risk = local["get_risk_manager"]()
        st.subheader("Risk parameters")

        col1, col2 = st.columns(2)
        with col1:
            risk_per_trade = st.number_input("Risk per trade (%)", min_value=0.1, max_value=5.0, value=risk.risk_per_trade_pct, step=0.1)
            max_daily_loss = st.number_input("Max daily loss (%)", min_value=0.5, max_value=10.0, value=risk.max_daily_loss_pct, step=0.1)
        with col2:
            max_drawdown = st.number_input("Max drawdown (%)", min_value=1.0, max_value=20.0, value=risk.max_drawdown_pct, step=0.5)
            max_positions = st.number_input("Max positions", min_value=1, max_value=10, value=risk.max_positions, step=1)

        if st.button("Update risk parameters"):
            risk.risk_per_trade_pct = risk_per_trade
            risk.max_daily_loss_pct = max_daily_loss
            risk.max_drawdown_pct = max_drawdown
            risk.max_positions = max_positions
            st.success("Risk updated")

        st.divider()
        st.subheader("Current risk status")
        mt5 = local["get_mt5_client"]()
        portfolio = local["get_portfolio_manager"]()
        state = local["get_state_manager"]()

        account_info = mt5.get_account_info()
        if account_info:
            equity = account_info.get("equity", 0)
            balance = account_info.get("balance", 0)
            drawdown_pct = ((state.max_equity - equity) / state.max_equity) * 100 if state.max_equity > 0 else 0.0
            daily_loss_pct = (state.daily_pnl / balance * 100) if balance > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Drawdown", f"{drawdown_pct:.2f}%")
            col2.metric("Daily PnL", f"${state.daily_pnl:.2f}")
            col3.metric("Open positions", portfolio.get_open_positions_count())
            risk_status = "OK"
            if drawdown_pct > risk.max_drawdown_pct:
                risk_status = "Drawdown exceeded"
            elif daily_loss_pct < -risk.max_daily_loss_pct:
                risk_status = "Daily loss exceeded"
            elif portfolio.get_open_positions_count() >= risk.max_positions:
                risk_status = "Max positions"
            col4.metric("Risk status", risk_status)
        else:
            st.warning("Account info not available")
    else:
        st.info("Risk configuration is managed on the bot host.")


# Page: AI Assistant
elif page == "AI Assistant":
    st.header("AI Assistant")

    local = load_local_services()
    if local.get("ok"):
        config = local["get_config"]()
        st.subheader("AI status")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Model: {config.ai.gemini_model or 'Not set'}")
        with col2:
            st.write("API key configured: " + ("Yes" if config.ai.gemini_api_key else "No"))
        st.divider()

    decisions_data, dec_error = api_get("/decisions")
    recent_decisions = decisions_data.get("decisions", []) if decisions_data else []

    st.subheader("Decision explorer")
    if recent_decisions:
        st.dataframe(normalize_decisions(recent_decisions)[-10:], width="stretch")
    else:
        st.info("No decisions yet" if not dec_error else f"Decisions error: {dec_error}")

    st.divider()
    st.subheader("Ask the AI")
    question = st.text_area("Question", placeholder="Ask about strategy, risk, or last decision...")
    include_last = st.checkbox("Include last decision context", value=True)

    ai_client, ai_error = get_ai_client()
    if ai_error:
        st.warning(f"AI not available: {ai_error}")

    if st.button("Ask AI", disabled=not question.strip()):
        if not ai_client:
            st.error("AI client not available. Check Gemini API key in .env.")
        else:
            context = {}
            if include_last and recent_decisions:
                context["last_decision"] = recent_decisions[-1]
            context["api_url"] = api_url

            system_prompt = (
                "You are an AI trading assistant. "
                "Return strict JSON only. "
                "Schema: {answer: string, risks: [string], next_steps: [string], confidence: number}"
            )
            user_prompt = f"Question: {question}\nContext: {json.dumps(context)}"

            with st.spinner("Thinking..."):
                result = ai_client.generate_content(system_prompt, user_prompt, use_cache=False)

            if not result:
                st.error("AI response was not valid JSON. Try again or simplify the question.")
            else:
                st.markdown("### Answer")
                st.write(result.get("answer", "No answer"))
                st.markdown("### Risks")
                st.write(result.get("risks", []))
                st.markdown("### Next steps")
                st.write(result.get("next_steps", []))
                st.markdown("### Confidence")
                st.write(result.get("confidence", 0))


# Page: News
elif page == "News":
    st.header("News")
    try:
        from app.news.sentiment import NewsSentimentAnalyzer
        from app.core.config import get_config

        config = get_config()
        analyzer = NewsSentimentAnalyzer()
        symbols = config.trading.default_symbols
        symbol = st.selectbox("Symbol", options=symbols)
        if st.button("Analyze sentiment"):
            with st.spinner("Analyzing..."):
                result = analyzer.analyze_symbol(symbol)
            st.write(result.get("summary", "No summary"))
            st.write(result.get("sentiment", "neutral"))
            st.write(result.get("score", 0))
            if result.get("headlines"):
                st.json(result.get("headlines"))
    except Exception as exc:
        st.info(f"News module not available: {exc}")


# Page: Logs
elif page == "Logs":
    st.header("Logs")
    tab_orders, tab_reviews = st.tabs(["Order executions", "Execution reviews"])

    with tab_orders:
        st.subheader("Order log")
        trades_data, trade_list_error = api_get("/trades")
        if trades_data and trades_data.get("trades"):
            st.dataframe(normalize_trades(trades_data["trades"])[-100:], width="stretch")
        else:
            st.info("No trades yet" if not trade_list_error else f"Trades error: {trade_list_error}")

    with tab_reviews:
        st.subheader("Review log")
        decisions_data, dec_error = api_get("/decisions")
        if decisions_data and decisions_data.get("decisions"):
            decisions = normalize_decisions(decisions_data["decisions"])
            only_actionable = st.checkbox("Only BUY/SELL reviews", value=False)
            if only_actionable:
                decisions = [d for d in decisions if d.get("action") in {"BUY", "SELL"}]
            st.dataframe(decisions[-100:], width="stretch")
        else:
            st.info("No reviews yet" if not dec_error else f"Decisions error: {dec_error}")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
