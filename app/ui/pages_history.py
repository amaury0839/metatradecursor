"""Historical Analysis and Trade History UI Pages"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from app.core.database import get_database_manager
from app.core.logger import setup_logger

logger = setup_logger("ui_history")


def render_analysis_history_page():
    """Render analysis history page"""
    st.title("📊 Historical Analysis")
    
    db = get_database_manager()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days = st.selectbox("Time Period", [1, 3, 7, 14, 30], index=2)
    
    with col2:
        symbols = ['ALL'] + ['EURUSD', 'USDJPY', 'GBPUSD', 'BTCUSD', 'ETHUSD', 'XRPUSD']
        selected_symbol = st.selectbox("Symbol", symbols)
    
    with col3:
        signal_filter = st.selectbox("Signal", ['ALL', 'BUY', 'SELL', 'HOLD'])
    
    # Get analysis history
    symbol_query = None if selected_symbol == 'ALL' else selected_symbol
    analyses = db.get_analysis_history(symbol=symbol_query, days=days)
    
    if not analyses:
        st.warning("No analysis data available for selected period")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(analyses)
    
    # Apply signal filter
    if signal_filter != 'ALL':
        df = df[df['final_signal'] == signal_filter]
    
    # Display summary metrics
    st.subheader("Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyses", len(df))
    
    with col2:
        buy_signals = len(df[df['final_signal'] == 'BUY'])
        st.metric("BUY Signals", buy_signals)
    
    with col3:
        sell_signals = len(df[df['final_signal'] == 'SELL'])
        st.metric("SELL Signals", sell_signals)
    
    with col4:
        hold_signals = len(df[df['final_signal'] == 'HOLD'])
        st.metric("HOLD Signals", hold_signals)
    
    # Signal distribution chart
    st.subheader("Signal Distribution")
    signal_counts = df['final_signal'].value_counts()
    fig = px.pie(values=signal_counts.values, names=signal_counts.index,
                 title="Analysis Signal Distribution",
                 color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'})
    st.plotly_chart(fig, width="stretch")
    
    # Confidence over time
    st.subheader("Confidence Trend")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_sorted = df.sort_values('timestamp')
    
    fig = go.Figure()
    
    for signal in ['BUY', 'SELL', 'HOLD']:
        signal_df = df_sorted[df_sorted['final_signal'] == signal]
        if not signal_df.empty:
            color = 'green' if signal == 'BUY' else 'red' if signal == 'SELL' else 'gray'
            fig.add_trace(go.Scatter(
                x=signal_df['timestamp'],
                y=signal_df['confidence'],
                mode='markers+lines',
                name=signal,
                marker=dict(color=color, size=8),
                line=dict(color=color, width=1)
            ))
    
    fig.update_layout(
        title="Confidence Levels Over Time",
        xaxis_title="Time",
        yaxis_title="Confidence",
        hovermode='x unified'
    )
    st.plotly_chart(fig, width="stretch")
    
    # RSI distribution
    st.subheader("Technical Indicators")
    col1, col2 = st.columns(2)
    
    with col1:
        if 'tech_rsi' in df.columns:
            fig = go.Figure(data=[go.Histogram(x=df['tech_rsi'].dropna(), nbinsx=30)])
            fig.update_layout(title="RSI Distribution", xaxis_title="RSI", yaxis_title="Count")
            fig.add_vline(x=30, line_dash="dash", line_color="green", annotation_text="Oversold")
            fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        if 'combined_score' in df.columns:
            fig = go.Figure(data=[go.Histogram(x=df['combined_score'].dropna(), nbinsx=30)])
            fig.update_layout(title="Combined Score Distribution", 
                            xaxis_title="Score", yaxis_title="Count")
            fig.add_vline(x=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, width="stretch")
    
    # Detailed analysis table
    st.subheader("Detailed Analysis Records")
    
    # Select columns to display
    display_cols = ['timestamp', 'symbol', 'final_signal', 'confidence', 
                   'tech_rsi', 'sentiment_score', 'combined_score']
    display_cols = [col for col in display_cols if col in df.columns]
    
    display_df = df[display_cols].sort_values('timestamp', ascending=False)
    
    # Format columns
    if 'timestamp' in display_df.columns:
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Color code signals
    def highlight_signal(row):
        if row['final_signal'] == 'BUY':
            return ['background-color: rgba(0,255,0,0.1)'] * len(row)
        elif row['final_signal'] == 'SELL':
            return ['background-color: rgba(255,0,0,0.1)'] * len(row)
        return [''] * len(row)
    
    styled_df = display_df.style.apply(highlight_signal, axis=1)
    st.dataframe(styled_df, width="stretch", height=400)


def render_ai_decisions_page():
    """Render AI decisions history page"""
    st.title("🤖 AI Decision History")
    
    db = get_database_manager()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days = st.selectbox("Time Period", [1, 3, 7, 14, 30], index=2, key='ai_days')
    
    with col2:
        symbols = ['ALL'] + ['EURUSD', 'USDJPY', 'GBPUSD', 'BTCUSD', 'ETHUSD', 'XRPUSD']
        selected_symbol = st.selectbox("Symbol", symbols, key='ai_symbol')
    
    with col3:
        show_executed = st.checkbox("Executed Only", value=False)
    
    # Get AI decisions
    symbol_query = None if selected_symbol == 'ALL' else selected_symbol
    decisions = db.get_ai_decisions(symbol=symbol_query, days=days, executed_only=show_executed)
    
    if not decisions:
        st.warning("No AI decisions available for selected period")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(decisions)
    
    # Display summary
    st.subheader("AI Decision Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Decisions", len(df))
    
    with col2:
        enhanced_count = len(df[df['engine_type'] == 'enhanced'])
        st.metric("Enhanced AI", enhanced_count)
    
    with col3:
        executed_count = len(df[df['executed'] == 1])
        st.metric("Executed", executed_count)
    
    with col4:
        avg_conf = df['confidence'].mean()
        st.metric("Avg Confidence", f"{avg_conf:.1%}")
    
    # Engine type distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Engine Type Distribution")
        engine_counts = df['engine_type'].value_counts()
        fig = px.pie(values=engine_counts.values, names=engine_counts.index,
                    title="AI Engine Usage")
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("Action Distribution")
        action_counts = df['action'].value_counts()
        fig = px.bar(x=action_counts.index, y=action_counts.values,
                    title="AI Actions",
                    color=action_counts.index,
                    color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'})
        st.plotly_chart(fig, width="stretch")
    
    # Confidence comparison
    st.subheader("Confidence by Engine Type")
    fig = go.Figure()
    
    for engine in df['engine_type'].unique():
        engine_df = df[df['engine_type'] == engine]
        fig.add_trace(go.Box(y=engine_df['confidence'], name=engine))
    
    fig.update_layout(title="Confidence Distribution by Engine", yaxis_title="Confidence")
    st.plotly_chart(fig, width="stretch")
    
    # Detailed decisions table
    st.subheader("Detailed AI Decisions")
    
    display_cols = ['timestamp', 'symbol', 'action', 'confidence', 'engine_type', 
                   'executed', 'stop_loss', 'take_profit']
    display_cols = [col for col in display_cols if col in df.columns]
    
    display_df = df[display_cols].sort_values('timestamp', ascending=False)
    
    # Format
    if 'timestamp' in display_df.columns:
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    if 'confidence' in display_df.columns:
        display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
    if 'executed' in display_df.columns:
        display_df['executed'] = display_df['executed'].map({1: '✅', 0: '❌'})
    
    st.dataframe(display_df, width="stretch", height=400)


def render_trade_history_page():
    """Render trade history and performance page"""
    st.title("📈 Trade History & Performance")
    
    db = get_database_manager()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=1, key='trade_days')
    
    with col2:
        symbols = ['ALL'] + ['EURUSD', 'USDJPY', 'GBPUSD', 'BTCUSD', 'ETHUSD', 'XRPUSD']
        selected_symbol = st.selectbox("Symbol", symbols, key='trade_symbol')
    
    with col3:
        status_options = ['ALL', 'open', 'closed']
        status = st.selectbox("Status", status_options, key='trade_status')
    
    # Get trades
    symbol_query = None if selected_symbol == 'ALL' else selected_symbol
    status_query = None if status == 'ALL' else status
    trades = db.get_trades(symbol=symbol_query, status=status_query, days=days)
    
    if not trades:
        st.warning("No trades available for selected period")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(trades)
    
    # Performance summary
    perf = db.get_performance_summary(days=days)
    
    st.subheader("Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", perf['total_trades'])
        st.metric("Winning Trades", perf['winning_trades'])
    
    with col2:
        st.metric("Win Rate", f"{perf['win_rate']:.1f}%")
        st.metric("Losing Trades", perf['losing_trades'])
    
    with col3:
        profit_color = "normal" if perf['net_profit'] >= 0 else "inverse"
        st.metric("Net Profit", f"${perf['net_profit']:.2f}", delta_color=profit_color)
        st.metric("Avg Profit/Trade", f"${perf['avg_profit']:.2f}")
    
    with col4:
        st.metric("Profit Factor", f"{perf['profit_factor']:.2f}")
        st.metric("Gross Profit", f"${perf['gross_profit']:.2f}")
    
    # Equity curve
    st.subheader("Equity Curve")
    closed_trades = df[df['status'] == 'closed'].copy()
    
    if not closed_trades.empty:
        closed_trades['close_timestamp'] = pd.to_datetime(closed_trades['close_timestamp'])
        closed_trades = closed_trades.sort_values('close_timestamp')
        closed_trades['cumulative_profit'] = closed_trades['profit'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=closed_trades['close_timestamp'],
            y=closed_trades['cumulative_profit'],
            mode='lines',
            name='Equity',
            line=dict(color='blue', width=2),
            fill='tozeroy'
        ))
        
        fig.update_layout(
            title="Cumulative P&L Over Time",
            xaxis_title="Date",
            yaxis_title="Cumulative Profit ($)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, width="stretch")
    
    # Profit distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profit Distribution")
        if not closed_trades.empty:
            fig = go.Figure(data=[go.Histogram(
                x=closed_trades['profit'],
                nbinsx=30,
                marker_color='green'
            )])
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            fig.update_layout(xaxis_title="Profit ($)", yaxis_title="Count")
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("Trades by Symbol")
        symbol_counts = df['symbol'].value_counts()
        fig = px.bar(x=symbol_counts.index, y=symbol_counts.values,
                    title="Trade Count by Symbol")
        fig.update_layout(xaxis_title="Symbol", yaxis_title="Count")
        st.plotly_chart(fig, width="stretch")
    
    # Detailed trades table
    st.subheader("Detailed Trade Records")
    
    display_cols = ['ticket', 'symbol', 'type', 'volume', 'open_price', 'close_price',
                   'profit', 'status', 'open_timestamp', 'close_timestamp']
    display_cols = [col for col in display_cols if col in df.columns]
    
    display_df = df[display_cols].sort_values('open_timestamp', ascending=False)
    
    # Format
    if 'open_timestamp' in display_df.columns:
        display_df['open_timestamp'] = pd.to_datetime(display_df['open_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    if 'close_timestamp' in display_df.columns:
        display_df['close_timestamp'] = pd.to_datetime(display_df['close_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Color code by profit
    def highlight_profit(row):
        if pd.notna(row.get('profit')):
            if row['profit'] > 0:
                return ['background-color: rgba(0,255,0,0.1)'] * len(row)
            elif row['profit'] < 0:
                return ['background-color: rgba(255,0,0,0.1)'] * len(row)
        return [''] * len(row)
    
    styled_df = display_df.style.apply(highlight_profit, axis=1)
    st.dataframe(styled_df, width="stretch", height=400)
