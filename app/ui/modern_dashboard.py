"""
Modern Streamlit dashboard for the trading bot.
Focused on a cleaner UI, de-duplicated logic, and a statement view.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.core.config import get_config
from app.core.database import get_database_manager
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.ui.ui_components import section_header, stat_card, metric_grid, empty_state

logger = setup_logger("ui_modern")


def apply_ui_theme() -> None:
    """Inject a modern, intentional visual style."""
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=DM+Sans:wght@400;500;700&display=swap');

:root {
    --ink: #121316;
    --subtle: #6a6f78;
    --accent: #2fbf8f;
    --accent-2: #f7b267;
    --panel: #ffffff;
    --panel-2: #f7f5ef;
    --border: #e7e2d8;
    --shadow: rgba(20, 20, 20, 0.08);
}

html, body, [class*="st-"] {
    font-family: "DM Sans", system-ui, -apple-system, sans-serif;
    color: var(--ink);
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 10% -10%, #f8efe2 0%, transparent 60%),
        radial-gradient(900px 500px at 90% 10%, #eaf7f1 0%, transparent 55%),
        linear-gradient(180deg, #f7f5ef 0%, #f2f1ec 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8f6f1 100%);
    border-right: 1px solid var(--border);
}

h1, h2, h3, h4, h5, h6 {
    font-family: "Space Grotesk", system-ui, -apple-system, sans-serif;
    letter-spacing: -0.02em;
}

.hero {
    background: linear-gradient(135deg, #1f2933 0%, #0b0d0f 100%);
    color: #ffffff;
    border-radius: 18px;
    padding: 28px 32px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.25);
    position: relative;
    overflow: hidden;
}

.hero:after {
    content: "";
    position: absolute;
    top: -60px;
    right: -60px;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(47,191,143,0.35), transparent 65%);
}

.hero-title {
    font-size: 2.2rem;
    margin: 0;
}

.hero-subtitle {
    color: #c8d0da;
    margin-top: 6px;
    font-size: 0.95rem;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    color: #ffffff;
    font-size: 0.85rem;
    margin-right: 6px;
}

.stat-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 10px 20px var(--shadow);
    animation: fadeUp 0.7s ease both;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 700;
}

.stat-label {
    color: var(--subtle);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.soft-panel {
    background: var(--panel-2);
    border: 1px dashed var(--border);
    border-radius: 12px;
    padding: 16px;
}

.section-title {
    font-size: 1.1rem;
    margin-bottom: 6px;
}

.table-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 10px 20px var(--shadow);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _get_db():
    if "db" not in st.session_state:
        st.session_state.db = get_database_manager()
    return st.session_state.db


def _get_config():
    if "config" not in st.session_state:
        st.session_state.config = get_config()
    return st.session_state.config


def get_mt5_status() -> Dict[str, Any]:
    """Check MT5 connection status from shared state."""
    try:
        from app.core.shared_state import get_shared_state_manager
        shared_state = get_shared_state_manager()
        state_data = shared_state.get_state()
        
        if state_data and 'mt5' in state_data:
            mt5_data = state_data['mt5']
            return {
                "connected": mt5_data.get('connected', False),
                "account": mt5_data.get('account', 0),
                "balance": mt5_data.get('balance', 0.0),
                "equity": mt5_data.get('equity', 0.0),
                "margin_free": mt5_data.get('margin_free', 0.0),
                "margin_level": mt5_data.get('margin_level', 0.0),
                "last_update": state_data.get('last_update', ''),
            }
    except Exception as exc:
        logger.error("Failed to read shared state: %s", exc)

    return {"connected": False}


def get_trading_stats(days: int = 30) -> Dict[str, Any]:
    """Get trading statistics from the history database."""
    try:
        db = _get_db()
        return db.get_performance_summary(days=days)
    except Exception as exc:
        logger.error("Failed to get trading stats: %s", exc)
        return {}


def render_header() -> None:
    """Render the hero header with status chips."""
    mt5_status = get_mt5_status()
    status_text = "Connected" if mt5_status.get("connected") else "Offline"
    account_text = (
        f"Account {mt5_status.get('account')}"
        if mt5_status.get("connected")
        else "No account"
    )

    st.markdown(
        f"""
