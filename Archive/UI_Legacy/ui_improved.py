"""Professional Streamlit Dashboard for AI Trading Bot"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import time
import plotly.express as px
import plotly.graph_objects as go

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("streamlit_dashboard")

# API Configuration
API_BASE_URL = "http://localhost:8000"
CACHE_TTL = 10  # Increased from 2s to 10s for better performance (less constant refreshes)
API_TIMEOUT = 8  # Increased timeout for slow connections
API_RETRIES = 1  # Reduced from 2 to 1 (fail faster, less waiting)

def safe_timestamp(ts):
    """Convert timestamp safely, handling str/int/None"""
    if not ts:
        return "N/A"
    try:
        ts_int = int(ts) if isinstance(ts, str) else ts
        if ts_int > 0:
            return datetime.fromtimestamp(ts_int).strftime("%m-%d %H:%M")
    except Exception:
        pass
    return "N/A"

# Cache data functions
@st.cache_data(ttl=CACHE_TTL)
def api_call(endpoint: str, retries: int = API_RETRIES):
    """Make API call with caching and retry logic"""
    for attempt in range(retries + 1):
        try:
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                timeout=API_TIMEOUT,
                verify=False  # Skip SSL verification for localhost
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 502:
                # Bad gateway - server restarting
                if attempt < retries:
                    time.sleep(0.5)
                    continue
        except requests.exceptions.Timeout:
            logger.debug(f"API timeout on {endpoint}")
            if attempt < retries:
                time.sleep(0.3)
                continue
        except requests.exceptions.ConnectionError:
            logger.debug(f"API connection error on {endpoint}")
            if attempt < retries:
                time.sleep(0.3)
                continue
        except Exception as e:
            logger.warning(f"API error on {endpoint}: {e}")
    return None

def fetch_positions():
    data = api_call("/positions")
    return data.get("positions", []) if data else []

def fetch_connection_status():
    data = api_call("/status/connection")
    return data if data else {}

def fetch_trading_status():
    data = api_call("/status/trading")
    return data if data else {}

def fetch_trades():
    data = api_call("/trades?limit=100")
    return data.get("trades", []) if data else []

def fetch_decisions():
    data = api_call("/decisions?limit=100")
    return data.get("decisions", []) if data else []

def fetch_analysis_logs(symbol: str = None, analysis_type: str = None, status: str = None, limit: int = 100):
    """Fetch analysis logs with optional filters"""
    endpoint = "/logs/analysis?limit=" + str(limit)
    if symbol:
        endpoint += f"&symbol={symbol}"
    if analysis_type:
        endpoint += f"&analysis_type={analysis_type}"
    if status:
        endpoint += f"&status={status}"
    
    data = api_call(endpoint)
    return data.get("logs", []) if data else []


def fetch_symbols_info():
    """Fetch broker symbol details (volume min/max/step)"""
    data = api_call("/symbols/info")
    return data.get("symbols", []) if data else []


def fetch_ai_tuning():
    """Fetch AI tuning parameters"""
    data = api_call("/ai/tuning")
    return data if data else {}


def fetch_mini_backtest(symbol: str = "EURUSD", candles: int = 50):
    """Fetch quick backtest results"""
    data = api_call(f"/ai/backtest/mini?symbol={symbol}&candles={candles}")
    return data if data else {}

# Page Config
st.set_page_config(
    page_title="AI Trading Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (bold, intentional UI)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@400;500;600&display=swap');

    :root {
        --bg: #050915;
        --panel: #0c1222;
        --card: #0f172a;
        --card-strong: #131c31;
        --border: rgba(255, 255, 255, 0.14);
        --accent: #2ee6a0;
        --accent-2: #6c8bff;
        --muted: #cbd5e1;
        --text: #f8fafc;
    }

    html, body, [class*="block-container"] {
        background: radial-gradient(130% 130% at 20% 10%, rgba(46, 230, 160, 0.08), transparent),
                    radial-gradient(120% 120% at 80% 0%, rgba(108, 139, 255, 0.14), transparent),
                    linear-gradient(180deg, #050915 0%, #0b1429 100%) !important;
        color: var(--text);
        font-family: 'Space Grotesk', 'Manrope', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', 'Manrope', sans-serif;
        letter-spacing: -0.02em;
    }

    .header-container {
        background: linear-gradient(120deg, rgba(46, 230, 160, 0.18) 0%, rgba(108, 139, 255, 0.22) 100%);
        border: 1px solid rgba(255,255,255,0.18);
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    }

    .header-container:after {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 20% 20%, rgba(46, 230, 160, 0.18), transparent 45%),
                    radial-gradient(circle at 80% 0%, rgba(108, 139, 255, 0.18), transparent 40%);
        pointer-events: none;
    }

    .metric-card {
        background: var(--card-strong);
        border: 1px solid rgba(255,255,255,0.16);
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }
    .metric-card h4 {
        margin: 0 0 6px 0;
        color: var(--muted);
        font-size: 0.9rem;
    }
    .metric-card .value {
        font-size: 1.5rem;
        font-weight: 700;
    }
    .metric-card .delta {
        font-size: 0.9rem;
        color: var(--muted);
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.18);
        background: rgba(255,255,255,0.06);
        color: var(--text);
        font-weight: 600;
    }
    .chip.good { color: #34d399; border-color: rgba(52,211,153,0.35); background: rgba(52,211,153,0.08); }
    .chip.warn { color: #f59e0b; border-color: rgba(245,158,11,0.35); background: rgba(245,158,11,0.08); }
    .chip.bad  { color: #f87171; border-color: rgba(248,113,113,0.35); background: rgba(248,113,113,0.08); }

    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        padding: 0 4px 6px 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: var(--card-strong);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 12px;
        color: var(--muted);
        padding: 10px 14px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(120deg, rgba(46,230,160,0.28), rgba(108,139,255,0.28));
        color: #0b1224 !important;
        border-color: transparent;
    }

    .stDataFrame { border-radius: 12px; overflow: hidden; }

    .stMetric { background: var(--card-strong); border: 1px solid rgba(255,255,255,0.16); padding: 12px; border-radius: 12px; }

    .stButton>button {
        background: linear-gradient(120deg, #2ee6a0, #6c8bff);
        color: #071018;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: 0 8px 24px rgba(108,139,255,0.28);
    }
    .stButton>button:hover { filter: brightness(1.08); }
</style>
""", unsafe_allow_html=True)

