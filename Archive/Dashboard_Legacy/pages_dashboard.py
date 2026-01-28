"""Dashboard page - Works for both local and remote modes"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Try to import local modules (for local mode)
try:
    from app.trading.mt5_client import get_mt5_client
    from app.trading.portfolio import get_portfolio_manager
    from app.core.state import get_state_manager
    from app.core.config import get_config
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def render_dashboard():
    """Render dashboard page - auto-detects local or remote mode"""
    if LOCAL_MODE:
        render_dashboard_local()
    else:
        # Remote mode - use API client
        if "api_client" in st.session_state:
            render_dashboard_remote(st.session_state.api_client)
        else:
            st.error("API client not available. Please configure connection.")


def render_dashboard_local():
    """Render dashboard page - Local mode"""
    mt5 = get_mt5_client()
    portfolio = get_portfolio_manager()
    state = get_state_manager()
    config = get_config()
    
    # Account metrics
    col1, col2, col3, col4 = st.columns(4)
    
    account_info = mt5.get_account_info()
    if account_info:
        with col1:
            st.metric("Balance", f"${account_info.get('balance', 0):,.2f}")
        with col2:
            st.metric("Equity", f"${account_info.get('equity', 0):,.2f}")
        with col3:
            unrealized_pnl = portfolio.get_unrealized_pnl()
            st.metric("Unrealized PnL", f"${unrealized_pnl:,.2f}", 
                     delta=f"{unrealized_pnl/account_info.get('balance', 1)*100:.2f}%")
        with col4:
            open_positions = portfolio.get_open_positions_count()
            st.metric("Open Positions", open_positions)
    
    st.divider()
    
    # Open positions
    st.subheader("📊 Open Positions")
    positions = portfolio.get_open_positions()
    
    if positions:
        position_data = []
        for pos in positions:
            position_data.append({
                "Symbol": pos.get('symbol', ''),
                "Type": "BUY" if pos.get('type', 0) == 0 else "SELL",
                "Volume": f"{pos.get('volume', 0):.2f}",
                "Entry Price": f"{pos.get('price_open', 0):.5f}",
                "Current Price": f"{pos.get('price_current', 0):.5f}",
                "SL": f"{pos.get('sl', 0):.5f}" if pos.get('sl', 0) > 0 else "N/A",
                "TP": f"{pos.get('tp', 0):.5f}" if pos.get('tp', 0) > 0 else "N/A",
                "PnL": f"${pos.get('profit', 0):.2f}",
            })
        
        st.dataframe(position_data, width="stretch")
    else:
        st.info("No open positions")
    
    st.divider()
    
    # Recent decisions
    st.subheader("🎯 Recent Decisions")
    decisions = state.get_recent_decisions(limit=10)
    
    if decisions:
        decision_data = []
        for dec in decisions:
            decision_data.append({
                "Time": dec.get('timestamp', '')[:19] if dec.get('timestamp') else '',
                "Symbol": dec.get('symbol', ''),
                "Signal": dec.get('signal', ''),
                "Action": dec.get('action', ''),
                "Confidence": f"{dec.get('confidence', 0):.2f}",
                "Risk OK": "✅" if dec.get('risk_checks_passed') else "❌",
                "Executed": "✅" if dec.get('execution_success') else "❌",
            })
        
        st.dataframe(decision_data, width="stretch")
    else:
        st.info("No decisions yet")
    
    st.divider()
    
    # PnL by symbol
    st.subheader("💰 PnL by Symbol")
    pnl_by_symbol = portfolio.get_unrealized_pnl_by_symbol()
    
    if pnl_by_symbol:
        symbols = list(pnl_by_symbol.keys())
        pnls = list(pnl_by_symbol.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=symbols,
                y=pnls,
                marker_color=['green' if p > 0 else 'red' for p in pnls]
            )
        ])
        fig.update_layout(
            title="Unrealized PnL by Symbol",
            xaxis_title="Symbol",
            yaxis_title="PnL ($)",
            height=400
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No PnL data available")


def render_dashboard_remote(api_client):
    """Render dashboard page - Remote mode using API client"""
    import asyncio
    
    # Get data from API
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    conn_status = loop.run_until_complete(api_client.get_connection_status())
    trading_status = loop.run_until_complete(api_client.get_trading_status())
    positions = loop.run_until_complete(api_client.get_positions())
    decisions = loop.run_until_complete(api_client.get_decisions(limit=10))
    loop.close()
    
    # Account metrics
    col1, col2, col3, col4 = st.columns(4)
    
    account_info = conn_status.get("account_info")
    if account_info:
        with col1:
            st.metric("Balance", f"${account_info.get('balance', 0):,.2f}")
        with col2:
            st.metric("Equity", f"${account_info.get('equity', 0):,.2f}")
        with col3:
            unrealized_pnl = (account_info.get('equity', 0) - account_info.get('balance', 0))
            st.metric("Unrealized PnL", f"${unrealized_pnl:,.2f}")
        with col4:
            st.metric("Open Positions", trading_status.get('open_positions', 0))
    
    st.divider()
    
    # Open positions
    st.subheader("📊 Open Positions")
    
    if positions:
        position_data = []
        for pos in positions:
            position_data.append({
                "Symbol": pos.get('symbol', ''),
                "Type": "BUY" if pos.get('type', 0) == 0 else "SELL",
                "Volume": f"{pos.get('volume', 0):.2f}",
                "Entry Price": f"{pos.get('price_open', 0):.5f}",
                "Current Price": f"{pos.get('price_current', 0):.5f}",
                "SL": f"{pos.get('sl', 0):.5f}" if pos.get('sl', 0) > 0 else "N/A",
                "TP": f"{pos.get('tp', 0):.5f}" if pos.get('tp', 0) > 0 else "N/A",
                "PnL": f"${pos.get('profit', 0):.2f}",
            })
        
        st.dataframe(position_data, width="stretch")
    else:
        st.info("No open positions")
    
    st.divider()
    
    # Recent decisions
    st.subheader("🎯 Recent Decisions")
    
    if decisions:
        decision_data = []
        for dec in decisions:
            decision_data.append({
                "Time": dec.get('timestamp', '')[:19] if dec.get('timestamp') else '',
                "Symbol": dec.get('symbol', ''),
                "Signal": dec.get('signal', ''),
                "Action": dec.get('action', ''),
                "Confidence": f"{dec.get('confidence', 0):.2f}",
                "Risk OK": "✅" if dec.get('risk_checks_passed') else "❌",
                "Executed": "✅" if dec.get('execution_success') else "❌",
            })
        
        st.dataframe(decision_data, width="stretch")
    else:
        st.info("No decisions yet")
    
    st.divider()
    
    # PnL by symbol
    st.subheader("💰 PnL by Symbol")
    
    if positions:
        pnl_by_symbol = {}
        for pos in positions:
            symbol = pos.get('symbol', '')
            profit = pos.get('profit', 0.0)
            if symbol:
                pnl_by_symbol[symbol] = pnl_by_symbol.get(symbol, 0.0) + profit
        
        if pnl_by_symbol:
            symbols = list(pnl_by_symbol.keys())
            pnls = list(pnl_by_symbol.values())
            
            fig = go.Figure(data=[
                go.Bar(
                    x=symbols,
                    y=pnls,
                    marker_color=['green' if p > 0 else 'red' for p in pnls]
                )
            ])
            fig.update_layout(
                title="Unrealized PnL by Symbol",
                xaxis_title="Symbol",
                yaxis_title="PnL ($)",
                height=400
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No PnL data available")
    else:
        st.info("No positions to display")