<div class="hero">
  <div class="hero-title">MetaTrade Control Room</div>
  <div class="hero-subtitle">AI trading operations, risk, and performance in one view.</div>
  <div style="margin-top: 16px;">
    <span class="chip">MT5: {status_text}</span>
    <span class="chip">{account_text}</span>
    <span class="chip">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Sidebar with enhanced status and controls."""
    with st.sidebar:
        st.markdown("## 🎛️ Control Panel")
        st.caption("Realtime status and quick controls")
        
        # MT5 Connection Status
        mt5_status = get_mt5_status()
        status = "🟢 Connected" if mt5_status.get("connected") else "🔴 Offline"
        
        st.markdown(f"### MT5 Status: {status}")
        
        if mt5_status.get("connected"):
            st.write(f"**Account:** {mt5_status.get('account')}")
            st.write(f"**Balance:** ${mt5_status.get('balance', 0):,.2f}")
            st.write(f"**Equity:** ${mt5_status.get('equity', 0):,.2f}")
            st.write(f"**Free Margin:** ${mt5_status.get('margin_free', 0):,.2f}")
            
            # Margin level indicator
            margin_level = mt5_status.get('margin_level', 0)
            if margin_level >= 200:
                st.success(f"Margin Level: {margin_level:.0f}% ✅")
            elif margin_level >= 100:
                st.warning(f"Margin Level: {margin_level:.0f}% ⚠️")
            else:
                st.error(f"Margin Level: {margin_level:.0f}% 🚨")
            
            # Last update
            last_update = mt5_status.get('last_update', '')
            if last_update:
                st.caption(f"Updated: {last_update}")
        
        st.divider()
        
        # Trading statistics
        st.markdown("### 📊 Quick Stats")
        try:
            mt5_client = get_mt5_client()
            positions = mt5_client.get_positions()
            
            if positions:
                total_profit = sum(p.get('profit', 0) for p in positions)
                buy_count = sum(1 for p in positions if p.get('type') == 0)
                sell_count = sum(1 for p in positions if p.get('type') == 1)
                
                st.metric("Open Positions", len(positions))
                st.metric("Floating P&L", f"${total_profit:.2f}")
                st.write(f"🟢 Buy: {buy_count} | 🔴 Sell: {sell_count}")
            else:
                st.info("No open positions")
        except Exception as e:
            st.warning("Could not load positions")
        
        st.divider()
        
        # Controls
        st.markdown("### ⚙️ Settings")
        
        # Auto-refresh toggle
        auto_refresh = st.toggle("Auto-refresh", value=True)
        if auto_refresh:
            refresh_rate = st.slider("Refresh rate (seconds)", 5, 60, 15, 5)
            st.caption(f"Dashboard updates every {refresh_rate}s")
        
        # Risk profile selector
        st.selectbox(
            "Risk Profile",
            ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"],
            index=1,
            help="Select your risk profile (requires bot restart)"
        )
        
        st.divider()
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("📊 Export", use_container_width=True):
                st.info("Go to Statement tab to export")
        
        st.divider()
        
        # System info
        st.markdown("### ℹ️ System")
        st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption("Version: 1.0.0")
        st.caption("Mode: Live Trading")


def render_quick_stats() -> None:
    """Render quick statistics cards."""
    mt5_status = get_mt5_status()

    col1, col2, col3, col4 = st.columns(4)
    if mt5_status.get("connected"):
        balance = mt5_status.get("balance", 0.0)
        equity = mt5_status.get("equity", 0.0)
        margin_free = mt5_status.get("margin_free", 0.0)
        margin_used = max(balance - margin_free, 0.0)
        usage = (margin_used / balance * 100) if balance else 0.0

        with col1:
            stat_card("Balance", f"${balance:,.2f}", "Account balance")
        with col2:
            stat_card("Equity", f"${equity:,.2f}", "Balance plus open PnL")
        with col3:
            stat_card("Free Margin", f"${margin_free:,.2f}", "Available margin")
        with col4:
            stat_card("Margin Used", f"{usage:.1f}%", "Utilization")
    else:
        with col1:
            stat_card("MT5 Status", "Offline", "Connect MT5 to load metrics")
        with col2:
            stat_card("Balance", "N/A", "No account data")
        with col3:
            stat_card("Equity", "N/A", "No account data")
        with col4:
            stat_card("Margin Used", "N/A", "No account data")


def _plot_equity_curve(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["close_timestamp"],
            y=df["cumulative_pnl"],
            mode="lines+markers",
            line=dict(color="#2fbf8f", width=3),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(47,191,143,0.2)",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="Close time",
        yaxis_title="Cumulative net PnL",
        template="plotly_white",
    )
    return fig


def render_dashboard_tab() -> None:
    """Main dashboard view with enhanced real-time data."""
    section_header("Live overview")
    render_quick_stats()

    # Add real-time trading activity
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        section_header("Open Positions Summary", "Live from MT5")
        try:
            mt5_client = get_mt5_client()
            positions = mt5_client.get_positions()
            
            if positions:
                # Group by type
                buy_count = sum(1 for p in positions if p.get('type') == 0)
                sell_count = sum(1 for p in positions if p.get('type') == 1)
                total_profit = sum(p.get('profit', 0) for p in positions)
                
                metric_grid([
                    {"label": "Total Positions", "value": str(len(positions)), "note": "Live now"},
                    {"label": "Buy Positions", "value": str(buy_count), "note": "Long"},
                    {"label": "Sell Positions", "value": str(sell_count), "note": "Short"},
                    {"label": "Unrealized P&L", "value": f"${total_profit:.2f}", "note": "Floating"},
                ], columns=4)
                
                # Top 5 profitable/losing positions
                sorted_positions = sorted(positions, key=lambda x: x.get('profit', 0), reverse=True)
                
                st.markdown("#### 🏆 Top Performers")
                top_5 = sorted_positions[:5]
                for p in top_5:
                    profit = p.get('profit', 0)
                    symbol = p.get('symbol', 'N/A')
                    ptype = "🟢 BUY" if p.get('type') == 0 else "🔴 SELL"
                    st.write(f"{symbol} {ptype}: **${profit:.2f}**")
                
            else:
                st.info("No open positions - Account is flat")
        except Exception as e:
            st.warning(f"Could not load live positions: {e}")
    
    with col2:
        section_header("Account Health", "Risk metrics")
        mt5_status = get_mt5_status()
        if mt5_status.get("connected"):
            balance = mt5_status.get("balance", 0)
            equity = mt5_status.get("equity", 0)
            margin_free = mt5_status.get("margin_free", 0)
            margin_level = mt5_status.get("margin_level", 0)
            
            # Calculate drawdown
            drawdown = ((balance - equity) / balance * 100) if balance > 0 else 0
            
            st.metric("Margin Level", f"{margin_level:.0f}%", 
                     help="Margin level indicator (should be > 100%)")
            st.metric("Drawdown", f"{abs(drawdown):.2f}%",
                     delta=f"{'⚠️' if abs(drawdown) > 5 else '✅'}")
            
            # Risk gauge
            if margin_level >= 200:
                risk_status = "🟢 Low Risk"
            elif margin_level >= 100:
                risk_status = "🟡 Moderate Risk"
            else:
                risk_status = "🔴 High Risk"
            
            st.write(f"**Risk Status:** {risk_status}")

    section_header("Performance snapshot", "Closed trades over the last 30 days")
    stats = get_trading_stats(days=30)
    metric_grid(
        [
            {"label": "Trades (30d)", "value": str(stats.get("total_trades", 0)), "note": "Closed trades"},
            {"label": "Win Rate", "value": f"{stats.get('win_rate', 0.0):.1f}%", "note": "Closed trades"},
            {"label": "Net PnL", "value": f"${stats.get('net_profit', 0.0):,.2f}", "note": "Last 30 days"},
            {"label": "Profit Factor", "value": f"{stats.get('profit_factor', 0.0):.2f}", "note": "Gross profit/loss"},
        ],
        columns=4,
    )

    section_header("PnL curve", "Closed trades only")
    db = _get_db()
    end = datetime.now()
    start = end - timedelta(days=30)
    trades = db.get_closed_trades(start, end)
    df = pd.DataFrame(trades)
    if df.empty:
        empty_state("No closed trades", "No closed trades found in the last 30 days.")
    else:
        df["close_timestamp"] = pd.to_datetime(df["close_timestamp"])
        df["net_pnl"] = (
            df["profit"].fillna(0)
            - df["commission"].fillna(0)
            - df["swap"].fillna(0)
        )
        df = df.sort_values("close_timestamp")
        df["cumulative_pnl"] = df["net_pnl"].cumsum()
        st.plotly_chart(_plot_equity_curve(df), use_container_width=True)


def render_positions_tab() -> None:
    """Open positions view - live from MT5."""
    section_header("Live positions")
    
    try:
        # Get live positions from MT5
        mt5_client = get_mt5_client()
        positions = mt5_client.get_positions()
        
        if not positions:
            st.info("✅ No open positions - Account is flat")
            return
        
        # Calculate totals
        total_profit = sum(p.get('profit', 0) for p in positions)
        total_volume = sum(p.get('volume', 0) for p in positions)
        buy_positions = sum(1 for p in positions if p.get('type') == 0)
        sell_positions = sum(1 for p in positions if p.get('type') == 1)
        
        # Show metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Open Positions", len(positions))
        with col2:
            profit_delta = "📈" if total_profit > 0 else "📉" if total_profit < 0 else "➖"
            st.metric("Total P&L", f"${total_profit:.2f}", delta=profit_delta)
        with col3:
            st.metric("Total Volume", f"{total_volume:.2f} lots")
        with col4:
            st.metric("Buy/Sell", f"{buy_positions}/{sell_positions}")
        with col5:
            mt5_status = get_mt5_status()
            equity = mt5_status.get('equity', 0)
            exposure_pct = (abs(total_profit) / equity * 100) if equity > 0 else 0
            st.metric("Exposure", f"{exposure_pct:.2f}%")
        
        st.markdown("---")
        
        # Build enhanced dataframe
        position_data = []
        for p in positions:
            # Calculate unrealized P&L percentage
            entry_price = p.get('price_open', 0)
            current_price = p.get('price_current', 0)
            profit = p.get('profit', 0)
            volume = p.get('volume', 0)
            
            # Price change
            if entry_price > 0:
                price_change_pct = ((current_price - entry_price) / entry_price * 100)
                if p.get('type') == 1:  # SELL position
                    price_change_pct = -price_change_pct
            else:
                price_change_pct = 0
            
            # Duration
            time_create = p.get('time', 0)
            if time_create > 0:
                duration = datetime.now() - datetime.fromtimestamp(time_create)
                duration_str = f"{duration.days}d {duration.seconds//3600}h" if duration.days > 0 else f"{duration.seconds//3600}h {(duration.seconds//60)%60}m"
            else:
                duration_str = "N/A"
            
            position_data.append({
                "Ticket": p.get('ticket', 'N/A'),
                "Symbol": p.get('symbol', 'N/A'),
                "Type": "🟢 BUY" if p.get('type') == 0 else "🔴 SELL",
                "Volume": f"{volume:.2f}",
                "Entry": f"{entry_price:.5f}",
                "Current": f"{current_price:.5f}",
                "SL": f"{p.get('sl', 0):.5f}" if p.get('sl', 0) > 0 else "None",
                "TP": f"{p.get('tp', 0):.5f}" if p.get('tp', 0) > 0 else "None",
                "Change %": f"{price_change_pct:+.2f}%",
                "Profit": f"${profit:.2f}",
                "Swap": f"${p.get('swap', 0):.2f}",
                "Duration": duration_str,
                "Comment": p.get('comment', '')[:20],
            })
        
        df = pd.DataFrame(position_data)
        
        # Color-code profit column
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Profit": st.column_config.NumberColumn(
                    "Profit",
                    format="$%.2f",
                ),
                "Change %": st.column_config.TextColumn(
                    "Change %",
                ),
            }
        )
        
        # Group by symbol
        st.markdown("### 📊 Exposure by Symbol")
        symbol_groups = {}
        for p in positions:
            symbol = p.get('symbol', 'Unknown')
            if symbol not in symbol_groups:
                symbol_groups[symbol] = {'count': 0, 'profit': 0, 'volume': 0}
            symbol_groups[symbol]['count'] += 1
            symbol_groups[symbol]['profit'] += p.get('profit', 0)
            symbol_groups[symbol]['volume'] += p.get('volume', 0)
        
        symbol_df = pd.DataFrame([
            {
                'Symbol': symbol,
                'Positions': data['count'],
                'Total Volume': f"{data['volume']:.2f}",
                'Net P&L': f"${data['profit']:.2f}"
            }
            for symbol, data in sorted(symbol_groups.items(), key=lambda x: x[1]['profit'], reverse=True)
        ])
        
        st.dataframe(symbol_df, use_container_width=True, hide_index=True)
            
    except Exception as exc:
        st.error(f"Error loading positions from MT5: {exc}")
        logger.error(f"Position tab error: {exc}", exc_info=True)


def render_analysis_tab() -> None:
    """Analysis and insights view with real data from database."""
    section_header("Market analysis & AI insights")
    
    try:
        db = _get_db()
        
        # Get recent AI decisions (last 24 hours)
        try:
            conn = sqlite3.connect('data/trading_history.db')
            cursor = conn.cursor()
            
            # AI decisions stats
            cursor.execute("""
                SELECT 
                    decision,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM ai_decisions
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY decision
            """)
            ai_stats = cursor.fetchall()
            
            # Recent analysis
            cursor.execute("""
                SELECT 
                    symbol,
                    signal,
                    rsi,
                    trend_bullish,
                    trend_bearish,
                    timestamp
                FROM analysis_history
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
                LIMIT 50
            """)
            recent_analysis = cursor.fetchall()
            
            conn.close()
            
            # Display AI decision distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🤖 AI Decision Mix (24h)")
                if ai_stats:
                    total_decisions = sum(row[1] for row in ai_stats)
                    decision_data = []
                    for decision, count, avg_conf in ai_stats:
                        pct = (count / total_decisions * 100) if total_decisions > 0 else 0
                        decision_data.append({
                            "Decision": decision.upper() if decision else "HOLD",
                            "Count": count,
                            "Percentage": f"{pct:.1f}%",
                            "Avg Confidence": f"{avg_conf:.2f}" if avg_conf else "N/A"
                        })
                    
                    df_decisions = pd.DataFrame(decision_data)
                    st.dataframe(df_decisions, use_container_width=True, hide_index=True)
                    
                    # Create pie chart
                    fig = go.Figure(data=[go.Pie(
                        labels=[d["Decision"] for d in decision_data],
                        values=[d["Count"] for d in decision_data],
                        marker=dict(colors=['#2fbf8f', '#f7b267', '#e63946']),
                        hole=0.4
                    )])
                    fig.update_layout(
                        height=250,
                        margin=dict(l=20, r=20, t=10, b=10),
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No AI decisions in the last 24 hours")
            
            with col2:
                st.markdown("### 📊 Technical Signals (1h)")
                if recent_analysis:
                    # Count signals
                    signal_counts = {}
                    for row in recent_analysis:
                        signal = row[1] if row[1] else 'HOLD'
                        signal_counts[signal] = signal_counts.get(signal, 0) + 1
                    
                    total_signals = sum(signal_counts.values())
                    signal_data = []
                    for signal, count in signal_counts.items():
                        pct = (count / total_signals * 100) if total_signals > 0 else 0
                        signal_data.append({
                            "Signal": signal.upper(),
                            "Count": count,
                            "Percentage": f"{pct:.1f}%"
                        })
                    
                    df_signals = pd.DataFrame(signal_data)
                    st.dataframe(df_signals, use_container_width=True, hide_index=True)
                    
                    # Trend analysis
                    bullish = sum(1 for row in recent_analysis if row[3])  # trend_bullish
                    bearish = sum(1 for row in recent_analysis if row[4])  # trend_bearish
                    neutral = len(recent_analysis) - bullish - bearish
                    
                    st.markdown("#### Market Sentiment")
                    st.write(f"🟢 Bullish: {bullish} ({bullish/len(recent_analysis)*100:.1f}%)")
                    st.write(f"🔴 Bearish: {bearish} ({bearish/len(recent_analysis)*100:.1f}%)")
                    st.write(f"⚪ Neutral: {neutral} ({neutral/len(recent_analysis)*100:.1f}%)")
                else:
                    st.info("No technical analysis in the last hour")
            
            # Recent analysis table
            st.markdown("---")
            st.markdown("### 📈 Recent Analysis (Last Hour)")
            
            if recent_analysis:
                analysis_data = []
                for row in recent_analysis:
                    symbol, signal, rsi, bullish, bearish, timestamp = row
                    
                    trend = "🟢 Bullish" if bullish else "🔴 Bearish" if bearish else "⚪ Neutral"
                    
                    analysis_data.append({
                        "Time": datetime.fromisoformat(timestamp).strftime("%H:%M:%S"),
                        "Symbol": symbol,
                        "Signal": signal.upper() if signal else "HOLD",
                        "RSI": f"{rsi:.1f}" if rsi else "N/A",
                        "Trend": trend
                    })
                
                df_analysis = pd.DataFrame(analysis_data)
                st.dataframe(df_analysis, use_container_width=True, hide_index=True, height=300)
            else:
                st.info("No analysis data available")
                
        except Exception as e:
            st.warning(f"Could not load analysis data: {e}")
            logger.error(f"Analysis query error: {e}", exc_info=True)
            
    except Exception as exc:
        st.error(f"Error in analysis tab: {exc}")
        logger.error(f"Analysis tab error: {exc}", exc_info=True)


def render_settings_tab() -> None:
    """Settings and configuration."""
    section_header("Configuration")
    config = _get_config()

    tab1, tab2, tab3 = st.tabs(["Trading", "Risk", "System"])
    with tab1:
        st.markdown("#### Trading")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox(
                "Trading mode",
                ["PAPER", "LIVE"],
                index=0 if config.trading.mode == "PAPER" else 1,
            )
        with col2:
            st.number_input(
                "Max concurrent positions",
                min_value=1,
                max_value=200,
                value=min(config.trading.default_max_positions, 200),
            )

    with tab2:
        st.markdown("#### Risk limits")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.slider("Risk per trade (%)", 0.1, 5.0, 1.0, 0.1)
        with col2:
            st.slider("Daily loss limit (%)", 1.0, 10.0, 3.0, 0.5)
        with col3:
            st.slider("Max drawdown (%)", 5.0, 30.0, 10.0, 1.0)

    with tab3:
        st.markdown("#### System status")
        st.write(f"Mode: {config.trading.mode}")
        st.write("Streamlit: active")


def render_account_tab() -> None:
    """Detailed account information from MT5."""
    section_header("Account details")
    
    try:
        mt5_client = get_mt5_client()
        account_info = mt5_client.get_account_info()
        
        if not account_info:
            st.warning("Could not retrieve account information from MT5")
            return
        
        # Account overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("### 💰 Balance")
            balance = account_info.get('balance', 0)
            st.markdown(f"#### ${balance:,.2f}")
            st.caption("Account balance")
        
        with col2:
            st.markdown("### 📊 Equity")
            equity = account_info.get('equity', 0)
            st.markdown(f"#### ${equity:,.2f}")
            st.caption("Balance + floating P&L")
        
        with col3:
            st.markdown("### 📈 Profit")
            profit = account_info.get('profit', 0)
            profit_color = "green" if profit >= 0 else "red"
            st.markdown(f"#### :{profit_color}[${profit:,.2f}]")
            st.caption("Unrealized P&L")
        
        with col4:
            st.markdown("### 💳 Free Margin")
            margin_free = account_info.get('margin_free', 0)
            st.markdown(f"#### ${margin_free:,.2f}")
            st.caption("Available for trading")
        
        st.markdown("---")
        
        # Detailed metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Account Information")
            st.write(f"**Login:** {account_info.get('login', 'N/A')}")
            st.write(f"**Server:** {account_info.get('server', 'N/A')}")
            st.write(f"**Name:** {account_info.get('name', 'N/A')}")
            st.write(f"**Company:** {account_info.get('company', 'N/A')}")
            st.write(f"**Currency:** {account_info.get('currency', 'USD')}")
            st.write(f"**Leverage:** 1:{account_info.get('leverage', 0)}")
        
        with col2:
            st.markdown("#### Margin Information")
            margin = account_info.get('margin', 0)
            margin_level = account_info.get('margin_level', 0)
            margin_so_call = account_info.get('margin_so_call', 0)
            margin_so_so = account_info.get('margin_so_so', 0)
            
            st.write(f"**Margin Used:** ${margin:,.2f}")
            st.write(f"**Margin Level:** {margin_level:.2f}%")
            st.write(f"**Margin Call:** {margin_so_call:.0f}%")
            st.write(f"**Stop Out:** {margin_so_so:.0f}%")
            
            # Margin health indicator
            if margin_level >= 200:
                st.success("✅ Healthy margin level")
            elif margin_level >= 100:
                st.warning("⚠️ Moderate margin usage")
            else:
                st.error("🚨 Critical margin level!")
        
        with col3:
            st.markdown("#### Trading Limits")
            st.write(f"**Limit Orders:** {account_info.get('limit_orders', 'N/A')}")
            st.write(f"**Trade Allowed:** {'✅ Yes' if account_info.get('trade_allowed', False) else '❌ No'}")
            st.write(f"**Trade Expert:** {'✅ Yes' if account_info.get('trade_expert', False) else '❌ No'}")
            
            # Credit/bonus
            credit = account_info.get('credit', 0)
            if credit > 0:
                st.write(f"**Credit/Bonus:** ${credit:,.2f}")
        
        st.markdown("---")
        
        # Historical performance from database
        st.markdown("### 📊 Historical Performance")
        
        db = _get_db()
        stats_7d = db.get_performance_summary(days=7)
        stats_30d = db.get_performance_summary(days=30)
        stats_90d = db.get_performance_summary(days=90)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Last 7 Days")
            st.metric("Net P&L", f"${stats_7d.get('net_profit', 0):.2f}")
            st.metric("Trades", stats_7d.get('total_trades', 0))
            st.metric("Win Rate", f"{stats_7d.get('win_rate', 0):.1f}%")
        
        with col2:
            st.markdown("#### Last 30 Days")
            st.metric("Net P&L", f"${stats_30d.get('net_profit', 0):.2f}")
            st.metric("Trades", stats_30d.get('total_trades', 0))
            st.metric("Win Rate", f"{stats_30d.get('win_rate', 0):.1f}%")
        
        with col3:
            st.markdown("#### Last 90 Days")
            st.metric("Net P&L", f"${stats_90d.get('net_profit', 0):.2f}")
            st.metric("Trades", stats_90d.get('total_trades', 0))
            st.metric("Win Rate", f"{stats_90d.get('win_rate', 0):.1f}%")
        
    except Exception as exc:
        st.error(f"Error loading account information: {exc}")
        logger.error(f"Account tab error: {exc}", exc_info=True)


def render_logs_tab() -> None:
    """Activity and logs view with enhanced filtering."""
    section_header("Trading activity feed")
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        days_filter = st.selectbox("Time range", [1, 3, 7, 14, 30], index=2)
    with col2:
        symbol_filter = st.text_input("Filter by symbol (optional)").strip().upper()
    with col3:
        status_filter = st.selectbox("Status", ["All", "OPEN", "CLOSED"], index=0)
    
    db = _get_db()
    trades = db.get_trades(days=days_filter)
    
    if not trades:
        empty_state("No recent trades", f"No trades recorded in the last {days_filter} days.")
        return
    
    df = pd.DataFrame(trades)
    
    # Apply filters
    if symbol_filter:
        df = df[df['symbol'].str.contains(symbol_filter, case=False, na=False)]
    
    if status_filter != "All":
        df = df[df['status'] == status_filter]
    
    if df.empty:
        st.info("No trades match your filters")
        return
    
    # Convert timestamps
    df["open_timestamp"] = pd.to_datetime(df["open_timestamp"])
    if "close_timestamp" in df.columns:
        df["close_timestamp"] = pd.to_datetime(df["close_timestamp"])
    
    # Sort by most recent
    df = df.sort_values("open_timestamp", ascending=False)
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", len(df))
    with col2:
        open_trades = len(df[df['status'] == 'OPEN'])
        st.metric("Open", open_trades)
    with col3:
        closed_trades = len(df[df['status'] == 'CLOSED'])
        st.metric("Closed", closed_trades)
    with col4:
        total_profit = df['profit'].sum() if 'profit' in df.columns else 0
        st.metric("Total P&L", f"${total_profit:.2f}")
    
    st.markdown("---")
    
    # Format display columns
    display_columns = ["open_timestamp", "symbol", "type", "volume", "open_price"]
    
    if "close_price" in df.columns:
        display_columns.append("close_price")
    if "profit" in df.columns:
        display_columns.append("profit")
    if "status" in df.columns:
        display_columns.append("status")
    if "ticket" in df.columns:
        display_columns.insert(0, "ticket")
    
    # Limit columns that exist
    display_columns = [col for col in display_columns if col in df.columns]
    
    # Show dataframe with enhanced formatting
    st.dataframe(
        df[display_columns].head(100),
        use_container_width=True,
        hide_index=True,
        column_config={
            "open_timestamp": st.column_config.DatetimeColumn(
                "Open Time",
                format="YYYY-MM-DD HH:mm:ss"
            ),
            "close_timestamp": st.column_config.DatetimeColumn(
                "Close Time",
                format="YYYY-MM-DD HH:mm:ss"
            ),
            "profit": st.column_config.NumberColumn(
                "Profit",
                format="$%.2f"
            ),
            "type": st.column_config.TextColumn(
                "Type"
            ),
        }
    )
    
    # Export option
    csv = df[display_columns].to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download filtered data (CSV)",
        data=csv,
        file_name=f"trading_activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def _statement_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive trading metrics from dataframe"""
    if df.empty:
        return {
            "net": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
    
    net = df["net_pnl"].sum()
    wins = df[df["net_pnl"] > 0]
    losses = df[df["net_pnl"] < 0]
    breakeven = df[df["net_pnl"] == 0]
    
    total_trades = len(df)
    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(breakeven)
    
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
    
    # Gross profit/loss
    gross_profit = wins["net_pnl"].sum() if not wins.empty else 0.0
    gross_loss = abs(losses["net_pnl"].sum()) if not losses.empty else 0.0
    
    # Profit factor (gross profit / gross loss)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (1.0 if gross_profit > 0 else 0.0)
    
    # Average per winning/losing trade (should be negative for losses)
    avg_win = wins["net_pnl"].mean() if not wins.empty else 0.0
    avg_loss = losses["net_pnl"].mean() if not losses.empty else 0.0  # This is already negative
    
    # Best and worst trades
    best_trade = df["net_pnl"].max() if not df.empty else 0.0
    worst_trade = df["net_pnl"].min() if not df.empty else 0.0
    
    # Ratio metrics
    if not wins.empty and not losses.empty:
        ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
    else:
        ratio = 0.0
    
    return {
        "net": net,
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "be_count": be_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": abs(avg_loss) if avg_loss != 0 else 0.0,  # Display as positive loss amount
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "ratio": ratio,
    }


def render_statement_tab() -> None:
    """Account statement based on historical closed trades."""
    section_header("Account statement", "Historical closed trades")

    col1, col2, col3 = st.columns(3)
    with col1:
        range_key = st.selectbox("Range", ["7d", "30d", "90d", "365d", "Custom"])
    with col2:
        symbol_filter = st.text_input("Symbol filter (optional)").strip().upper()
    with col3:
        include_commission = st.toggle("Net after commission", value=True)

    end_date = datetime.now()
    if range_key == "Custom":
        date_range = st.date_input(
            "Start and end",
            value=(end_date.date() - timedelta(days=30), end_date.date()),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date = datetime.combine(date_range[0], datetime.min.time())
            end_date = datetime.combine(date_range[1], datetime.max.time())
        else:
            start_date = end_date - timedelta(days=30)
    else:
        days = int(range_key.replace("d", ""))
        start_date = end_date - timedelta(days=days)

    db = _get_db()
    trades = db.get_closed_trades(start_date, end_date, symbol_filter or None)
    df = pd.DataFrame(trades)
    if df.empty:
        empty_state(
            "No closed trades",
            "No closed trades in the selected range. Ensure data/trading_history.db is populated.",
        )
        return

    df["open_timestamp"] = pd.to_datetime(df["open_timestamp"])
    df["close_timestamp"] = pd.to_datetime(df["close_timestamp"])
    
    # Calculate profit correctly from entry/exit
    df["open_price"] = pd.to_numeric(df["open_price"], errors='coerce').fillna(0)
    df["close_price"] = pd.to_numeric(df["close_price"], errors='coerce').fillna(0)
    df["volume"] = pd.to_numeric(df["volume"], errors='coerce').fillna(0)
    df["type"] = pd.to_numeric(df["type"], errors='coerce').fillna(0)
    
    # If profit not in DB, calculate it
    df["profit"] = pd.to_numeric(df["profit"], errors='coerce').fillna(0)
    
    # Recalculate if missing/zero and we have price data
    mask = df["profit"] == 0
    for idx, row in df[mask].iterrows():
        if row["open_price"] > 0 and row["close_price"] > 0:
            if row["type"] == 0:  # BUY
                calculated_profit = (row["close_price"] - row["open_price"]) * row["volume"]
            else:  # SELL
                calculated_profit = (row["open_price"] - row["close_price"]) * row["volume"]
            df.at[idx, "profit"] = calculated_profit
    
    df["commission"] = pd.to_numeric(df["commission"], errors='coerce').fillna(0)
    df["swap"] = pd.to_numeric(df["swap"], errors='coerce').fillna(0)
    
    df["gross_pnl"] = df["profit"]
    
    if include_commission:
        df["net_pnl"] = df["gross_pnl"] - df["commission"] - df["swap"]
    else:
        df["net_pnl"] = df["gross_pnl"]

    df = df.sort_values("close_timestamp")
    df["cumulative_pnl"] = df["net_pnl"].cumsum()
    df["close_date"] = df["close_timestamp"].dt.date

    metrics = _statement_metrics(df)
    
    # Display main metrics with better layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Net PnL", f"${metrics['net']:,.2f}", 
                 delta="✅ Profitable" if metrics['net'] > 0 else "❌ Loss" if metrics['net'] < 0 else "Breakeven")
    with col2:
        st.metric("📊 Total Trades", metrics["total_trades"],
                 delta=f"{metrics['win_count']}W/{metrics['loss_count']}L/{metrics['be_count']}BE")
    with col3:
        st.metric("📈 Win Rate", f"{metrics['win_rate']:.1f}%",
                 delta=f"{metrics['win_count']} wins" if metrics['win_count'] > 0 else "No wins")
    with col4:
        st.metric("🎯 Profit Factor", f"{metrics['profit_factor']:.2f}",
                 delta="Above 1.0 is profitable" if metrics['profit_factor'] >= 1.0 else "Below 1.0 is loss")
    
    st.markdown("---")
    
    # Secondary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📍 Avg Win", f"${metrics['avg_win']:,.2f}",
                 help="Average profit per winning trade")
    with col2:
        st.metric("📍 Avg Loss", f"${metrics['avg_loss']:,.2f}",
                 help="Average loss per losing trade (shown as positive)")
    with col3:
        st.metric("🏆 Best Trade", f"${metrics['best_trade']:,.2f}",
                 help="Largest single trade profit")
    with col4:
        st.metric("🔻 Worst Trade", f"${metrics['worst_trade']:,.2f}",
                 help="Largest single trade loss")

    section_header("Equity curve")
    st.plotly_chart(_plot_equity_curve(df), use_container_width=True)

    section_header("Daily summary")
    daily = (
        df.groupby("close_date")
        .agg(
            trades=("id", "count"),
            gross=("gross_pnl", "sum"),
            net=("net_pnl", "sum"),
        )
        .reset_index()
    )
    st.dataframe(daily, use_container_width=True, hide_index=True)

    section_header("Statement details")
    statement = df[
        [
            "close_timestamp",
            "ticket",
            "symbol",
            "type",
            "volume",
            "open_price",
            "close_price",
            "gross_pnl",
            "commission",
            "swap",
            "net_pnl",
        ]
    ].rename(
        columns={
            "close_timestamp": "close_time",
            "open_price": "entry",
            "close_price": "exit",
            "gross_pnl": "gross",
            "net_pnl": "net",
        }
    )
    st.dataframe(statement, use_container_width=True, hide_index=True)

    csv = statement.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download statement (CSV)",
        data=csv,
        file_name="account_statement.csv",
        mime="text/csv",
    )
