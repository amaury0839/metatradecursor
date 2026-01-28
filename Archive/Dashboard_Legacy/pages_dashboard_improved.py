"""Improved Dashboard - Modern, Clean Design"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import defaultdict

# Try to import local modules
try:
    from app.trading.mt5_client import get_mt5_client
    from app.trading.portfolio import get_portfolio_manager
    from app.core.state import get_state_manager
    from app.core.config import get_config
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def calculate_win_rate(positions_history):
    """Calculate actual win rate from closed positions"""
    if not positions_history:
        return 0.0, 0, 0
    
    winners = sum(1 for p in positions_history if p.get('profit', 0) > 0)
    losers = sum(1 for p in positions_history if p.get('profit', 0) < 0)
    total = len(positions_history)
    
    if total == 0:
        return 0.0, 0, 0
    
    win_rate = (winners / total) * 100 if total > 0 else 0
    return win_rate, winners, losers


def calculate_profit_factor(positions_history):
    """Calculate profit factor (gross profit / gross loss)"""
    if not positions_history:
        return 0.0
    
    gross_profit = sum(p.get('profit', 0) for p in positions_history if p.get('profit', 0) > 0)
    gross_loss = abs(sum(p.get('profit', 0) for p in positions_history if p.get('profit', 0) < 0))
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    
    return gross_profit / gross_loss if gross_loss > 0 else 0.0


def render_dashboard():
    """Render modern dashboard"""
    if LOCAL_MODE:
        render_dashboard_local()
    else:
        st.error("Local mode required for dashboard")


def render_dashboard_local():
    """Render dashboard - Local mode"""
    mt5 = get_mt5_client()
    portfolio = get_portfolio_manager()
    state = get_state_manager()
    config = get_config()
    
    # Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>📊 Trading Dashboard</h1>
        <p style='color: rgba(255,255,255,0.8); margin: 5px 0 0 0;'>Real-time Portfolio & Performance Metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Account Info
    account_info = mt5.get_account_info()
    if account_info:
        col1, col2, col3, col4 = st.columns(4)
        
        balance = account_info.get('balance', 0)
        equity = account_info.get('equity', 0)
        unrealized = equity - balance
        
        with col1:
            st.metric(
                "💵 Balance",
                f"${balance:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "📈 Equity",
                f"${equity:,.2f}",
                delta=f"${unrealized:+,.2f}" if unrealized != 0 else "Neutral"
            )
        
        with col3:
            open_positions = portfolio.get_open_positions_count()
            st.metric(
                "🔓 Open Positions",
                open_positions,
                delta=None
            )
        
        with col4:
            margin_used = account_info.get('margin', 0)
            margin_available = account_info.get('margin_free', 0)
            margin_level = ((margin_available + margin_used) / margin_used * 100) if margin_used > 0 else 0
            st.metric(
                "📊 Margin Level",
                f"{margin_level:.0f}%",
                delta="Safe" if margin_level > 200 else ("Warning" if margin_level > 100 else "Critical")
            )
    
    st.divider()
    
    # Performance Metrics
    st.subheader("📈 Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    # Get recent trades for metrics (limited data available locally)
    closed_positions = state.get_recent_trades(limit=50) or []
    win_rate, winners, losers = calculate_win_rate(closed_positions)
    profit_factor = calculate_profit_factor(closed_positions)
    
    with col1:
        st.metric(
            "🎯 Win Rate",
            f"{win_rate:.1f}%" if closed_positions else "N/A",
            delta=f"{winners}W / {losers}L" if closed_positions else None
        )
    
    with col2:
        st.metric(
            "💹 Profit Factor",
            f"{profit_factor:.2f}" if closed_positions else "N/A",
            delta="Good" if profit_factor > 1.5 else ("Fair" if profit_factor > 1.0 else "Poor")
        )
    
    with col3:
        avg_win = (sum(p.get('profit', 0) for p in closed_positions if p.get('profit', 0) > 0) / winners) if winners > 0 else 0
        st.metric(
            "🏆 Avg Win",
            f"${avg_win:,.2f}" if closed_positions else "N/A"
        )
    
    with col4:
        avg_loss = (sum(p.get('profit', 0) for p in closed_positions if p.get('profit', 0) < 0) / losers) if losers > 0 else 0
        st.metric(
            "💔 Avg Loss",
            f"${avg_loss:,.2f}" if closed_positions else "N/A"
        )
    
    st.divider()
    
    # Open Positions - Detailed View
    st.subheader("🔓 Open Positions")
    positions = portfolio.get_open_positions()
    
    if positions:
        # Summary cards
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        total_exposure = sum(p.get('volume', 0) for p in positions)
        total_pnl = sum(p.get('profit', 0) for p in positions)
        winning_positions = sum(1 for p in positions if p.get('profit', 0) > 0)
        
        with summary_col1:
            st.metric("Total Volume", f"{total_exposure:.2f} lots")
        with summary_col2:
            st.metric("Total P&L", f"${total_pnl:+,.2f}", delta=f"{(total_pnl/account_info.get('balance', 1)*100):+.2f}%")
        with summary_col3:
            st.metric("Winning Positions", f"{winning_positions}/{len(positions)}")
        
        # Positions table
        position_data = []
        for pos in positions:
            pnl = pos.get('profit', 0)
            pnl_pct = ((pos.get('price_current', 0) - pos.get('price_open', 0)) / pos.get('price_open', 1) * 100) if pos.get('price_open', 0) > 0 else 0
            
            position_data.append({
                "Symbol": pos.get('symbol', ''),
                "Type": "🟢 BUY" if pos.get('type', 0) == 0 else "🔴 SELL",
                "Volume": f"{pos.get('volume', 0):.2f}",
                "Entry": f"{pos.get('price_open', 0):.5f}",
                "Current": f"{pos.get('price_current', 0):.5f}",
                "P&L": f"${pnl:+,.2f}",
                "P&L %": f"{pnl_pct:+.2f}%",
                "SL": f"{pos.get('sl', 0):.5f}" if pos.get('sl', 0) > 0 else "None",
                "TP": f"{pos.get('tp', 0):.5f}" if pos.get('tp', 0) > 0 else "None",
            })
        
        st.dataframe(position_data, use_container_width=True)
    else:
        st.info("📭 No open positions - market might be closed or no signals generated")
    
    st.divider()
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    # PnL by Symbol
    with col_chart1:
        st.subheader("💰 P&L by Symbol")
        pnl_by_symbol = portfolio.get_unrealized_pnl_by_symbol()
        
        if pnl_by_symbol:
            symbols = list(pnl_by_symbol.keys())
            pnls = list(pnl_by_symbol.values())
            
            fig = go.Figure(data=[
                go.Bar(
                    x=symbols,
                    y=pnls,
                    marker_color=['#2ecc71' if p > 0 else '#e74c3c' for p in pnls],
                    text=[f'${p:.2f}' for p in pnls],
                    textposition='auto',
                )
            ])
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Symbol",
                yaxis_title="P&L ($)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No P&L data")
    
    # Win/Loss Distribution
    with col_chart2:
        st.subheader("📊 Win/Loss Distribution")
        if closed_positions and (winners > 0 or losers > 0):
            fig = go.Figure(data=[
                go.Pie(
                    labels=['Wins', 'Losses'],
                    values=[winners, losers],
                    marker_colors=['#2ecc71', '#e74c3c'],
                    hole=0.3,
                    textinfo='label+percent+value',
                )
            ])
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No closed positions yet")
    
    st.divider()
    
    # Recent Decisions
    st.subheader("🎯 Recent Trading Signals")
    decisions = state.get_recent_decisions(limit=10)
    
    if decisions:
        decision_data = []
        for dec in decisions:
            decision_data.append({
                "Time": dec.get('timestamp', '')[:16] if dec.get('timestamp') else '',
                "Symbol": dec.get('symbol', ''),
                "Signal": dec.get('signal', ''),
                "Action": dec.get('action', ''),
                "Confidence": f"{dec.get('confidence', 0):.0%}",
                "Executed": "✅" if dec.get('execution_success') else "❌",
            })
        
        st.dataframe(decision_data, use_container_width=True, hide_index=True)
    else:
        st.info("No decisions yet")
