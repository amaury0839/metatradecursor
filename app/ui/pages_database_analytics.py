"""Database Analytics - Performance and Analysis Visualization"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from app.core.database import get_database_manager


def render_database_analytics():
    """Main analytics dashboard from database"""
    st.title("📊 Database Analytics & Performance")
    
    db = get_database_manager()
    
    # Tab selection
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Performance",
        "🎯 Trade Analysis", 
        "🤖 AI Decisions",
        "📊 Analysis History",
        "💾 System Stats"
    ])
    
    # ============== TAB 1: Performance ==============
    with tab1:
        st.header("Performance Metrics")
        
        try:
            # Get all trades
            trades = db.get_trades()
            
            if trades and len(trades) > 0:
                trades_df = pd.DataFrame(trades)
                
                # Convert timestamp strings to datetime
                trades_df['open_timestamp'] = pd.to_datetime(trades_df['open_timestamp'])
                if 'close_timestamp' in trades_df.columns:
                    trades_df['close_timestamp'] = pd.to_datetime(trades_df['close_timestamp'], errors='coerce')
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_trades = len(trades_df)
                    st.metric("Total Trades", total_trades)
                
                with col2:
                    closed_trades = len(trades_df[trades_df['status'] == 'closed'])
                    st.metric("Closed Trades", closed_trades)
                
                with col3:
                    if closed_trades > 0:
                        closed_df = trades_df[trades_df['status'] == 'closed']
                        total_profit = closed_df['profit'].sum() if 'profit' in closed_df.columns else 0
                        st.metric("Total P&L", f"${total_profit:.2f}", 
                                 delta=f"{(total_profit/abs(total_profit)*100) if total_profit != 0 else 0:.1f}%" if total_profit != 0 else "0%")
                    else:
                        st.metric("Total P&L", "$0.00")
                
                with col4:
                    if closed_trades > 0:
                        closed_df = trades_df[trades_df['status'] == 'closed']
                        win_rate = (len(closed_df[closed_df['profit'] > 0]) / closed_trades * 100) if closed_trades > 0 else 0
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    else:
                        st.metric("Win Rate", "0%")
                
                # Performance over time
                st.subheader("Equity Curve")
                
                closed_df = trades_df[trades_df['status'] == 'closed'].copy()
                if len(closed_df) > 0:
                    closed_df = closed_df.sort_values('close_timestamp')
                    closed_df['cumulative_profit'] = closed_df['profit'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=closed_df['close_timestamp'],
                        y=closed_df['cumulative_profit'],
                        mode='lines+markers',
                        name='Cumulative P&L',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    fig.update_layout(
                        title="Cumulative P&L Over Time",
                        xaxis_title="Date",
                        yaxis_title="P&L ($)",
                        height=400,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, width="stretch")
                
                # Profit distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Profit Distribution")
                    closed_df = trades_df[trades_df['status'] == 'closed']
                    if len(closed_df) > 0:
                        fig = px.histogram(
                            closed_df,
                            x='profit',
                            nbins=20,
                            title='Trade P&L Distribution',
                            labels={'profit': 'P&L ($)'},
                            color_discrete_sequence=['#1f77b4']
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, width="stretch")
                
                with col2:
                    st.subheader("Win vs Loss")
                    closed_df = trades_df[trades_df['status'] == 'closed']
                    if len(closed_df) > 0:
                        wins = len(closed_df[closed_df['profit'] > 0])
                        losses = len(closed_df[closed_df['profit'] <= 0])
                        
                        fig = go.Figure(data=[
                            go.Bar(x=['Wins', 'Losses'], y=[wins, losses],
                                   marker_color=['#2ecc71', '#e74c3c'])
                        ])
                        fig.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig, width="stretch")
                
            else:
                st.info("No trades found in database yet.")
                
        except Exception as e:
            st.error(f"Error loading performance data: {e}")
    
    # ============== TAB 2: Trade Analysis ==============
    with tab2:
        st.header("Trade Analysis")
        
        try:
            trades = db.get_trades()
            
            if trades and len(trades) > 0:
                trades_df = pd.DataFrame(trades)
                
                # Filter options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_filter = st.multiselect(
                        "Trade Status",
                        options=['open', 'closed'],
                        default=['closed']
                    )
                
                with col2:
                    if 'symbol' in trades_df.columns:
                        symbols = trades_df['symbol'].unique().tolist()
                        symbol_filter = st.multiselect(
                            "Symbols",
                            options=symbols,
                            default=symbols[:3] if len(symbols) > 3 else symbols
                        )
                    else:
                        symbol_filter = []
                
                with col3:
                    trade_type = st.multiselect(
                        "Trade Type",
                        options=['BUY', 'SELL'] if 'trade_type' in trades_df.columns else [],
                        default=['BUY', 'SELL']
                    )
                
                # Apply filters
                filtered_df = trades_df.copy()
                if status_filter:
                    filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
                if symbol_filter:
                    filtered_df = filtered_df[filtered_df['symbol'].isin(symbol_filter)]
                if trade_type and 'trade_type' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['trade_type'].isin(trade_type)]
                
                # Symbol performance
                st.subheader("Performance by Symbol")
                if 'symbol' in filtered_df.columns:
                    symbol_perf = []
                    for symbol in filtered_df['symbol'].unique():
                        sym_trades = filtered_df[filtered_df['symbol'] == symbol]
                        closed = sym_trades[sym_trades['status'] == 'closed']
                        
                        total_trades = len(sym_trades)
                        closed_trades = len(closed)
                        total_profit = closed['profit'].sum() if 'profit' in closed.columns and len(closed) > 0 else 0
                        win_rate = (len(closed[closed['profit'] > 0]) / closed_trades * 100) if closed_trades > 0 else 0
                        
                        symbol_perf.append({
                            'Symbol': symbol,
                            'Total': total_trades,
                            'Closed': closed_trades,
                            'P&L': f"${total_profit:.2f}",
                            'Win Rate': f"{win_rate:.1f}%"
                        })
                    
                    perf_df = pd.DataFrame(symbol_perf)
                    st.dataframe(perf_df, width="stretch", hide_index=True)
                
                # Detailed trades table
                st.subheader("Trade Details")
                display_cols = ['ticket', 'symbol', 'trade_type', 'volume', 'open_price', 'close_price', 'profit', 'status']
                available_cols = [col for col in display_cols if col in filtered_df.columns]
                
                st.dataframe(
                    filtered_df[available_cols].sort_values('ticket', ascending=False),
                    width="stretch",
                    hide_index=True
                )
                
            else:
                st.info("No trades found in database.")
                
        except Exception as e:
            st.error(f"Error loading trade analysis: {e}")
    
    # ============== TAB 3: AI Decisions ==============
    with tab3:
        st.header("AI Decision Analysis")
        
        try:
            decisions = db.get_ai_decisions()
            
            if decisions and len(decisions) > 0:
                decisions_df = pd.DataFrame(decisions)
                
                # Engine type distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Decision Engine Usage")
                    if 'engine_type' in decisions_df.columns:
                        engine_counts = decisions_df['engine_type'].value_counts()
                        fig = px.pie(
                            values=engine_counts.values,
                            names=engine_counts.index,
                            title='Enhanced vs Simple Engine',
                            color_discrete_map={'enhanced': '#3498db', 'simple': '#95a5a6'}
                        )
                        st.plotly_chart(fig, width="stretch")
                
                with col2:
                    st.subheader("Decision Actions")
                    if 'action' in decisions_df.columns:
                        action_counts = decisions_df['action'].value_counts()
                        fig = px.bar(
                            x=action_counts.index,
                            y=action_counts.values,
                            title='Action Distribution',
                            labels={'x': 'Action', 'y': 'Count'},
                            color_discrete_sequence=['#2ecc71']
                        )
                        st.plotly_chart(fig, width="stretch")
                
                # Confidence analysis
                st.subheader("Confidence Analysis")
                
                if 'confidence' in decisions_df.columns:
                    fig = go.Figure()
                    
                    if 'engine_type' in decisions_df.columns:
                        for engine in decisions_df['engine_type'].unique():
                            engine_data = decisions_df[decisions_df['engine_type'] == engine]['confidence']
                            fig.add_trace(go.Box(
                                y=engine_data,
                                name=f"{engine.upper()} Engine",
                                boxmean='sd'
                            ))
                    
                    fig.update_layout(
                        title='Confidence Distribution by Engine',
                        yaxis_title='Confidence',
                        height=400
                    )
                    st.plotly_chart(fig, width="stretch")
                
                # Recent decisions
                st.subheader("Recent Decisions")
                display_cols = ['symbol', 'timeframe', 'action', 'confidence', 'engine_type', 'timestamp']
                available_cols = [col for col in display_cols if col in decisions_df.columns]
                
                st.dataframe(
                    decisions_df[available_cols].sort_values('timestamp', ascending=False).head(20),
                    width="stretch",
                    hide_index=True
                )
                
            else:
                st.info("No AI decisions found in database.")
                
        except Exception as e:
            st.error(f"Error loading AI decisions: {e}")
    
    # ============== TAB 4: Analysis History ==============
    with tab4:
        st.header("Analysis History")
        
        try:
            analysis = db.get_analysis_history()
            
            if analysis and len(analysis) > 0:
                analysis_df = pd.DataFrame(analysis)
                
                # Filter options
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'symbol' in analysis_df.columns:
                        symbols = analysis_df['symbol'].unique().tolist()
                        symbol_filter = st.multiselect(
                            "Filter by Symbol",
                            options=symbols,
                            default=symbols[0] if symbols else None,
                            key="analysis_symbol"
                        )
                    else:
                        symbol_filter = []
                
                with col2:
                    days = st.slider("Last X days", 1, 30, 7)
                
                # Apply filters
                filtered_df = analysis_df.copy()
                if symbol_filter and 'symbol' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['symbol'].isin(symbol_filter)]
                
                # RSI trends
                st.subheader("Technical Indicators Trends")
                
                if 'rsi' in filtered_df.columns and len(filtered_df) > 0:
                    fig = go.Figure()
                    
                    if 'symbol' in filtered_df.columns:
                        for symbol in filtered_df['symbol'].unique()[:3]:
                            sym_data = filtered_df[filtered_df['symbol'] == symbol].sort_values('timestamp')
                            fig.add_trace(go.Scatter(
                                x=sym_data['timestamp'],
                                y=sym_data['rsi'],
                                name=symbol,
                                mode='lines'
                            ))
                    
                    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                    fig.update_layout(
                        title='RSI Over Time',
                        yaxis_title='RSI',
                        height=400
                    )
                    st.plotly_chart(fig, width="stretch")
                
                # Analysis statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_rsi = filtered_df['rsi'].mean() if 'rsi' in filtered_df.columns else 0
                    st.metric("Avg RSI", f"{avg_rsi:.2f}")
                
                with col2:
                    avg_macd = filtered_df['macd'].mean() if 'macd' in filtered_df.columns else 0
                    st.metric("Avg MACD", f"{avg_macd:.4f}")
                
                with col3:
                    avg_bb = filtered_df['bollinger_position'].mean() if 'bollinger_position' in filtered_df.columns else 0
                    st.metric("Avg BB Pos", f"{avg_bb:.2f}")
                
                with col4:
                    analysis_count = len(filtered_df)
                    st.metric("Total Analysis", analysis_count)
                
                # Recent analysis
                st.subheader("Latest Analysis Records")
                display_cols = ['symbol', 'rsi', 'macd', 'bollinger_position', 'technical_signal', 'timestamp']
                available_cols = [col for col in display_cols if col in filtered_df.columns]
                
                st.dataframe(
                    filtered_df[available_cols].sort_values('timestamp', ascending=False).head(50),
                    width="stretch",
                    hide_index=True
                )
                
            else:
                st.info("No analysis history found in database.")
                
        except Exception as e:
            st.error(f"Error loading analysis history: {e}")
    
    # ============== TAB 5: System Stats ==============
    with tab5:
        st.header("System Statistics")
        
        try:
            # Get all counts
            col1, col2, col3, col4 = st.columns(4)
            
            trades = db.get_trades()
            decisions = db.get_ai_decisions()
            analysis = db.get_analysis_history()
            
            with col1:
                st.metric("Total Trades", len(trades) if trades else 0)
            
            with col2:
                st.metric("Total Decisions", len(decisions) if decisions else 0)
            
            with col3:
                st.metric("Total Analysis", len(analysis) if analysis else 0)
            
            with col4:
                # Database size
                import os
                try:
                    db_path = "data/trading_data.db"
                    if os.path.exists(db_path):
                        size_mb = os.path.getsize(db_path) / (1024 * 1024)
                        st.metric("DB Size", f"{size_mb:.2f} MB")
                    else:
                        st.metric("DB Size", "N/A")
                except:
                    st.metric("DB Size", "Error")
            
            # Database health
            st.subheader("Database Health")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if trades:
                    trades_df = pd.DataFrame(trades)
                    open_trades = len(trades_df[trades_df['status'] == 'open'])
                    closed_trades = len(trades_df[trades_df['status'] == 'closed'])
                    st.write(f"**Open Trades:** {open_trades}")
                    st.write(f"**Closed Trades:** {closed_trades}")
            
            with col2:
                if decisions:
                    decisions_df = pd.DataFrame(decisions)
                    enhanced = len(decisions_df[decisions_df['engine_type'] == 'enhanced']) if 'engine_type' in decisions_df.columns else 0
                    simple = len(decisions_df[decisions_df['engine_type'] == 'simple']) if 'engine_type' in decisions_df.columns else 0
                    st.write(f"**Enhanced AI:** {enhanced}")
                    st.write(f"**Simple AI:** {simple}")
            
            with col3:
                st.write("**Database Status:** ✅ Connected")
                st.write(f"**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Data summary table
            st.subheader("Data Summary by Symbol")
            
            if trades:
                trades_df = pd.DataFrame(trades)
                if 'symbol' in trades_df.columns:
                    summary = []
                    for symbol in trades_df['symbol'].unique():
                        sym_trades = trades_df[trades_df['symbol'] == symbol]
                        summary.append({
                            'Symbol': symbol,
                            'Total': len(sym_trades),
                            'Open': len(sym_trades[sym_trades['status'] == 'open']),
                            'Closed': len(sym_trades[sym_trades['status'] == 'closed']),
                            'Avg Volume': sym_trades['volume'].mean() if 'volume' in sym_trades.columns else 0
                        })
                    
                    summary_df = pd.DataFrame(summary)
                    st.dataframe(summary_df, width="stretch", hide_index=True)
            
        except Exception as e:
            st.error(f"Error loading system statistics: {e}")

