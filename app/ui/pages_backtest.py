"""Streamlit page for backtesting"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from app.backtest.historical_engine import HistoricalBacktestEngine
from app.backtest.data_loader import HistoricalDataLoader
from app.backtest.visualizer import get_visualizer
from app.core.logger import setup_logger

logger = setup_logger("backtest_page")


def render_backtest():
    """Render backtesting page"""
    st.title("📊 Historical Backtesting")
    
    st.markdown("""
    Test your trading strategy on historical data to evaluate performance metrics,
    optimize parameters, and validate your approach before live trading.
    """)
    
    # Configuration section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Backtest Configuration")
        
        symbol = st.selectbox(
            "Symbol",
            ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
             "BTCUSD", "ETHUSD", "XAUUSD", "US30", "NAS100"],
            index=0
        )
        
        timeframe = st.selectbox(
            "Timeframe",
            ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
            index=2  # M15 default
        )
        
        # Date range
        default_start = datetime.now() - timedelta(days=365)
        default_end = datetime.now()
        
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            max_value=datetime.now()
        )
        
        end_date = st.date_input(
            "End Date",
            value=default_end,
            max_value=datetime.now()
        )
    
    with col2:
        st.subheader("💰 Trading Parameters")
        
        initial_balance = st.number_input(
            "Initial Balance ($)",
            min_value=100,
            max_value=1000000,
            value=10000,
            step=1000
        )
        
        risk_per_trade = st.slider(
            "Risk per Trade (%)",
            min_value=0.1,
            max_value=10.0,
            value=2.0,
            step=0.1
        )
        
        max_positions = st.number_input(
            "Max Concurrent Positions",
            min_value=1,
            max_value=10,
            value=1,
            step=1
        )
        
        max_holding_bars = st.number_input(
            "Max Holding Bars",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Maximum number of bars to hold a position before timeout"
        )
    
    # Run backtest button
    if st.button("🚀 Run Backtest", type="primary", width='stretch'):
        run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.min.time()),
            initial_balance=initial_balance,
            risk_per_trade=risk_per_trade,
            max_positions=max_positions,
            max_holding_bars=max_holding_bars
        )


def run_backtest(symbol, timeframe, start_date, end_date, initial_balance, 
                 risk_per_trade, max_positions, max_holding_bars):
    """Execute backtest and display results"""
    
    with st.spinner("Loading historical data from MT5..."):
        # Load data
        loader = HistoricalDataLoader()
        data = loader.load_data(symbol, timeframe, start_date, end_date)
        
        if data is None or len(data) == 0:
            st.error("❌ Failed to load historical data. Check MT5 connection and data availability.")
            return
        
        st.success(f"✅ Loaded {len(data):,} bars from {data['time'].min()} to {data['time'].max()}")
    
    with st.spinner("Running backtest simulation..."):
        # Initialize engine
        engine = HistoricalBacktestEngine(initial_balance=initial_balance)
        
        # Run backtest
        results = engine.run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            data=data,
            max_positions=max_positions,
            risk_per_trade=risk_per_trade,
            max_holding_bars=max_holding_bars
        )
        
        if results is None:
            st.error("❌ Backtest failed")
            return
        
        st.success(f"✅ Backtest completed: {results.total_trades} trades executed")
    
    # Display results
    display_results(results)


def display_results(results):
    """Display backtest results with visualizations"""
    
    visualizer = get_visualizer()
    
    # Summary metrics
    st.markdown("---")
    st.subheader("📈 Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        initial = results.parameters.get('initial_balance', 0)
        final = results.equity_curve[-1] if results.equity_curve else initial
        pct_return = ((final - initial) / initial * 100) if initial > 0 else 0
        
        st.metric(
            "Net Profit",
            f"${results.net_profit:,.2f}",
            f"{pct_return:+.2f}%"
        )
        
        st.metric(
            "Win Rate",
            f"{results.win_rate:.1f}%"
        )
    
    with col2:
        st.metric(
            "Profit Factor",
            f"{results.profit_factor:.2f}"
        )
        
        st.metric(
            "Sharpe Ratio",
            f"{results.sharpe_ratio:.2f}"
        )
    
    with col3:
        st.metric(
            "Max Drawdown",
            f"${results.max_drawdown:,.2f}",
            f"-{results.max_drawdown_pct:.2f}%",
            delta_color="inverse"
        )
        
        st.metric(
            "Total Trades",
            f"{results.total_trades}"
        )
    
    with col4:
        st.metric(
            "Avg Win",
            f"${results.avg_win:,.2f}"
        )
        
        st.metric(
            "Avg Loss",
            f"${results.avg_loss:,.2f}"
        )
    
    # Equity curve
    st.markdown("---")
    st.subheader("💹 Equity Curve & Drawdown")
    fig_equity = visualizer.plot_equity_curve(results)
    st.plotly_chart(fig_equity, width='stretch')
    
    # Trade analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Trade Distribution")
        fig_dist = visualizer.plot_trade_distribution(results)
        st.plotly_chart(fig_dist, width='stretch')
    
    with col2:
        st.subheader("🎯 MAE vs MFE")
        fig_mae = visualizer.plot_mae_mfe(results)
        st.plotly_chart(fig_mae, width='stretch')
    
    # Monthly returns
    st.markdown("---")
    st.subheader("📅 Monthly Returns")
    fig_monthly = visualizer.plot_monthly_returns(results)
    st.plotly_chart(fig_monthly, width='stretch')
    
    # Trade breakdown
    st.markdown("---")
    st.subheader("🔍 Trade Breakdown by Strategy Type")
    
    # Strategy type breakdown
    strategy_stats = {}
    for trade in results.trades:
        strategy = trade.strategy_type if hasattr(trade, 'strategy_type') else 'SWING'
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {'count': 0, 'profit': 0.0, 'wins': 0}
        strategy_stats[strategy]['count'] += 1
        strategy_stats[strategy]['profit'] += trade.profit
        if trade.profit > 0:
            strategy_stats[strategy]['wins'] += 1
    
    strategy_df = pd.DataFrame([
        {
            'Strategy': strategy,
            'Trades': stats['count'],
            'Wins': stats['wins'],
            'Win %': f"{(stats['wins'] / stats['count'] * 100):.1f}%" if stats['count'] > 0 else "0%",
            'Total Profit': f"${stats['profit']:.2f}",
            'Avg Profit': f"${stats['profit'] / stats['count']:.2f}" if stats['count'] > 0 else "$0.00"
        }
        for strategy, stats in sorted(strategy_stats.items())
    ])
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(strategy_df, width='stretch', hide_index=True)
    
    with col2:
        if strategy_stats:
            strategy_names = list(strategy_stats.keys())
            strategy_counts = [strategy_stats[s]['count'] for s in strategy_names]
            fig_strategy = go.Figure(
                data=[go.Pie(labels=strategy_names, values=strategy_counts, hole=0.3)],
                layout=go.Layout(title="Trade Distribution by Strategy", height=350)
            )
            st.plotly_chart(fig_strategy, width='stretch')
    
    st.markdown("---")
    st.subheader("🔍 Exit Reason Breakdown")
    
    exit_reasons = {}
    for trade in results.trades:
        reason = trade.exit_reason
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    exit_df = pd.DataFrame([
        {
            'Exit Reason': reason,
            'Count': count,
            'Percentage': f"{(count / results.total_trades * 100):.1f}%"
        }
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True)
    ])
    
    st.dataframe(exit_df, width='stretch', hide_index=True)
    
    # Detailed trade log
    with st.expander("📋 Detailed Trade Log"):
        trades_df = pd.DataFrame([{
            'Strategy': t.strategy_type,  # NEW: Show strategy type
            'Entry Time': t.entry_time.strftime('%Y-%m-%d %H:%M') if t.entry_time else 'N/A',
            'Exit Time': t.exit_time.strftime('%Y-%m-%d %H:%M') if t.exit_time else 'N/A',
            'Direction': t.direction,
            'Entry Price': f"{t.entry_price:.5f}",
            'Exit Price': f"{t.exit_price:.5f}",
            'Volume': f"{t.volume:.2f}",
            'Profit': f"${t.profit:.2f}",
            'Profit %': f"{t.profit_pct:.2f}%",
            'Duration': f"{t.duration_bars} bars",
            'Exit Reason': t.exit_reason
        } for t in results.trades])
        
        st.dataframe(trades_df, width='stretch', hide_index=True)
    
    # Export buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export trades to CSV
        trades_csv = trades_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Trades CSV",
            data=trades_csv,
            file_name=f"backtest_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export equity curve
        equity_df = pd.DataFrame({
            'Timestamp': results.equity_timestamps,
            'Equity': results.equity_curve,
            'Drawdown': results.drawdown_curve
        })
        equity_csv = equity_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Equity CSV",
            data=equity_csv,
            file_name=f"backtest_equity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Generate text report
        report = visualizer.generate_report(results)
        st.download_button(
            label="📥 Download Report",
            data=report,
            file_name=f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

