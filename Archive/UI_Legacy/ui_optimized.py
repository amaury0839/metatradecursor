"""High-performance optimized Streamlit UI"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px

# Local imports
from app.core.config import get_config
from app.trading.mt5_client import get_mt5_client
from app.trading.portfolio import get_portfolio_manager
from app.trading.integrated_analysis import get_integrated_analyzer
from app.core.database import get_database_manager
from app.trading.indicator_optimizer import get_indicator_optimizer
from app.ui.cache_manager import get_cache, get_historical_cache, streamlit_cache

# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="🤖 Trading Bot - Performance Suite",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Dashboard"

# ============================================================================
# CACHED DATA LOADERS (with optimized TTL)
# ============================================================================

@streamlit_cache(ttl=10)  # 10 second cache
def load_account_info() -> Dict[str, Any]:
    """Load account info with caching"""
    mt5 = get_mt5_client()
    return mt5.get_account_info() or {}

@streamlit_cache(ttl=15)
def load_open_positions() -> List[Dict]:
    """Load open positions"""
    portfolio = get_portfolio_manager()
    return portfolio.get_open_positions() or []

@streamlit_cache(ttl=20)
def load_trade_history(days: int = 7) -> pd.DataFrame:
    """Load historical trades with optimal caching"""
    db = get_database_manager()
    cache = get_historical_cache()
    
    key = f"trades_{days}d"
    cached = cache.get(key, max_age_seconds=3600)
    if cached is not None:
        return cached
    
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return pd.DataFrame()
    
    df = pd.DataFrame(trades)
    cache.set(key, df)
    return df

@streamlit_cache(ttl=30)
def load_performance_metrics(days: int = 7) -> Dict[str, Any]:
    """Load performance metrics"""
    db = get_database_manager()
    
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0
        }
    
    wins = sum(1 for t in trades if t.get("profit", 0) > 0)
    losses = len(trades) - wins
    gross_profit = sum(max(0, t.get("profit", 0)) for t in trades)
    gross_loss = sum(abs(min(0, t.get("profit", 0))) for t in trades)
    
    return {
        "total_trades": len(trades),
        "win_rate": wins / len(trades) if trades else 0,
        "winning_trades": wins,
        "losing_trades": losses,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else gross_profit,
        "total_pnl": sum(t.get("profit", 0) for t in trades),
    }

# ============================================================================
# DASHBOARD - MAIN VIEW
# ============================================================================

def render_dashboard():
    """Render optimized main dashboard"""
    st.title("📊 Trading Bot Dashboard")
    
    # Top metrics row (3 columns)
    col1, col2, col3, col4 = st.columns(4)
    
    account = load_account_info()
    positions = load_open_positions()
    
    with col1:
        st.metric(
            "💰 Equity",
            f"${account.get('equity', 0):,.2f}",
            f"${account.get('equity', 0) - account.get('balance', 0):+.2f}"
        )
    
    with col2:
        st.metric(
            "📈 Open Positions",
            len(positions),
            "4 Max"
        )
    
    with col3:
        st.metric(
            "📊 Win Rate",
            f"{load_performance_metrics()['win_rate']*100:.1f}%",
            help="Last 7 days"
        )
    
    with col4:
        st.metric(
            "🎯 Profit Factor",
            f"{load_performance_metrics()['profit_factor']:.2f}",
            help="Gross Profit / Gross Loss"
        )
    
    st.divider()
    
    # Two-column layout
    col_chart, col_positions = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📈 Equity Curve (24h)")
        render_equity_chart()
    
    with col_positions:
        st.subheader("💼 Open Positions")
        render_positions_table(positions)
    
    st.divider()
    
    # Trade distribution
    col_dist, col_time = st.columns(2)
    with col_dist:
        st.subheader("Trade Distribution")
        render_trade_distribution()
    
    with col_time:
        st.subheader("Performance by Hour")
        render_hourly_performance()


def render_equity_chart():
    """Optimized equity chart"""
    try:
        db = get_database_manager()
        trades = db.get_trades(since=datetime.now() - timedelta(hours=24))
        
        if not trades:
            st.info("No trades in last 24 hours")
            return
        
        # Calculate running equity
        df = pd.DataFrame(trades)
        df['timestamp'] = pd.to_datetime(df['open_timestamp'])
        df = df.sort_values('timestamp')
        df['cumulative_pnl'] = df['profit'].cumsum()
        
        # Create chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cumulative_pnl'],
            mode='lines+markers',
            name='Equity',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy'
        ))
        
        fig.update_layout(
            height=300,
            showlegend=False,
            hovermode='x unified',
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")


def render_positions_table(positions: List[Dict]):
    """Optimized positions table"""
    if not positions:
        st.info("No open positions")
        return
    
    data = []
    for pos in positions:
        data.append({
            "Symbol": pos.get("symbol", "N/A"),
            "Type": "🔼 BUY" if pos.get("type") == 0 else "🔽 SELL",
            "Volume": f"{pos.get('volume', 0):.2f}",
            "Entry": f"${pos.get('price_open', 0):.5f}",
            "P&L": f"${pos.get('profit', 0):+.2f}",
            "ROI%": f"{(pos.get('profit', 0) / (pos.get('price_open', 0) * pos.get('volume', 0) * 100000) * 100 if pos.get('price_open') else 0):+.2f}%"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_trade_distribution():
    """Trade count by symbol"""
    df = load_trade_history(days=7)
    if df.empty:
        st.info("No trades")
        return
    
    symbol_counts = df['symbol'].value_counts().head(10)
    fig = px.bar(symbol_counts, title="Trade Count by Symbol")
    st.plotly_chart(fig, use_container_width=True, height=300)


def render_hourly_performance():
    """Hourly win rate"""
    df = load_trade_history(days=7)
    if df.empty:
        st.info("No trades")
        return
    
    df['hour'] = pd.to_datetime(df['open_timestamp']).dt.hour
    df['is_win'] = df['profit'] > 0
    
    hourly = df.groupby('hour')['is_win'].agg(['sum', 'count'])
    hourly['win_rate'] = (hourly['sum'] / hourly['count'] * 100).fillna(0)
    
    fig = px.bar(hourly.reset_index(), x='hour', y='win_rate', title="Win Rate by Hour")
    st.plotly_chart(fig, use_container_width=True, height=300)


# ============================================================================
# ANALYSIS TAB
# ============================================================================

def render_analysis():
    """Real-time analysis view"""
    st.title("🔍 Real-time Analysis")
    
    config = get_config()
    analyzer = get_integrated_analyzer()
    
    symbols = config.trading.default_symbols
    selected_symbol = st.selectbox("Select Symbol", symbols)
    
    if selected_symbol:
        with st.spinner(f"Analyzing {selected_symbol}..."):
            analysis = analyzer.analyze_symbol(selected_symbol)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Signal", analysis.get("signal", "N/A"))
            st.metric("Confidence", f"{analysis.get('confidence', 0):.1%}")
        
        with col2:
            if analysis.get("technical"):
                tech = analysis["technical"]["data"]
                st.metric("RSI", f"{tech.get('rsi', 0):.1f}")
                st.metric("ATR", f"{tech.get('atr', 0):.5f}")
        
        with col3:
            if analysis.get("sentiment"):
                st.metric("Sentiment", f"{analysis['sentiment'].get('score', 0):+.2f}")
                st.metric("News Items", len(analysis.get("sentiment", {}).get("articles", [])))
        
        st.divider()
        st.json(analysis)


# ============================================================================
# OPTIMIZER TAB
# ============================================================================

def render_optimizer():
    """AI-driven indicator optimizer"""
    st.title("🤖 Indicator Optimizer")
    
    optimizer = get_indicator_optimizer()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Performance Analysis")
        hours = st.slider("Analyze last N hours", 1, 72, 24)
        
        if st.button("📊 Analyze & Generate Recommendations"):
            with st.spinner("AI analyzing performance..."):
                report = optimizer.continuous_optimization_report(hours=hours)
            
            if "error" not in report:
                # Display results
                perf = report.get("performance_summary", {})
                st.write(f"**Total Trades**: {perf.get('total_trades', 0)}")
                
                if "by_strategy" in perf:
                    st.write("**By Strategy**:")
                    for strat, metrics in perf["by_strategy"].items():
                        st.write(f"  - {strat}: {metrics['trades']} trades, {metrics['win_rate']*100:.1f}% WR")
                
                # Show recommendations
                rec = report.get("ai_recommendation", {})
                if "error" not in rec:
                    st.info("**AI Recommendations**:")
                    st.write(rec.get("recommendation", "No recommendations"))
                
                # Show adaptive parameters
                st.success("**Suggested Adaptive Parameters**:")
                adaptive = report.get("adaptive_parameters", {})
                for param, value in adaptive.items():
                    st.write(f"  - {param}: {value}")
                
                # Option to apply
                if st.button("✅ Apply Recommended Parameters"):
                    success, msg = optimizer.apply_optimization(adaptive)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.error(report.get("error"))
    
    with col2:
        st.subheader("Optimization Status")
        st.metric("Last Update", "Active")
        st.metric("Active Parameters", len(optimizer.current_params))
        st.metric("Optimization Mode", "Continuous")


# ============================================================================
# HISTORY TAB
# ============================================================================

def render_history():
    """Optimized trade history view"""
    st.title("📋 Trade History")
    
    days = st.slider("Show trades from last N days", 1, 30, 7)
    
    df = load_trade_history(days=days)
    
    if df.empty:
        st.info(f"No trades in the last {days} days")
        return
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Trades", len(df))
    with col2:
        st.metric("Wins", sum(df['profit'] > 0))
    with col3:
        st.metric("Losses", sum(df['profit'] <= 0))
    with col4:
        st.metric("Total P&L", f"${df['profit'].sum():+.2f}")
    with col5:
        st.metric("Avg Trade", f"${df['profit'].mean():+.2f}")
    
    st.divider()
    
    # Display dataframe with formatting
    df_display = df[[
        'symbol', 'trade_type', 'volume', 'open_price', 'close_price',
        'profit', 'open_timestamp'
    ]].copy()
    
    df_display['profit_pct'] = (df_display['profit'] / (df_display['open_price'] * df_display['volume'] * 100000) * 100).round(2)
    df_display = df_display.sort_values('open_timestamp', ascending=False)
    
    st.dataframe(df_display, use_container_width=True)
    
    # Export option
    if st.button("📥 Export to CSV"):
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


# ============================================================================
# MAIN APP LOGIC
# ============================================================================

def main():
    """Main app router"""
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio(
        "Select Page",
        ["📊 Dashboard", "🔍 Analysis", "🤖 Optimizer", "📋 History", "⚙️ Settings"],
        key="nav"
    )
    
    # Add refresh indicator
    st.sidebar.divider()
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
    with col2:
        if st.button("🔄 Refresh"):
            get_cache().clear()
            st.rerun()
    
    # Render selected page
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "🔍 Analysis":
        render_analysis()
    elif page == "🤖 Optimizer":
        render_optimizer()
    elif page == "📋 History":
        render_history()
    elif page == "⚙️ Settings":
        render_settings()


def render_settings():
    """Settings page"""
    st.title("⚙️ Settings")
    
    st.subheader("Cache Settings")
    if st.button("Clear All Cache"):
        get_cache().clear()
        st.success("Cache cleared!")
    
    st.subheader("Bot Settings")
    config = get_config()
    st.write(f"Mode: {config.trading.mode}")
    st.write(f"Risk per Trade: {config.trading.default_risk_per_trade}%")
    st.write(f"Max Positions: 4")


if __name__ == "__main__":
    main()
