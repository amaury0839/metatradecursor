"""Enhanced Logs page - All logs from database"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from app.core.database import get_database_manager
from app.core.logger import setup_logger

logger = setup_logger("logs_page")


def render_logs():
    """Render all database logs and audit trail"""
    
    st.title("📋 Complete Logs & Audit Trail")
    
    db = get_database_manager()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analysis Logs",
        "🤖 AI Decisions",
        "💰 Trades",
        "📈 Performance"
    ])
    
    # ============= TAB 1: Analysis Logs =============
    with tab1:
        st.header("Analysis Logs - Complete Record")
        
        try:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                days = st.slider("Days back", 1, 30, 7, key="analysis_days")
            
            with col2:
                symbol_list = list(set([a.get('symbol') for a in db.get_analysis_history(days=30) if a.get('symbol')]))
                symbol = st.selectbox(
                    "Symbol",
                    options=["ALL"] + sorted(symbol_list),
                    key="analysis_symbol"
                )
            
            with col3:
                limit = st.number_input("Max records", 10, 500, 100, key="analysis_limit")
            
            # Get data
            analysis = db.get_analysis_history(days=days)
            
            if analysis:
                df = pd.DataFrame(analysis)
                
                # Apply symbol filter
                if symbol != "ALL":
                    df = df[df['symbol'] == symbol]
                
                df = df.head(limit).copy()
                
                # Metrics
                st.subheader("Analysis Metrics")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Records", len(df))
                
                with col2:
                    if 'tech_rsi' in df.columns and len(df) > 0:
                        avg_rsi = pd.to_numeric(df['tech_rsi'], errors='coerce').mean()
                        st.metric("Avg RSI", f"{avg_rsi:.1f}" if not pd.isna(avg_rsi) else "N/A")
                    else:
                        st.metric("Avg RSI", "N/A")
                
                with col3:
                    if 'sentiment_score' in df.columns and len(df) > 0:
                        avg_sent = pd.to_numeric(df['sentiment_score'], errors='coerce').mean()
                        st.metric("Avg Sentiment", f"{avg_sent:.2f}" if not pd.isna(avg_sent) else "N/A")
                    else:
                        st.metric("Avg Sentiment", "N/A")
                
                with col4:
                    if 'confidence' in df.columns and len(df) > 0:
                        avg_conf = pd.to_numeric(df['confidence'], errors='coerce').mean()
                        st.metric("Avg Confidence", f"{avg_conf:.1f}%" if not pd.isna(avg_conf) else "N/A")
                    else:
                        st.metric("Avg Confidence", "N/A")
                
                with col5:
                    if 'symbol' in df.columns:
                        symbols_count = df['symbol'].nunique()
                        st.metric("Symbols", symbols_count)
                    else:
                        st.metric("Symbols", "N/A")
                
                st.divider()
                
                # Table
                st.subheader("Analysis Records")
                
                cols_to_show = [
                    'timestamp', 'symbol', 'tech_signal', 'tech_rsi', 
                    'sentiment_score', 'combined_score', 'final_signal', 'confidence'
                ]
                available_cols = [col for col in cols_to_show if col in df.columns]
                
                if len(available_cols) > 0:
                    st.dataframe(
                        df[available_cols].sort_values('timestamp', ascending=False),
                        width="stretch",
                        height=500
                    )
                else:
                    st.warning("No columns to display")
                
            else:
                st.info("No analysis records found for selected period")
                
        except Exception as e:
            st.error(f"Error loading analysis logs: {e}")
            logger.error(f"Analysis logs error: {e}", exc_info=True)
    
    # ============= TAB 2: AI Decisions =============
    with tab2:
        st.header("AI Decisions Log - Decision History")
        
        try:
            # Filters
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                days = st.slider("Days back", 1, 30, 7, key="decision_days")
            
            with col2:
                engine = st.selectbox(
                    "Engine Type",
                    options=["ALL", "enhanced", "simple"],
                    key="decision_engine"
                )
            
            with col3:
                symbol_list = list(set([d.get('symbol') for d in db.get_ai_decisions(days=30) if d.get('symbol')]))
                symbol = st.selectbox(
                    "Symbol",
                    options=["ALL"] + sorted(symbol_list),
                    key="decision_symbol"
                )
            
            with col4:
                limit = st.number_input("Max records", 10, 500, 100, key="decision_limit")
            
            # Get data
            decisions = db.get_ai_decisions(days=days)
            
            if decisions:
                df = pd.DataFrame(decisions)
                
                # Apply filters
                if engine != "ALL":
                    df = df[df['engine_type'] == engine]
                
                if symbol != "ALL":
                    df = df[df['symbol'] == symbol]
                
                df = df.head(limit).copy()
                
                # Metrics
                st.subheader("Decision Metrics")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Decisions", len(df))
                
                with col2:
                    if 'engine_type' in df.columns:
                        enhanced_count = len(df[df['engine_type'] == 'enhanced'])
                        st.metric("Enhanced AI", enhanced_count)
                    else:
                        st.metric("Enhanced AI", "N/A")
                
                with col3:
                    if 'engine_type' in df.columns:
                        simple_count = len(df[df['engine_type'] == 'simple'])
                        st.metric("Simple AI", simple_count)
                    else:
                        st.metric("Simple AI", "N/A")
                
                with col4:
                    if 'confidence' in df.columns and len(df) > 0:
                        avg_conf = pd.to_numeric(df['confidence'], errors='coerce').mean()
                        st.metric("Avg Confidence", f"{avg_conf:.1f}%" if not pd.isna(avg_conf) else "N/A")
                    else:
                        st.metric("Avg Confidence", "N/A")
                
                with col5:
                    if 'action' in df.columns:
                        buy_count = len(df[df['action'] == 'BUY'])
                        st.metric("BUY Actions", buy_count)
                    else:
                        st.metric("BUY Actions", "N/A")
                
                st.divider()
                
                # Table
                st.subheader("Decision Records")
                
                cols_to_show = [
                    'timestamp', 'symbol', 'action', 'confidence', 
                    'engine_type', 'reasoning', 'executed'
                ]
                available_cols = [col for col in cols_to_show if col in df.columns]
                
                if len(available_cols) > 0:
                    st.dataframe(
                        df[available_cols].sort_values('timestamp', ascending=False),
                        width="stretch",
                        height=500
                    )
                else:
                    st.warning("No columns to display")
                
            else:
                st.info("No decision records found for selected period")
                
        except Exception as e:
            st.error(f"Error loading decision logs: {e}")
            logger.error(f"Decision logs error: {e}", exc_info=True)
    
    # ============= TAB 3: Trades =============
    with tab3:
        st.header("Trades Log - Complete Trade History")
        
        try:
            # Filters
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                days = st.slider("Days back", 1, 90, 30, key="trade_days")
            
            with col2:
                status = st.selectbox(
                    "Status",
                    options=["ALL", "open", "closed"],
                    key="trade_status"
                )
            
            with col3:
                symbol_list = list(set([t.get('symbol') for t in db.get_trades(days=30) if t.get('symbol')]))
                symbol = st.selectbox(
                    "Symbol",
                    options=["ALL"] + sorted(symbol_list),
                    key="trade_symbol"
                )
            
            with col4:
                limit = st.number_input("Max records", 10, 500, 100, key="trade_limit")
            
            # Get data
            trades = db.get_trades(days=days)
            
            if trades:
                df = pd.DataFrame(trades)
                
                # Apply filters
                if status != "ALL":
                    df = df[df['status'] == status]
                
                if symbol != "ALL":
                    df = df[df['symbol'] == symbol]
                
                df = df.head(limit).copy()
                
                # Metrics
                st.subheader("Trade Metrics")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Trades", len(df))
                
                with col2:
                    if 'status' in df.columns:
                        open_count = len(df[df['status'] == 'open'])
                        st.metric("Open", open_count)
                    else:
                        st.metric("Open", "N/A")
                
                with col3:
                    if 'status' in df.columns:
                        closed_count = len(df[df['status'] == 'closed'])
                        st.metric("Closed", closed_count)
                    else:
                        st.metric("Closed", "N/A")
                
                with col4:
                    if 'profit' in df.columns and len(df) > 0:
                        total_pnl = pd.to_numeric(df['profit'], errors='coerce').sum()
                        st.metric("Total P&L", f"${total_pnl:.2f}")
                    else:
                        st.metric("Total P&L", "N/A")
                
                with col5:
                    if 'profit' in df.columns and 'status' in df.columns:
                        closed_df = df[df['status'] == 'closed']
                        if len(closed_df) > 0:
                            wins = len(closed_df[pd.to_numeric(closed_df['profit'], errors='coerce') > 0])
                            win_rate = wins / len(closed_df) * 100
                            st.metric("Win Rate", f"{win_rate:.1f}%")
                        else:
                            st.metric("Win Rate", "N/A")
                    else:
                        st.metric("Win Rate", "N/A")
                
                st.divider()
                
                # Table
                st.subheader("Trade Records")
                
                cols_to_show = [
                    'open_timestamp', 'ticket', 'symbol', 'type', 'volume',
                    'open_price', 'close_price', 'profit', 'commission', 'status'
                ]
                available_cols = [col for col in cols_to_show if col in df.columns]
                
                if len(available_cols) > 0:
                    st.dataframe(
                        df[available_cols].sort_values('open_timestamp', ascending=False),
                        width="stretch",
                        height=500
                    )
                else:
                    st.warning("No columns to display")
                
            else:
                st.info("No trade records found for selected period")
                
        except Exception as e:
            st.error(f"Error loading trade logs: {e}")
            logger.error(f"Trade logs error: {e}", exc_info=True)
    
    # ============= TAB 4: Performance =============
    with tab4:
        st.header("Performance Summary")
        
        try:
            performance = db.get_performance_summary(days=30)
            
            if performance:
                # Metrics
                st.subheader("Performance Metrics (Last 30 Days)")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    total = performance.get('total_trades', 0)
                    winners = performance.get('winning_trades', 0)
                    st.metric(
                        "Total Trades",
                        total,
                        delta=f"{winners} winners"
                    )
                
                with col2:
                    win_rate = performance.get('win_rate', 0)
                    st.metric(
                        "Win Rate",
                        f"{win_rate:.1f}%"
                    )
                
                with col3:
                    pf = performance.get('profit_factor', 0)
                    st.metric(
                        "Profit Factor",
                        f"{pf:.2f}"
                    )
                
                with col4:
                    pnl = performance.get('net_profit', 0)
                    delta_text = "Profit" if pnl > 0 else ("Loss" if pnl < 0 else "Neutral")
                    st.metric(
                        "Net P&L",
                        f"${pnl:.2f}",
                        delta=delta_text
                    )
                
                with col5:
                    gp = performance.get('gross_profit', 0)
                    gl = performance.get('gross_loss', 0)
                    st.metric(
                        "Gross Profit",
                        f"${gp:.2f}",
                        delta=f"-${gl:.2f} loss"
                    )
                
                st.divider()
                
                # Details
                st.subheader("Detailed Performance")
                
                perf_data = {
                    'Metric': [
                        'Total Trades',
                        'Winning Trades',
                        'Losing Trades',
                        'Win Rate',
                        'Gross Profit',
                        'Gross Loss',
                        'Net P&L',
                        'Average Profit',
                        'Profit Factor'
                    ],
                    'Value': [
                        performance.get('total_trades', 0),
                        performance.get('winning_trades', 0),
                        performance.get('losing_trades', 0),
                        f"{performance.get('win_rate', 0):.2f}%",
                        f"${performance.get('gross_profit', 0):.2f}",
                        f"${performance.get('gross_loss', 0):.2f}",
                        f"${performance.get('net_profit', 0):.2f}",
                        f"${performance.get('avg_profit', 0):.2f}",
                        f"{performance.get('profit_factor', 0):.2f}"
                    ]
                }
                
                perf_df = pd.DataFrame(perf_data)
                st.dataframe(perf_df, width="stretch", hide_index=True)
                
            else:
                st.info("No performance data available yet")
                
        except Exception as e:
            st.error(f"Error loading performance data: {e}")
            logger.error(f"Performance data error: {e}", exc_info=True)