# Initialize session
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Performance optimization: Local session cache for frequent data
if "cached_data" not in st.session_state:
    st.session_state.cached_data = {
        "connection": None,
        "trading": None,
        "positions": None,
        "trades": None,
        "decisions": None,
        "updated_at": 0
    }

def should_refresh_cache():
    """Check if cache is stale (every 10s)"""
    return time.time() - st.session_state.cached_data["updated_at"] > CACHE_TTL

def get_cached_data(key: str, fetch_func, *args):
    """Get data from local session cache or fetch from API"""
    # Return cached if still fresh
    if not should_refresh_cache() and st.session_state.cached_data[key] is not None:
        return st.session_state.cached_data[key]
    
    # Fetch fresh data
    data = fetch_func(*args)
    
    # Update cache if this is the first key being fetched in this cycle
    if st.session_state.cached_data[key] is None:
        st.session_state.cached_data["updated_at"] = time.time()
    
    st.session_state.cached_data[key] = data
    return data

# ========== HEADER ==========
def render_header():
    """Professional header with account info"""
    config = get_config()
    conn = get_cached_data("connection", fetch_connection_status)
    status = get_cached_data("trading", fetch_trading_status)
    
    balance = status.get('balance', 0) or 0
    equity = status.get('equity', 0) or 0
    is_connected = conn.get('connected', False)
    is_running = status.get('scheduler_running', False)
    mode = "LIVE" if not config.is_paper_mode() else "PAPER"
    latency_ms = conn.get('latency_ms')
    last_sync = conn.get('last_sync') or status.get('last_heartbeat')
    
    st.markdown("<div class='header-container'>", unsafe_allow_html=True)
    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown("<h2 style='margin:0;'>🤖 AI Trading Command Center</h2>", unsafe_allow_html=True)
        st.markdown("<p style='margin:4px 0 10px 0; color: var(--muted);'>Gemini-assisted execution · Forex + Crypto · Risk-aware sizing</p>", unsafe_allow_html=True)
        chips = []
        chips.append(f"<span class='chip {'good' if is_connected else 'bad'}'>MT5 {'Connected' if is_connected else 'Offline'}</span>")
        chips.append(f"<span class='chip {'good' if is_running else 'warn'}'>Loop {'Running' if is_running else 'Stopped'}</span>")
        chips.append(f"<span class='chip'>Mode {mode}</span>")
        if latency_ms is not None:
            chips.append(f"<span class='chip'>Latency {latency_ms} ms</span>")
        if last_sync:
            chips.append(f"<span class='chip'>Sync {safe_timestamp(last_sync)}</span>")
        st.markdown(" ".join(chips), unsafe_allow_html=True)
    with cols[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='metric-card'>" +
                        f"<h4>Balance</h4><div class='value'>${balance:,.2f}</div>" +
                        f"<div class='delta'>Equity ${equity:,.2f}</div>" +
                        "</div>", unsafe_allow_html=True)
        with c2:
            open_positions = status.get('open_positions', 0)
            st.markdown("<div class='metric-card'>" +
                        f"<h4>Open Positions</h4><div class='value'>{open_positions}</div>" +
                        f"<div class='delta'>Symbols {status.get('symbols_trading', 0)}</div>" +
                        "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ========== DASHBOARD TAB ==========
def render_dashboard():
    """Dashboard with live stats"""
    st.subheader("📊 Trading Dashboard")
    
    status = fetch_trading_status()
    conn = fetch_connection_status()
    positions = fetch_positions()
    trades = fetch_trades()
    logs = fetch_analysis_logs(status="ERROR", analysis_type="EXECUTION", limit=15) or []
    feed_logs = fetch_analysis_logs(limit=50) or []
    symbols_info = fetch_symbols_info()
    ai_tuning = fetch_ai_tuning()
    
    # Statistics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📈 Open Positions", len(positions))
    
    with col2:
        winning = len([p for p in positions if p.get('profit', 0) > 0])
        losing = len([p for p in positions if p.get('profit', 0) < 0])
        st.metric("✅ Winning", f"{winning}/{len(positions)}")
    
    with col3:
        total_pnl = sum(p.get('profit', 0) for p in positions)
        st.metric("💵 Unrealized P&L", f"${total_pnl:,.2f}", 
                  delta="Profit" if total_pnl > 0 else ("Loss" if total_pnl < 0 else "—"))
    
    with col4:
        if trades:
            closed_trades = [t for t in trades if t.get('status') == 'closed']
            if closed_trades:
                wins = len([t for t in closed_trades if t.get('profit', 0) > 0])
                win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0
                st.metric("🏆 Win Rate", f"{win_rate:.1f}%")
            else:
                st.metric("🏆 Win Rate", "—", delta="Waiting...")
        else:
            st.metric("🏆 Win Rate", "—", delta="No trades yet")
    
    with col5:
        symbols_active = len(set(p.get('symbol') for p in positions))
        st.metric("🌍 Symbols", f"{symbols_active} active")
    
    st.divider()

    # Execution health KPIs
    st.markdown("### ⚙️ Execution Health")
    c1, c2, c3, c4, c5 = st.columns(5)
    latency = conn.get('latency_ms') if conn else None
    last_sync = conn.get('last_sync') if conn else None
    heartbeat = status.get('last_heartbeat') if status else None
    loop_running = status.get('scheduler_running', False)
    symbols_trading = status.get('symbols_trading', 0)
    spread_fx = conn.get('avg_spread_pips_fx') if conn else None
    spread_crypto = conn.get('avg_spread_pips_crypto') if conn else None

    with c1:
        st.metric("📡 Latency", f"{latency} ms" if latency is not None else "N/A")
    with c2:
        st.metric("🕒 Heartbeat", safe_timestamp(heartbeat))
    with c3:
        st.metric("🔄 Last Sync", safe_timestamp(last_sync))
    with c4:
        st.metric("🧭 Loop", "Running" if loop_running else "Stopped")
    with c5:
        st.metric("🌐 Symbols Trading", symbols_trading)

    c6, c7 = st.columns(2)
    with c6:
        st.metric("📉 Avg FX Spread (pips)", f"{spread_fx:.1f}" if spread_fx is not None else "N/A")
    with c7:
        st.metric("🪙 Avg Crypto Spread (pips)", f"{spread_crypto:.1f}" if spread_crypto is not None else "N/A")

    # Performance strip for closed trades
    closed_trades = [t for t in trades if t.get('status') == 'closed'] if trades else []
    if closed_trades:
        st.markdown("### 📈 Performance Snapshot")
        p1, p2, p3, p4, p5 = st.columns(5)
        profits = [t.get('profit', 0) for t in closed_trades]
        total_profit = sum(profits)
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        largest_win = max(profits) if profits else 0
        largest_loss = min(profits) if profits else 0

        with p1:
            st.metric("💰 Total P&L", f"${total_profit:,.2f}")
        with p2:
            st.metric("🏆 Win Rate", f"{win_rate:.1f}%")
        with p3:
            st.metric("📈 Avg Win", f"${avg_win:,.2f}")
        with p4:
            st.metric("📉 Avg Loss", f"${avg_loss:,.2f}")
        with p5:
            st.metric("🥇/🥵 Max Win/Loss", f"${largest_win:,.0f} / ${largest_loss:,.0f}")
    
    # Show open positions
    if positions:
        st.subheader("📍 Open Positions Details")
        
        pos_data = []
        for p in positions:
            pnl = p.get('profit', 0)
            pnl_color = "🟢" if pnl > 0 else ("🔴" if pnl < 0 else "⚪")
            
            pos_data.append({
                "🎫": str(p.get('ticket', 'N/A')),
                "📍 Symbol": p.get('symbol', 'N/A'),
                "Type": "🔵 BUY" if p.get('type', 0) == 0 else "🔴 SELL",
                "Volume": f"{p.get('volume', 0):.2f}",
                "Entry Price": f"{p.get('price_open', 0):.5f}",
                "Current Price": f"{p.get('price_current', 0):.5f}",
                "P&L": f"{pnl_color} ${pnl:,.2f}"
            })
        
        df = pd.DataFrame(pos_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("💤 No open positions")

    # AI Tuning Panel
    st.divider()
    st.markdown("### 🧠 AI Tuning State")
    if ai_tuning:
        tune_cols = st.columns(4)
        with tune_cols[0]:
            st.metric("⚖️ Risk/Trade", f"{ai_tuning.get('risk_per_trade', 0):.1f}%")
        with tune_cols[1]:
            st.metric("📉 Max Drawdown", f"{ai_tuning.get('max_drawdown', 0):.1f}%")
        with tune_cols[2]:
            st.metric("🛑 Max Positions", ai_tuning.get('max_positions', 25))
        with tune_cols[3]:
            st.metric("📊 Status", ai_tuning.get('status', 'unknown'))
        
        tune_cols2 = st.columns(3)
        with tune_cols2[0]:
            st.metric("🪙 Crypto Cap", f"{ai_tuning.get('crypto_cap', 0):.2f} lots")
        with tune_cols2[1]:
            st.metric("💱 Forex Cap", f"{ai_tuning.get('forex_cap', 0):.2f} lots")
        with tune_cols2[2]:
            st.metric("📈/📉 ATR SL/TP", f"{ai_tuning.get('atr_sl_multiplier', 0):.1f}x / {ai_tuning.get('atr_tp_multiplier', 0):.1f}x")
    else:
        st.info("AI tuning data not available")

    # Recent execution alerts
    st.divider()
    st.markdown("### 🚨 Últimas alertas de ejecución (errores)")
    if logs:
        alert_rows = []
        for log in logs:
            alert_rows.append({
                "⏱️": safe_timestamp(log.get('timestamp')),  # timestamp may be epoch
                "📍 Symbol": log.get('symbol', '—'),
                "🧭 Type": log.get('analysis_type', '—'),
                "Status": log.get('status', '—'),
                "📝 Msg": (log.get('message') or '')[:90],
            })
        st.dataframe(pd.DataFrame(alert_rows), use_container_width=True, height=260)
    else:
        st.success("Sin errores recientes de ejecución")

    # Guardrails: broker volume constraints
    st.divider()
    st.markdown("### 🛡️ Guardrails de volumen (broker)")
    if symbols_info:
        guard_rows = []
        for s in symbols_info:
            sym = s.get('symbol', '—')
            vmin = s.get('volume_min')
            vmax = s.get('volume_max')
            vstep = s.get('volume_step')
            highlight = vmin is not None and vmin >= 10  # crypto CFDs typically 100+
            guard_rows.append({
                "📍": sym,
                "min": vmin,
                "step": vstep,
                "max": vmax,
                "⚠️": "alto" if highlight else "ok",
            })
        df_guard = pd.DataFrame(guard_rows)
        df_guard = df_guard.sort_values(by=["⚠️", "📍"], ascending=[False, True])
        st.dataframe(df_guard, use_container_width=True, height=320)
        st.caption("Nota: min>=10 suele indicar cripto con volumen mínimo 100+ (XRP/ADA/DOGE). El bot ya ajusta al mínimo del broker y rechaza si queda por debajo.")
    else:
        st.info("No se pudo obtener info de símbolos. Asegura que la API esté corriendo y conectada a MT5.")

    # Live event feed (all statuses)
    st.divider()
    st.markdown("### 📡 Live Event Feed")
    feed_status = st.selectbox("Filtrar por estado", ["All", "SUCCESS", "WARNING", "ERROR"], index=0)
    feed_filtered = [l for l in feed_logs if feed_status == "All" or l.get('status') == feed_status]
    if feed_filtered:
        feed_rows = []
        for log in feed_filtered[:50]:
            feed_rows.append({
                "⏱️": safe_timestamp(log.get('timestamp')),
                "📍": log.get('symbol', '—'),
                "Type": log.get('analysis_type', '—'),
                "Status": log.get('status', '—'),
                "📝": (log.get('message') or '')[:120],
            })
        st.dataframe(pd.DataFrame(feed_rows), use_container_width=True, height=320)
    else:
        st.info("Sin eventos recientes con ese filtro")

    # Symbol pulse: P&L by symbol (open positions)
    if positions:
        st.divider()
        st.markdown("### 🌡️ Symbol Pulse (P&L abierto)")
        pnl_by_symbol = {}
        for p in positions:
            sym = p.get('symbol', '—')
            pnl_by_symbol[sym] = pnl_by_symbol.get(sym, 0) + p.get('profit', 0)
        bars = sorted(pnl_by_symbol.items(), key=lambda x: x[1], reverse=True)
        if bars:
            fig = go.Figure([go.Bar(x=[b[0] for b in bars], y=[b[1] for b in bars], marker_color=["#2ee6a0" if v >=0 else "#ff6b6b" for _, v in bars])])
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), title="P&L abierto por símbolo")
            st.plotly_chart(fig, use_container_width=True)

