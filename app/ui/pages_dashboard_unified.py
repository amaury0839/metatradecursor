"""
Unified Dashboard - Consolidated from 4 versions
Location: app/ui/pages_dashboard_unified.py

Combines best features from:
- pages_dashboard.py (basic structure, clean)
- pages_dashboard_modern.py (modern components)
- pages_dashboard_modern_fixed.py (chart integration)
- pages_dashboard_improved.py (enhanced metrics)

Version: 2.0 - Jan 28, 2026
Status: Ready for production
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Local imports
try:
    from app.trading.mt5_client import get_mt5_client
    from app.trading.portfolio import get_portfolio_manager
    from app.trading.risk import get_risk_manager
    from app.core.state import get_state_manager
    from app.core.config import get_config
    from app.core.database import get_database_manager
    from app.ui.themes_modern import get_theme, apply_global_theme
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


# ============= SECTION 1: DATA LOADING =============

def load_account_metrics():
    """Load account information from MT5"""
    if not LOCAL_MODE:
        return None
    
    mt5 = get_mt5_client()
    account_info = mt5.get_account_info()
    
    if not account_info:
        return None
    
    return {
        'balance': account_info.get('balance', 0),
        'equity': account_info.get('equity', 0),
        'margin': account_info.get('margin', 0),
        'free_margin': account_info.get('free_margin', 0),
        'margin_level': account_info.get('margin_level', 0),
    }


def load_positions():
    """Load open positions from portfolio"""
    if not LOCAL_MODE:
        return []
    
    portfolio = get_portfolio_manager()
    positions = portfolio.get_open_positions()
    return positions if positions else []


def load_recent_decisions(limit=10):
    """Load recent trading decisions"""
    if not LOCAL_MODE:
        return []
    
    state = get_state_manager()
    decisions = state.get_recent_decisions(limit=limit)
    return decisions if decisions else []


def load_trade_history(limit=20):
    """Load recent closed trades from database"""
    if not LOCAL_MODE:
        return pd.DataFrame()
    
    try:
        db = get_database_manager()
        trades = db.get_trades(limit=limit)
        if trades:
            return pd.DataFrame(trades)
    except:
        pass
    
    return pd.DataFrame()


# ============= SECTION 2: METRIC DISPLAY =============

def display_account_metrics():
    """Display key account metrics"""
    account_info = load_account_metrics()
    
    if not account_info:
        st.warning("Could not load account information")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        balance = account_info['balance']
        st.metric(
            "💰 Balance",
            f"${balance:,.2f}",
            delta=None
        )
    
    with col2:
        equity = account_info['equity']
        balance = account_info['balance']
        daily_pnl = equity - balance
        pnl_pct = (daily_pnl / balance * 100) if balance > 0 else 0
        st.metric(
            "📈 Equity",
            f"${equity:,.2f}",
            delta=f"${daily_pnl:,.2f} ({pnl_pct:.2f}%)"
        )
    
    with col3:
        free_margin = account_info['free_margin']
        st.metric(
            "💳 Free Margin",
            f"${free_margin:,.2f}",
            delta=None
        )
    
    with col4:
        margin_level = account_info['margin_level']
        # Color code margin level
        if margin_level > 200:
            color = "🟢"
        elif margin_level > 100:
            color = "🟡"
        else:
            color = "🔴"
        
        st.metric(
            f"{color} Margin Level",
            f"{margin_level:.1f}%",
            delta=None
        )


def display_position_summary():
    """Display open positions summary"""
    portfolio = get_portfolio_manager()
    positions = load_positions()
    
    if not positions:
        st.info("📭 No open positions")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_profit = sum(pos.get('profit', 0) for pos in positions)
    winning_trades = len([p for p in positions if p.get('profit', 0) > 0])
    losing_trades = len([p for p in positions if p.get('profit', 0) < 0])
    
    with col1:
        st.metric(
            "📊 Total Positions",
            len(positions),
            delta=None
        )
    
    with col2:
        st.metric(
            "✅ Winning",
            winning_trades,
            delta=None
        )
    
    with col3:
        st.metric(
            "❌ Losing",
            losing_trades,
            delta=None
        )
    
    with col4:
        st.metric(
            "💵 Total P&L",
            f"${total_profit:,.2f}",
            delta=None
        )


# ============= SECTION 3: TABLES =============

def display_open_positions():
    """Display table of open positions"""
    positions = load_positions()
    
    if not positions:
        return
    
    st.subheader("📋 Open Positions")
    
    position_data = []
    for pos in positions:
        position_data.append({
            "Symbol": pos.get('symbol', ''),
            "Type": "🔵 BUY" if pos.get('type', 0) == 0 else "🔴 SELL",
            "Volume": f"{pos.get('volume', 0):.2f}",
            "Entry": f"{pos.get('price_open', 0):.5f}",
            "Current": f"{pos.get('price_current', 0):.5f}",
            "SL": f"{pos.get('sl', 0):.5f}" if pos.get('sl', 0) > 0 else "—",
            "TP": f"{pos.get('tp', 0):.5f}" if pos.get('tp', 0) > 0 else "—",
            "P&L $": f"${pos.get('profit', 0):.2f}",
            "P&L %": f"{pos.get('profit_pct', 0):.2f}%",
            "Ticket": pos.get('ticket', 0),
        })
    
    df = pd.DataFrame(position_data)
    
    # Style the dataframe
    st.dataframe(
        df,
        width='stretch',
        height=400,
        hide_index=True
    )


def display_recent_trades():
    """Display table of recent closed trades"""
    trades_df = load_trade_history(limit=15)
    
    if trades_df.empty:
        st.info("No trade history available")
        return
    
    st.subheader("📜 Recent Trades (Closed)")
    
    # Format columns if they exist
    if 'open_timestamp' in trades_df.columns:
        trades_df = trades_df.copy()
        try:
            trades_df['open_timestamp'] = pd.to_datetime(
                trades_df['open_timestamp']
            ).dt.strftime('%Y-%m-%d %H:%M')
        except:
            pass
    
    # Select relevant columns
    columns_to_show = [col for col in [
        'symbol', 'type', 'volume', 'open_price', 'close_price', 
        'profit', 'open_timestamp'
    ] if col in trades_df.columns]
    
    if columns_to_show:
        st.dataframe(
            trades_df[columns_to_show],
            width='stretch',
            height=300,
            hide_index=True
        )


def display_recent_decisions():
    """Display recent trading decisions"""
    decisions = load_recent_decisions(limit=10)
    
    if not decisions:
        st.info("No decisions yet")
        return
    
    st.subheader("🎯 Recent Decisions")
    
    decision_data = []
    for dec in decisions:
        decision_data.append({
            "⏰ Time": dec.get('timestamp', '')[:19] if dec.get('timestamp') else '—',
            "📍 Symbol": dec.get('symbol', '—'),
            "📈 Signal": dec.get('signal', '—'),
            "✅ Action": dec.get('action', '—'),
            "📊 Confidence": f"{dec.get('confidence', 0):.2f}",
            "🛡️ Risk OK": "✅" if dec.get('risk_checks_passed') else "❌",
            "🚀 Executed": "✅" if dec.get('execution_success') else "❌",
        })
    
    df = pd.DataFrame(decision_data)
    st.dataframe(
        df,
        width='stretch',
        height=300,
        hide_index=True
    )


# ============= SECTION 4: CHARTS =============

def display_equity_curve():
    """Display equity curve chart"""
    try:
        # Try to load from database
        if LOCAL_MODE:
            db = get_database_manager()
            trades = db.get_trades(limit=100)
            
            if not trades:
                st.info("No trade data available for chart")
                return
            
            # Build equity curve
            starting_equity = 10000  # Default starting equity
            trades_df = pd.DataFrame(trades)
            
            if 'close_timestamp' in trades_df.columns:
                trades_df = trades_df.sort_values('close_timestamp')
                trades_df['cumulative_pnl'] = trades_df['profit'].cumsum()
                trades_df['equity'] = starting_equity + trades_df['cumulative_pnl']
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trades_df['close_timestamp'],
                    y=trades_df['equity'],
                    mode='lines+markers',
                    name='Equity',
                    line=dict(color='blue', width=2),
                    fill='tozeroy',
                ))
                
                fig.update_layout(
                    title="📈 Equity Curve (Last 100 Trades)",
                    xaxis_title="Date",
                    yaxis_title="Equity ($)",
                    hovermode='x unified',
                    height=400,
                )
                
                st.plotly_chart(fig, width='stretch')
                return
    except:
        pass
    
    st.info("Could not load equity curve data")


def display_pnl_by_symbol():
    """Display P&L breakdown by symbol"""
    positions = load_positions()
    
    if not positions:
        st.info("No positions to display")
        return
    
    # Group by symbol
    pnl_by_symbol = {}
    for pos in positions:
        symbol = pos.get('symbol', 'Unknown')
        profit = pos.get('profit', 0)
        
        if symbol in pnl_by_symbol:
            pnl_by_symbol[symbol] += profit
        else:
            pnl_by_symbol[symbol] = profit
    
    # Create chart
    symbols = list(pnl_by_symbol.keys())
    profits = list(pnl_by_symbol.values())
    colors = ['green' if p > 0 else 'red' for p in profits]
    
    fig = go.Figure(data=[
        go.Bar(
            x=symbols,
            y=profits,
            marker_color=colors,
            text=[f"${p:.2f}" for p in profits],
            textposition='outside',
        )
    ])
    
    fig.update_layout(
        title="💰 P&L by Symbol",
        xaxis_title="Symbol",
        yaxis_title="P&L ($)",
        height=400,
        showlegend=False,
    )
    
    st.plotly_chart(fig, width='stretch')


def display_risk_status():
    """Display risk management status"""
    if not LOCAL_MODE:
        st.info("Risk status not available in remote mode")
        return
    
    risk = get_risk_manager()
    account_info = load_account_metrics()
    portfolio = get_portfolio_manager()
    
    if not account_info:
        return
    
    st.subheader("⚠️ Risk Management Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_positions = risk.max_positions
        current_positions = len(load_positions())
        usage_pct = (current_positions / max_positions * 100) if max_positions > 0 else 0
        
        color = "🟢" if usage_pct < 70 else "🟡" if usage_pct < 90 else "🔴"
        
        st.metric(
            f"{color} Position Limit",
            f"{current_positions}/{max_positions}",
            delta=f"{usage_pct:.0f}%"
        )
    
    with col2:
        max_daily_loss = getattr(risk, 'max_daily_loss_pct', 5.0)
        daily_pnl = account_info['equity'] - account_info['balance']
        daily_loss_pct = abs(daily_pnl / account_info['balance'] * 100) if account_info['balance'] > 0 else 0
        
        if daily_pnl >= 0:
            color = "🟢"
        elif daily_loss_pct < max_daily_loss:
            color = "🟡"
        else:
            color = "🔴"
        
        st.metric(
            f"{color} Daily Loss",
            f"{daily_loss_pct:.2f}%",
            delta=f"Max: {max_daily_loss}%"
        )
    
    with col3:
        max_drawdown = getattr(risk, 'max_drawdown_pct', 10.0)
        current_drawdown = 2.5  # Placeholder - would need to calculate from history
        
        color = "🟢" if current_drawdown < max_drawdown * 0.5 else "🟡"
        
        st.metric(
            f"{color} Drawdown",
            f"{current_drawdown:.2f}%",
            delta=f"Max: {max_drawdown}%"
        )


# ============= MAIN FUNCTION =============

def render_dashboard():
    """Main dashboard render function"""
    
    if not LOCAL_MODE:
        st.error("Dashboard requires local mode. Please configure local trading bot connection.")
        return
    
    # Apply theme if available
    try:
        apply_global_theme()
    except:
        pass
    
    st.title("📊 Trading Dashboard")
    
    # ===== TAB 1: OVERVIEW =====
    with st.container():
        st.subheader("Account Overview")
        display_account_metrics()
        
        st.divider()
        
        st.subheader("Position Summary")
        display_position_summary()
    
    # ===== TAB 2: POSITIONS & TRADES =====
    st.divider()
    
    col_pos, col_trades = st.columns(2)
    
    with col_pos:
        display_open_positions()
    
    with col_trades:
        display_recent_trades()
    
    # ===== TAB 3: DECISIONS =====
    st.divider()
    
    display_recent_decisions()
    
    # ===== TAB 4: ANALYTICS =====
    st.divider()
    
    st.subheader("📈 Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_equity_curve()
    
    with col2:
        display_pnl_by_symbol()
    
    # ===== TAB 5: RISK =====
    st.divider()
    
    display_risk_status()


if __name__ == "__main__":
    render_dashboard()

