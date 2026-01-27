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
CACHE_TTL = 2

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
def api_call(endpoint: str):
    """Make API call with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=3)
        if response.status_code == 200:
            return response.json()
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

# Page Config
st.set_page_config(
    page_title="AI Trading Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    .status-connected {
        background: #2ed573;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        display: inline-block;
    }
    .status-offline {
        background: #ff4757;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        display: inline-block;
    }
    .trade-win {
        background: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
    }
    .trade-loss {
        background: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ========== HEADER ==========
def render_header():
    """Professional header with account info"""
    config = get_config()
    conn = fetch_connection_status()
    status = fetch_trading_status()
    
    st.markdown("<div class='header-container'>", unsafe_allow_html=True)
    st.markdown("<h1>🤖 AI Forex & Crypto Trading Bot</h1>", unsafe_allow_html=True)
    st.markdown("<p>Automated Trading with Gemini AI | 50 Symbols | 2% Risk Per Trade</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        balance = status.get('balance', 0)
        st.metric("💰 Balance", f"${balance:,.2f}" if balance else "—")
    
    with col2:
        equity = status.get('equity', 0)
        st.metric("📊 Equity", f"${equity:,.2f}" if equity else "—")
    
    with col3:
        mode = "LIVE" if not config.is_paper_mode() else "PAPER"
        st.metric("🎯 Mode", mode)
    
    with col4:
        is_connected = conn.get('connected', False)
        status_text = "✅ Connected" if is_connected else "📡 Technical Mode"
        st.metric("🔗 MT5", status_text)
    
    with col5:
        is_running = status.get('scheduler_running', False)
        status_text = "🟢 Running" if is_running else "⚪ Stopped"
        st.metric("🔄 Loop", status_text)

# ========== DASHBOARD TAB ==========
def render_dashboard():
    """Dashboard with live stats"""
    st.subheader("📊 Trading Dashboard")
    
    status = fetch_trading_status()
    positions = fetch_positions()
    trades = fetch_trades()
    
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Forex Pairs (30 Symbols) - Variable Hours**")
        forex = """
        🔹 **Major (10):**
        EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, EURJPY, GBPJPY, EURGBP, EURAUD
        
        🔹 **Minor (10):**
        EURCAD, EURNZD, GBPAUD, GBPCAD, GBPNZD, AUDCAD, AUDNZD, CADCHF, CHFJPY, EURUSD
        
        🔹 **Exotic (5):**
        USDSEK, USDNOK, USDHKD, USDSGD, USDZAR
        """
        st.markdown(forex)
    
    with col2:
        st.write("**Cryptocurrencies (15 Symbols) - 24/7 Trading**")
        crypto = """
        💰 **Top Coins:**
        BTCUSD, ETHUSD, BNBUSD, SOLUSD, ADAUSD
        
        💰 **Alt Coins:**
        DOGEUSD, XRPUSD, DOTUSD, LTCUSD, AVAXUSD
        
        💰 **Emerging:**
        MATICUSD, LINKUSD, UNIUSD, FTMUSD, ARBUSD
        """
        st.markdown(crypto)
    
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

# ========== MAIN APP ==========
st.title("🤖 AI Trading Bot Control Panel")

render_header()
st.divider()

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📈 Trades",
    "🤖 AI Decisions",
    "🌍 Symbols",
    "📉 Statistics"
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
    render_statistics()

# Footer
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Refresh All Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col2:
    st.info("✅ Auto-refresh every 2 seconds | Last update: " + datetime.now().strftime("%H:%M:%S"))