# ========== TRADES HISTORY TAB ==========
def render_trades_history():
    """Show all trades with analysis"""
    st.subheader("📈 Trade History & Analysis")
    
    trades = fetch_trades()
    
    if not trades:
        st.info("No trades history available")
        return
    
    # Separate open and closed
    open_trades = [t for t in trades if t.get('status') == 'open']
    closed_trades = [t for t in trades if t.get('status') == 'closed']
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Trades", len(trades))
    
    with col2:
        if closed_trades:
            wins = len([t for t in closed_trades if t.get('profit', 0) > 0])
            st.metric("✅ Closed Trades", len(closed_trades))
        else:
            st.metric("✅ Closed Trades", 0)
    
    with col3:
        if closed_trades:
            total_profit = sum(t.get('profit', 0) for t in closed_trades)
            st.metric("💰 Closed P&L", f"${total_profit:,.2f}",
                     delta="Profit" if total_profit > 0 else ("Loss" if total_profit < 0 else "—"))
        else:
            st.metric("💰 Closed P&L", "$0.00")
    
    with col4:
        if closed_trades:
            wins = len([t for t in closed_trades if t.get('profit', 0) > 0])
            win_rate = (wins / len(closed_trades) * 100)
            st.metric("🏆 Win Rate", f"{win_rate:.1f}%")
        else:
            st.metric("🏆 Win Rate", "—")
    
    st.divider()
    
    # Tabs for closed vs open
    tab1, tab2 = st.tabs(["✅ Closed Trades", "📈 Open Trades"])
    
    with tab1:
        if closed_trades:
            st.write("**Closed Trades (Completed Transactions)**")
            
            closed_data = []
            for t in closed_trades:
                pnl = t.get('profit', 0)
                pnl_icon = "🟢" if pnl > 0 else ("🔴" if pnl < 0 else "⚪")
                
                closed_data.append({
                    "🎫 Ticket": str(t.get('ticket', 'N/A')),
                    "Symbol": t.get('symbol', 'N/A'),
                    "Type": "🔵 BUY" if t.get('type', 0) == 0 else "🔴 SELL",
                    "Entry": f"{t.get('open_price', 0):.5f}",
                    "Exit": f"{t.get('close_price', 0):.5f}",
                    "Volume": f"{t.get('volume', 0):.2f}",
                    "P&L": f"{pnl_icon} ${pnl:,.2f}"
                })
            
            df_closed = pd.DataFrame(closed_data)
            st.dataframe(df_closed, use_container_width=True, height=400)
            
            # P&L distribution chart
            pnls = [t.get('profit', 0) for t in closed_trades]
            fig = go.Figure(data=[go.Histogram(x=pnls, nbinsx=20)])
            fig.update_layout(title="P&L Distribution", xaxis_title="Profit/Loss ($)", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No closed trades yet")
    
    with tab2:
        if open_trades:
            st.write("**Open Trades (Active Positions)**")
            
            open_data = []
            for t in open_trades:
                pnl = t.get('profit', 0)
                pnl_icon = "🟢" if pnl > 0 else ("🔴" if pnl < 0 else "⚪")
                
                open_data.append({
                    "🎫 Ticket": str(t.get('ticket', 'N/A')),
                    "Symbol": t.get('symbol', 'N/A'),
                    "Type": "🔵 BUY" if t.get('type', 0) == 0 else "🔴 SELL",
                    "Entry": f"{t.get('open_price', 0):.5f}",
                    "Current": f"{t.get('current_price', 0):.5f}",
                    "Volume": f"{t.get('volume', 0):.2f}",
                    "P&L": f"{pnl_icon} ${pnl:,.2f}"
                })
            
            df_open = pd.DataFrame(open_data)
            st.dataframe(df_open, use_container_width=True, height=300)
        else:
            st.info("No open trades")

# ========== AI DECISIONS TAB ==========
def render_decisions():
    """Show AI decision history"""
    st.subheader("🤖 AI Decision History")
    
    decisions = fetch_decisions()
    
    if not decisions:
        st.info("No decision history available")
        return
    
    st.write(f"**Latest {len(decisions[:50])} Decisions**")
    
    # Decision breakdown
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        buy_signals = len([d for d in decisions if d.get('action') == 'BUY'])
        st.metric("🔵 BUY Signals", buy_signals)
    
    with col2:
        sell_signals = len([d for d in decisions if d.get('action') == 'SELL'])
        st.metric("🔴 SELL Signals", sell_signals)
    
    with col3:
        hold_signals = len([d for d in decisions if d.get('action') == 'HOLD'])
        st.metric("⚪ HOLD", hold_signals)
    
    with col4:
        avg_confidence = sum(d.get('confidence', 0) for d in decisions) / len(decisions) if decisions else 0
        st.metric("📊 Avg Confidence", f"{avg_confidence:.1f}%")
    
    st.divider()
    
    # Decision table
    decision_data = []
    for d in decisions[:50]:
        decision_data.append({
            "📍 Symbol": d.get('symbol', 'N/A'),
            "🎯 Action": d.get('action', 'N/A'),
            "📊 Confidence": f"{d.get('confidence', 0):.1f}%",
            "💭 Reasoning": d.get('reasoning', 'N/A')[:60] + "..." if d.get('reasoning') else "N/A",
            "✅ Executed": "Yes" if d.get('executed') else "No"
        })
    
    df_decisions = pd.DataFrame(decision_data)
    st.dataframe(df_decisions, use_container_width=True, height=400)
    
    # Confidence distribution
    confidences = [d.get('confidence', 0) for d in decisions]
    fig = go.Figure(data=[go.Histogram(x=confidences, nbinsx=15)])
    fig.update_layout(title="AI Confidence Distribution", xaxis_title="Confidence (%)", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)

# ========== SYMBOLS TAB ==========
def render_symbols():
    """Show trading symbols configuration"""
    st.subheader("🌍 Trading Symbols (50 Total)")
    show_crypto_only = st.toggle("🔎 Mostrar solo cripto (min_volume altos)", value=False)

    forex_major = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "EURAUD"]
    forex_minor = ["EURCAD", "EURNZD", "GBPAUD", "GBPCAD", "GBPNZD", "AUDCAD", "AUDNZD", "CADCHF", "CHFJPY", "EURUSD"]
    forex_exotic = ["USDSEK", "USDNOK", "USDHKD", "USDSGD", "USDZAR"]
    crypto_top = ["BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "ADAUSD"]
    crypto_alt = ["DOGEUSD", "XRPUSD", "DOTUSD", "LTCUSD", "AVAXUSD"]
    crypto_emerging = ["MATICUSD", "LINKUSD", "UNIUSD", "FTMUSD", "ARBUSD"]

    if not show_crypto_only:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Forex Pairs (30 Symbols) - Variable Hours**")
            st.markdown(
                f"""
                🔹 **Major (10):**
                {', '.join(forex_major)}

                🔹 **Minor (10):**
                {', '.join(forex_minor)}

                🔹 **Exotic (5):**
                {', '.join(forex_exotic)}
                """
            )

        with col2:
            st.write("**Cryptocurrencies (15 Symbols) - 24/7 Trading**")
            st.markdown(
                f"""
                💰 **Top Coins:**
                {', '.join(crypto_top)}

                💰 **Alt Coins:**
                {', '.join(crypto_alt)}

                💰 **Emerging:**
                {', '.join(crypto_emerging)}
                """
            )
    else:
        st.info("Filtrando solo cripto para revisar min_volume elevados (ej. XRP/ADA/DOGE).")
        st.markdown(
            f"""
            💰 **Top Coins:** {', '.join(crypto_top)}

            💰 **Alt Coins:** {', '.join(crypto_alt)}

            💰 **Emerging:** {', '.join(crypto_emerging)}
            """
        )
    
    # Trading configuration
    st.divider()
    st.write("**Current Configuration**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Symbols", "50")
    
    with col2:
        st.metric("📈 Max Positions", "25")
    
    with col3:
        st.metric("💰 Risk/Trade", "2%")
    
    with col4:
        st.metric("⏱️ Timeframe", "M15")

    st.caption("Tip: Los símbolos cripto suelen tener volume_min altos (100+ unidades). Revisa los avisos en ejecución si el volumen se ajusta al mínimo del broker.")

# ========== ANALYSIS LOGS TAB ==========
def render_analysis_logs():
    """Show analysis logs with filters"""
    st.subheader("📝 Analysis Logs & Events")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_symbol_input = st.text_input(
            "Filter by Symbol (leave empty for all)",
            value="",
            placeholder="e.g., EURUSD"
        )
        filter_symbol = filter_symbol_input if filter_symbol_input else None
    
    with col2:
        filter_type = st.selectbox(
            "Analysis Type",
            options=["All", "TECHNICAL", "AI", "EXECUTION", "RISK", "SENTIMENT"],
            index=0
        )
    
    with col3:
        filter_status = st.selectbox(
            "Status",
            options=["All", "SUCCESS", "WARNING", "ERROR"],
            index=0
        )
    
    with col4:
        limit = st.slider("Limit", min_value=10, max_value=500, value=100, step=10)
    
    # Fetch logs with filters
    type_param = filter_type if filter_type != "All" else None
    status_param = filter_status if filter_status != "All" else None
    
    logs = fetch_analysis_logs(
        symbol=filter_symbol,
        analysis_type=type_param,
        status=status_param,
        limit=limit
    )
    
    if not logs:
        st.info("📭 No logs found matching the filters")
        return
    
    st.divider()
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Logs", len(logs))
    
    with col2:
        success_count = len([l for l in logs if l.get('status') == 'SUCCESS'])
        st.metric("✅ Success", success_count)
    
    with col3:
        warning_count = len([l for l in logs if l.get('status') == 'WARNING'])
        st.metric("⚠️ Warnings", warning_count)
    
    with col4:
        error_count = len([l for l in logs if l.get('status') == 'ERROR'])
        st.metric("🔴 Errors", error_count)
    
    st.divider()
    
    # Analysis type breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart - logs by type
        type_counts = {}
        for log in logs:
            atype = log.get('analysis_type', 'UNKNOWN')
            type_counts[atype] = type_counts.get(atype, 0) + 1
        
        if type_counts:
            fig = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title="Logs by Analysis Type",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Bar chart - logs by status
        status_counts = {}
        for log in logs:
            astatus = log.get('status', 'UNKNOWN')
            status_counts[astatus] = status_counts.get(astatus, 0) + 1
        
        if status_counts:
            colors = {"SUCCESS": "#2ed573", "WARNING": "#ffa502", "ERROR": "#ff4757"}
            fig = px.bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                title="Logs by Status",
                labels={"x": "Status", "y": "Count"},
                color=list(status_counts.keys()),
                color_discrete_map=colors
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Detailed logs table
    st.subheader("📋 Detailed Logs")
    
    log_data = []
    for log in logs:
        status_emoji = "✅" if log.get('status') == 'SUCCESS' else ("⚠️" if log.get('status') == 'WARNING' else "🔴")
        
        log_data.append({
            "📅 Time": log.get('timestamp', 'N/A'),
            "📍 Symbol": log.get('symbol', '—'),
            "📊 Type": log.get('analysis_type', 'N/A'),
            "Status": status_emoji + " " + log.get('status', 'N/A'),
            "📝 Message": log.get('message', ''),
            "📌 Details": str(log.get('details', {})) if log.get('details') else "—"
        })
    
    df = pd.DataFrame(log_data)
    st.dataframe(df, use_container_width=True, height=600)
    
    # Download logs as CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Logs (CSV)",
        data=csv,
        file_name=f"analysis_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ========== STATS TAB ==========
def render_statistics():
    """Show overall statistics"""
    st.subheader("📊 Overall Statistics")
    
    trades = fetch_trades()
    positions = fetch_positions()
    status = fetch_trading_status()
    
    if trades:
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        
        if closed_trades:
            col1, col2, col3 = st.columns(3)
            
            # Profit metrics
            profits = [t.get('profit', 0) for t in closed_trades]
            total_profit = sum(profits)
            wins = len([p for p in profits if p > 0])
            losses = len([p for p in profits if p < 0])
            
            with col1:
                st.metric("📊 Total Trades", len(closed_trades))
                st.metric("✅ Wins", wins)
                st.metric("🔴 Losses", losses)
            
            with col2:
                st.metric("💰 Total P&L", f"${total_profit:,.2f}")
                st.metric("📈 Avg Win", f"${sum([p for p in profits if p > 0]) / wins:,.2f}" if wins > 0 else "$0.00")
                st.metric("📉 Avg Loss", f"${sum([p for p in profits if p < 0]) / losses:,.2f}" if losses > 0 else "$0.00")
            
            with col3:
                st.metric("🏆 Win Rate", f"{(wins/len(closed_trades)*100):.1f}%")
                st.metric("📊 Profit Factor", f"{total_profit / abs(sum([p for p in profits if p < 0])):,.2f}" if losses > 0 else "∞")
                st.metric("💵 Largest Win", f"${max(profits):,.2f}" if profits else "$0.00")
        else:
            st.info("No closed trades for statistics yet")
    else:
        st.info("No trades history")

# ========== AI BACKTEST TAB ==========
def render_ai_backtest():
    """Run and display AI strategy backtest"""
    st.subheader("🧪 AI Strategy Backtest (Live Data)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        bt_symbol = st.selectbox("Select Symbol", [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", 
            "XRPUSD", "ADAUSD", "LTCUSD", "DOGEUSD"
        ], index=0)
    with col2:
        bt_candles = st.slider("Candles (15-min)", 20, 200, 50, step=10)
    with col3:
        if st.button("🚀 Run Backtest", key="run_bt"):
            st.session_state.run_backtest = True
    
    if st.session_state.get("run_backtest"):
        with st.spinner(f"Running backtest for {bt_symbol}..."):
            bt_result = fetch_mini_backtest(symbol=bt_symbol, candles=bt_candles)
        
        if bt_result.get("status") == "completed":
            st.success(f"✅ Backtest completed: {bt_result.get('total_trades')} trades")
            
            bt_cols = st.columns(5)
            with bt_cols[0]:
                st.metric("📊 Total Trades", bt_result.get('total_trades', 0))
            with bt_cols[1]:
                st.metric("✅ Winners", bt_result.get('winning_trades', 0))
            with bt_cols[2]:
                st.metric("🏆 Win Rate", f"{bt_result.get('win_rate', 0):.1f}%")
            with bt_cols[3]:
                st.metric("💰 P&L", f"${bt_result.get('total_profit', 0):,.2f}")
            with bt_cols[4]:
                st.metric("📉 Max DD", f"{bt_result.get('max_drawdown', 0):.1f}%")
            
            st.info(f"💡 Profit Factor: {bt_result.get('profit_factor', 0):.2f}")
        elif bt_result.get("status") == "no_data":
            st.warning(f"⚠️ No historical data available for {bt_symbol}")
        elif bt_result.get("status") == "error":
            st.error(f"❌ Error: {bt_result.get('message', 'Unknown error')}")
        else:
            st.info("Ready to backtest. Select symbol and candles, then click 'Run Backtest'.")


# ========== MAIN APP ==========
st.title("🤖 AI Trading Bot Control Panel")

render_header()
st.divider()

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "📈 Trades",
    "🤖 AI Decisions",
    "🌍 Symbols",
    "📝 Analysis Logs",
    "📉 Statistics",
    "🧪 AI Backtest"
])

with tab1:
    render_dashboard()

with tab2:
    render_trades_history()

with tab3:
    render_decisions()

with tab4:
    render_symbols()

with tab5:
    render_analysis_logs()

with tab6:
    render_statistics()

with tab7:
    render_ai_backtest()

# Footer
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Force Refresh (clear cache)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col2:
    st.info("✅ Cache: 10s | Async API calls | Last update: " + datetime.now().strftime("%H:%M:%S"))


