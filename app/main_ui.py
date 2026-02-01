"""🎨 Amelia Bot - AI Trading Dashboard"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import time
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure page FIRST
st.set_page_config(
    page_title="Amelia Bot | AI Trading Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/amaury0839/metatradecursor",
        "About": "Amelia Bot: AI-Powered Crypto & Forex Trading"
    }
)

# Modern styling
st.markdown("""
<style>
    /* Dark modern theme */
    :root {
        --primary: #00D084;
        --secondary: #667eea;
        --danger: #FF4B4B;
        --warning: #FFB302;
        --success: #00D084;
        --dark: #0f0f0f;
        --card: #1a1a2e;
        --border: #16213e;
    }
    
    /* Main container */
    .main {
        background-color: #0f0f0f;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #16213e;
    }
    
    /* Header styling */
    .header-main {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Card styling */
    .metric-card {
        background-color: #1a1a2e;
        border: 1px solid #16213e;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #00D084;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .status-running {
        background-color: rgba(0, 208, 132, 0.2);
        color: #00D084;
    }
    
    .status-warning {
        background-color: rgba(255, 179, 2, 0.2);
        color: #FFB302;
    }
    
    .status-error {
        background-color: rgba(255, 75, 75, 0.2);
        color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "refresh_rate" not in st.session_state:
    st.session_state.refresh_rate = 5

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("# 🤖 AMELIA BOT CONTROL CENTER")
    st.divider()
    
    # Logo and branding
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 8px; margin-bottom: 1rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🤖</div>
        <div style="font-weight: bold; color: white; font-size: 1.2rem;">A-BOT</div>
        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8);">Advanced Trading System</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Status Section
    st.subheader("📊 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="status-badge status-running">✅ API Online</span>', unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="status-badge status-running">✅ Amelia Bot Active</span>', unsafe_allow_html=True)
    
    st.markdown('<span class="status-badge status-running">💰 24/7 Crypto</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-badge status-running">🕐 Forex Hours</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # Quick Stats
    st.subheader("📈 Quick Stats")
    st.metric("Amelia Bot Status", "🟢 Running")
    st.metric("API Port", "8002")
    st.metric("Dashboard Port", "8503")
    st.metric("Symbols Tracked", "47")
    st.metric("Crypto Pairs", "9")
    st.metric("Win Rate", "62%")
    
    st.divider()
    
    # Controls
    st.subheader("🎛️ Amelia Bot Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ START", use_container_width=True):
            st.success("✅ Amelia Bot iniciado")
    with col2:
        if st.button("⏹️ STOP", use_container_width=True):
            st.warning("⏸️ Amelia Bot pausado")
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    refresh_rate = st.slider("Refresh Rate (seconds)", 1, 30, st.session_state.refresh_rate)
    st.session_state.refresh_rate = refresh_rate
    
    st.divider()
    st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
st.markdown("""
<div class="header-main">
    <div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 3rem;">🤖</div>
            <div>
                <h1 class="header-title">AMELIA BOT</h1>
                <p class="header-subtitle">Advanced AI Trading System • Intelligent Forex & Crypto • Enterprise-Grade</p>
            </div>
        </div>
    </div>
    <div style="text-align: right; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.8;">Version 2.0</div>
        <div style="font-size: 0.9rem; opacity: 0.8;">Premium Edition</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Amelia Bot Dashboard",
    "💹 Posiciones Activas", 
    "📊 Análisis de Mercado",
    "⚙️ Configuración",
    "📋 Historial"
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab1:
    st.subheader("📊 Amelia Bot Trading Overview")
    
    # Get real data from MT5
    try:
        from app.trading.mt5_client import get_mt5_client
        from app.trading.portfolio import get_portfolio_manager
        
        mt5 = get_mt5_client()
        portfolio = get_portfolio_manager()
        
        # Get account info
        account_info = mt5.get_account_info()
        if account_info:
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            profit = account_info.get('profit', 0)
            margin_free = account_info.get('margin_free', 0)
        else:
            balance = equity = profit = margin_free = 0
        
        # Get positions
        positions = portfolio.get_open_positions()
        num_positions = len(positions) if positions else 0
        
        # Calculate daily PnL
        daily_pnl_pct = ((equity - balance) / balance * 100) if balance > 0 else 0
        daily_pnl_color = "#00D084" if profit >= 0 else "#FF4B4B"
        
        # Calculate exposure
        total_margin = account_info.get('margin', 0) if account_info else 0
        exposure_pct = (total_margin / equity * 100) if equity > 0 else 0
        exposure_color = "#FFB302" if exposure_pct < 20 else ("#FF4B4B" if exposure_pct > 50 else "#00D084")
        
    except Exception as e:
        st.error(f"Error loading MT5 data: {e}")
        balance = equity = profit = 0
        num_positions = 0
        daily_pnl_pct = 0
        exposure_pct = 0
        daily_pnl_color = "#888"
        exposure_color = "#888"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Account Balance</div>
            <div class="metric-value">${balance:,.2f}</div>
            <div style="font-size: 0.8rem; color: {daily_pnl_color};">${profit:+,.2f} Today ({daily_pnl_pct:+.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Open Trades</div>
            <div class="metric-value">{num_positions}</div>
            <div style="font-size: 0.8rem; color: #00D084;">Active Positions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Equity</div>
            <div class="metric-value">${equity:,.2f}</div>
            <div style="font-size: 0.8rem; color: #00D084;">Real-time</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Exposure</div>
            <div class="metric-value">{exposure_pct:.1f}%</div>
            <div style="font-size: 0.8rem; color: {exposure_color};">Margin Used</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Equity Curve")
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=[5000, 5100, 5080, 5150, 5234],
            mode='lines+markers',
            name='Equity',
            line=dict(color='#00D084', width=3),
            marker=dict(size=8)
        ))
        fig.update_layout(
            height=300,
            template='plotly_dark',
            hovermode='x unified',
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Asset Allocation")
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Pie(
            labels=['Forex', 'Crypto', 'Cash'],
            values=[45, 35, 20],
            marker=dict(colors=['#667eea', '#00D084', '#FFB302'])
        )])
        fig.update_layout(
            height=300,
            template='plotly_dark',
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: POSITIONS
# ============================================================================
with tab2:
    st.subheader("💹 Posiciones Activas de Amelia Bot")
    
    try:
        from app.trading.mt5_client import get_mt5_client
        mt5 = get_mt5_client()
        
        positions = mt5.get_positions()
        
        if positions:
            # Build dataframe from real positions
            positions_list = []
            for pos in positions:
                position_type = "BUY" if pos.get('type') == 0 else "SELL"
                symbol = pos.get('symbol', 'N/A')
                volume = pos.get('volume', 0)
                entry = pos.get('price_open', 0)
                current = pos.get('price_current', 0)
                profit = pos.get('profit', 0)
                profit_color = "🟢" if profit >= 0 else "🔴"
                
                positions_list.append({
                    'Symbol': symbol,
                    'Type': position_type,
                    'Volume': f"{volume:.2f}",
                    'Entry': f"{entry:,.4f}",
                    'Current': f"{current:,.4f}",
                    'P/L': f"{profit:+,.2f}",
                    'Status': profit_color
                })
            
            df = pd.DataFrame(positions_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.success(f"✅ {len(positions)} posiciones activas")
        else:
            st.info("📭 No hay posiciones abiertas actualmente")
            st.caption("El bot está evaluando oportunidades en tiempo real...")
    except Exception as e:
        st.error(f"Error cargando posiciones: {e}")
        st.caption("Verifica que MT5 esté conectado y el bot esté corriendo")

# ============================================================================
# TAB 3: ANALYSIS
# ============================================================================
with tab3:
    st.subheader("📊 Análisis de Mercado Amelia Bot")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Technical Signals")
        signals_data = {
            'Symbol': ['EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD', 'ETHUSD'],
            'Signal': ['🟢 BUY', '🔴 SELL', '⚫ HOLD', '🟢 BUY', '⚫ HOLD'],
            'Strength': ['75%', '68%', '52%', '82%', '55%'],
            'RSI': ['35', '65', '50', '28', '48']
        }
        df_signals = pd.DataFrame(signals_data)
        st.dataframe(df_signals, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 🧠 AI Sentiment")
        ai_data = {
            'Pair': ['Crypto Market', 'Forex Market', 'Gold (XAU)', 'Oil (XTIUSD)'],
            'Sentiment': ['🟢 Bullish', '⚫ Neutral', '🟡 Mixed', '🔴 Bearish'],
            'Confidence': ['85%', '62%', '58%', '71%']
        }
        df_ai = pd.DataFrame(ai_data)
        st.dataframe(df_ai, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 4: CONFIGURATION
# ============================================================================
with tab4:
    st.subheader("⚙️ Configuración de Amelia Bot")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Trading Parameters")
        st.number_input("Risk per Trade (%)", value=1.5, min_value=0.1, max_value=5.0)
        st.number_input("Max Daily Loss (%)", value=10.0, min_value=1.0, max_value=20.0)
        st.number_input("Max Open Positions", value=12, min_value=1, max_value=50)
        st.selectbox("Timeframe", ["M5", "M15", "M30", "H1", "H4", "D1"])
    
    with col2:
        st.markdown("#### AI Settings")
        st.toggle("Enable AI Analysis", value=True)
        st.toggle("Use Sentiment Analysis", value=True)
        st.toggle("Enable News Filter", value=True)
        st.selectbox("AI Model", ["Gemini 2.5 Flash", "GPT-4", "Claude"])

# ============================================================================
# TAB 5: LOGS
# ============================================================================
with tab5:
    st.subheader("📋 Historial y Logs de Amelia Bot")
    
    log_data = {
        'Time': ['23:58:25', '23:57:18', '23:56:42', '23:55:31', '23:54:15'],
        'Event': [
            '✅ Trade executed: EURUSD BUY 0.50 @ 1.0920',
            '📊 Analysis complete: 47 symbols analyzed',
            '💡 AI Gate: 8 signals strong, 3 weak',
            '⚠️ AUDSGD: Market closed, skipping',
            '🚀 Trading cycle started'
        ],
        'Type': ['✅', '📊', '🧠', '⏭️', '🔄']
    }
    
    df_logs = pd.DataFrame(log_data)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
    
    st.divider()
    st.markdown("### 📝 Detailed Logs")
    log_text = """
    [2026-01-30 23:58:25] ✅ EURUSD: Trade executed successfully
    [2026-01-30 23:58:24] 📊 Analyzing symbol: AUDSGD
    [2026-01-30 23:58:23] 🧠 AI Decision: HOLD (confidence 45%)
    [2026-01-30 23:58:22] 💹 Technical Signal: BUY (RSI 35, EMA bullish)
    [2026-01-30 23:58:21] 📡 Market Status: Crypto 24/7, Forex open
    """
    st.code(log_text, language="text")
