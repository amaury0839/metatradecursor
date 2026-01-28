"""Unified Modern Dashboard - Complete Trading Overview"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

from app.ui.themes_modern import get_theme, apply_global_theme
from app.ui.components_modern import (
    MetricsDisplay, ChartComponents, TableComponents, 
    AlertComponents, FormComponents, render_header
)


def load_trading_data():
    """Load current trading data from database/logs"""
    # This would be replaced with actual database calls
    # For now, return mock data
    return {
        "positions": 12,
        "max_positions": 50,
        "total_equity": 10250.00,
        "free_margin": 5125.00,
        "daily_pnl": 325.50,
        "win_rate": 0.62,
        "risk_exposure": 2.45,
    }


def load_positions_df():
    """Load open positions dataframe"""
    return pd.DataFrame({
        "Symbol": ["EURUSD", "GBPUSD", "USDJPY", "AUDCAD", "EURAUD", "NZDUSD", "XRPUSD", "BTCUSD", "AUDCHF", "CADJPY", "AUDNZD", "AUDSGD"],
        "Type": ["BUY", "SELL", "BUY", "SELL", "BUY", "SELL", "BUY", "SELL", "BUY", "SELL", "BUY", "SELL"],
        "Volume": [2.0, 1.5, 1.0, 0.5, 1.2, 0.8, 100, 0.02, 0.3, 0.1, 0.4, 0.6],
        "Entry": [1.0850, 1.2650, 145.32, 0.8945, 1.6850, 2.1250, 0.5234, 28450.50, 0.9145, 92.45, 1.0645, 0.9145],
        "Current": [1.0865, 1.2620, 145.45, 0.8935, 1.6870, 2.1200, 0.5250, 28380.00, 0.9135, 92.30, 1.0665, 0.9135],
        "P&L": [30.00, -37.50, 13.15, -5.00, 24.00, -40.00, 16.00, -70.50, -3.00, -1.50, 8.00, -3.00],
        "Risk%": [2.0, 2.0, 2.5, 2.5, 2.0, 2.0, 3.0, 3.0, 2.0, 2.0, 2.5, 2.5],
    })


def load_trades_df():
    """Load recent trades dataframe"""
    return pd.DataFrame({
        "ID": [1433007128, 1433007150, 1433007178, 1433007195, 1433007212],
        "Symbol": ["EURUSD", "GBPUSD", "AUDCAD", "XRPUSD", "BTCUSD"],
        "Type": ["BUY", "SELL", "SELL", "BUY", "SELL"],
        "Entry": [1.0850, 1.2650, 0.8945, 0.5200, 28600.00],
        "Exit": [1.0855, 1.2630, 0.8940, 0.5210, 28550.00],
        "P&L": [5.00, -30.00, -2.50, 10.00, -50.00],
        "Time": ["14:32:10", "14:28:45", "14:25:30", "14:22:15", "14:18:00"],
    })


def load_performance_data():
    """Load performance metrics"""
    # Generate sample performance data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
    returns = np.cumsum(np.random.normal(15, 25, 30))
    
    return pd.DataFrame({
        "Date": dates,
        "Cumulative Return": returns,
    })


def display_main_metrics(data):
    """Display main KPI metrics"""
    st.markdown("### 📊 Key Performance Indicators")
    
    metrics = {
        "Total Equity": {
            "value": f"${data['total_equity']:,.2f}",
            "unit": "",
            "change": 3.25,
            "positive": True
        },
        "Free Margin": {
            "value": f"${data['free_margin']:,.2f}",
            "unit": "",
            "change": 1.50,
            "positive": True
        },
        "Daily P&L": {
            "value": f"${data['daily_pnl']:,.2f}",
            "unit": "",
            "change": 5.40,
            "positive": True
        },
        "Win Rate": {
            "value": f"{data['win_rate']*100:.1f}%",
            "unit": "",
            "change": 2.10,
            "positive": True
        },
    }
    
    MetricsDisplay.display_metrics(metrics, cols=4)


def display_position_limits():
    """Display position limit visualization"""
    st.markdown("### 📍 Position Management (Critical Feature)")
    
    data = load_trading_data()
    max_pos = data["max_positions"]
    current_pos = data["positions"]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gauge for position limit
        fig = ChartComponents.gauge_chart(
            value=current_pos,
            max_value=max_pos,
            title=f"Open Positions: {current_pos}/{max_pos}",
            thresholds={"warning": 30, "critical": 40}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Position info
        remaining = max_pos - current_pos
        usage_pct = (current_pos / max_pos) * 100
        
        st.metric("Max Positions", max_pos)
        st.metric("Current Positions", current_pos)
        st.metric("Remaining Slots", remaining)
        
        if usage_pct > 80:
            AlertComponents.alert_box(
                "⚠️ Position limit approaching! Only 6 slots remaining.",
                "warning"
            )


def display_risk_management():
    """Display risk management and dynamic risk features"""
    st.markdown("### ⚠️ Risk Management (Dynamic Risk System)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk allocation by asset class
        risk_data = {
            "Forex Major\n(EURUSD, GBPUSD)": 2.0,
            "Forex Cross\n(AUDCAD, EURAUD)": 2.5,
            "Crypto\n(XRPUSD, BTCUSD)": 3.0,
        }
        
        fig = ChartComponents.pie_chart(risk_data, "Risk % by Asset Class")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk metrics
        st.markdown("#### Risk Configuration")
        st.info("""
        🔧 **Dynamic Risk System Activated**
        
        • **Forex Major**: 2.0% risk per trade
        • **Forex Cross**: 2.5% risk per trade  
        • **Crypto**: 3.0% risk per trade
        
        • **Multiplier Range**: 0.6x - 1.2x
        • **Performance-based**: Adjusts based on streak
        • **Hard Closes**: 4 rules active
        """)


def display_open_positions(df):
    """Display open positions with features highlight"""
    st.markdown("### 💼 Open Positions")
    
    # Add feature highlight
    with st.expander("ℹ️ How positions are managed"):
        st.markdown("""
        **Critical Features Integrated:**
        - ✅ Minimum lot enforcement (symbols have min quantities)
        - ✅ Dynamic risk adjustment based on performance
        - ✅ Hard close rules (RSI overbought, TTL expiration, EMA cross, trend change)
        - ✅ Position limit enforced at 50 maximum
        """)
    
    # Display table
    display_df = df.copy()
    display_df["P&L"] = display_df["P&L"].apply(lambda x: f"{'🟢' if x > 0 else '🔴'} ${x:.2f}")
    display_df["Risk%"] = display_df["Risk%"].apply(lambda x: f"🟡 {x:.1f}%" if x > 2.0 else f"🟢 {x:.1f}%")
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    total_pnl = df["P&L"].sum()
    winning_trades = (df["P&L"] > 0).sum()
    
    with col1:
        st.metric("Total P&L", f"${total_pnl:.2f}", delta=f"{(total_pnl/df['P&L'].sum()*100):.1f}%" if total_pnl > 0 else None)
    
    with col2:
        st.metric("Winning Positions", f"{winning_trades}/{len(df)}", delta=f"{(winning_trades/len(df)*100):.0f}%")
    
    with col3:
        avg_risk = df["Risk%"].mean()
        st.metric("Avg Risk%", f"{avg_risk:.2f}%")
    
    with col4:
        st.metric("Total Volume", f"${(df['Volume'] * df['Current']).sum():,.0f}")


def display_recent_trades(df):
    """Display recent trades history"""
    st.markdown("### 📈 Recent Trades (Last 5)")
    
    display_df = df.copy()
    display_df["P&L"] = display_df["P&L"].apply(lambda x: f"{'🟢' if x > 0 else '🔴'} ${x:.2f}")
    
    st.dataframe(display_df, use_container_width=True, height=250)


def display_performance_chart():
    """Display cumulative performance chart"""
    st.markdown("### 📊 Performance History (Last 30 Days)")
    
    df = load_performance_data()
    
    fig = ChartComponents.line_chart(
        df, "Date", "Cumulative Return",
        "Cumulative P&L (30 Days)",
        color="#2CA02C"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_hard_close_rules():
    """Display hard close rules status"""
    st.markdown("### 🛑 Hard Close Rules (Emergency Exit System)")
    
    rules = {
        "RSI Overbought": {
            "condition": "RSI > 80",
            "status": "active",
            "last_trigger": "14:25 - AUDCAD",
            "trades_closed": 3
        },
        "Time-to-Live": {
            "condition": "Position open > 4 hours",
            "status": "active",
            "last_trigger": "13:30 - EURUSD",
            "trades_closed": 1
        },
        "EMA Crossover": {
            "condition": "Price cross EMA 20",
            "status": "active",
            "last_trigger": "12:45 - GBPUSD",
            "trades_closed": 2
        },
        "Trend Reversal": {
            "condition": "ADX < 15 (weak trend)",
            "status": "active",
            "last_trigger": "11:20 - USDJPY",
            "trades_closed": 1
        },
    }
    
    cols = st.columns(2)
    
    for idx, (rule_name, rule_data) in enumerate(rules.items()):
        with cols[idx % 2]:
            st.markdown(f"""
            **{rule_name}**
            - Condition: `{rule_data['condition']}`
            - Status: {'🟢 Active' if rule_data['status'] == 'active' else '🔴 Inactive'}
            - Last trigger: {rule_data['last_trigger']}
            - Trades closed: {rule_data['trades_closed']}
            """)


def main():
    """Main dashboard function"""
    # Apply modern theme
    apply_global_theme()
    
    # Page config
    st.set_page_config(
        page_title="AI Trading Bot Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard Controls")
        
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
        show_advanced = st.checkbox("Show Advanced Metrics", value=False)
        
        st.divider()
        st.markdown("### 📋 Navigation")
        
        page = st.radio("Go to page:", [
            "Dashboard",
            "Trading Monitor",
            "Portfolio",
            "Analytics",
            "Risk Management",
            "Backtest",
            "Settings",
            "Logs"
        ])
    
    # Load data
    trading_data = load_trading_data()
    positions_df = load_positions_df()
    trades_df = load_trades_df()
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "🟢 Active", "System operational")
    
    with col2:
        st.metric("Positions", f"{trading_data['positions']}/{trading_data['max_positions']}", "+2 today")
    
    with col3:
        st.metric("Daily P&L", f"${trading_data['daily_pnl']:,.2f}", "+3.25%")
    
    st.divider()
    
    # Metrics row
    display_main_metrics(trading_data)
    
    st.divider()
    
    # Position management with limits
    display_position_limits()
    
    st.divider()
    
    # Risk management
    display_risk_management()
    
    st.divider()
    
    # Hard close rules
    display_hard_close_rules()
    
    st.divider()
    
    # Open positions
    display_open_positions(positions_df)
    
    st.divider()
    
    # Recent trades
    display_recent_trades(trades_df)
    
    st.divider()
    
    # Performance chart
    display_performance_chart()
    
    # Advanced metrics (if enabled)
    if show_advanced:
        st.divider()
        st.markdown("### 🔬 Advanced Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Drawdown chart
            drawdown_data = {
                "Max Drawdown": 5.2,
                "Current Drawdown": 2.1,
                "Recovery Time": 3,
            }
            
            for label, value in drawdown_data.items():
                st.metric(label, f"{value:.1f}%")
        
        with col2:
            # Asset breakdown
            asset_breakdown = {
                "Forex": 70.5,
                "Crypto": 29.5,
            }
            
            fig = ChartComponents.pie_chart(asset_breakdown, "Portfolio by Asset Class")
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
