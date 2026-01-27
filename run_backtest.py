"""Standalone backtest runner script"""

import argparse
from datetime import datetime, timedelta
import pandas as pd
from app.backtest.historical_engine import HistoricalBacktestEngine
from app.backtest.data_loader import HistoricalDataLoader
from app.backtest.visualizer import get_visualizer
from app.core.logger import setup_logger

logger = setup_logger("backtest_runner")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run historical backtest')
    
    parser.add_argument('--symbol', type=str, required=True,
                        help='Trading symbol (e.g., EURUSD)')
    parser.add_argument('--timeframe', type=str, default='M15',
                        choices=['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'],
                        help='Timeframe')
    parser.add_argument('--start', type=str, required=True,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True,
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial-balance', type=float, default=10000,
                        help='Initial account balance')
    parser.add_argument('--risk-per-trade', type=float, default=2.0,
                        help='Risk per trade (%)')
    parser.add_argument('--max-positions', type=int, default=1,
                        help='Maximum concurrent positions')
    parser.add_argument('--max-holding-bars', type=int, default=100,
                        help='Maximum bars to hold a position')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file for results (CSV)')
    parser.add_argument('--plot', action='store_true',
                        help='Generate and save plots')
    
    return parser.parse_args()


def main():
    """Main backtest execution"""
    args = parse_args()
    
    logger.info("=" * 60)
    logger.info("STARTING BACKTEST")
    logger.info("=" * 60)
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Timeframe: {args.timeframe}")
    logger.info(f"Period: {args.start} to {args.end}")
    logger.info(f"Initial Balance: ${args.initial_balance:,.2f}")
    logger.info(f"Risk per Trade: {args.risk_per_trade}%")
    logger.info(f"Max Positions: {args.max_positions}")
    logger.info("=" * 60)
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return
    
    # Load historical data
    logger.info("Loading historical data from MT5...")
    loader = HistoricalDataLoader()
    data = loader.load_data(args.symbol, args.timeframe, start_date, end_date)
    
    if data is None or len(data) == 0:
        logger.error("Failed to load historical data or no data available")
        return
    
    logger.info(f"Loaded {len(data):,} bars")
    logger.info(f"Date range: {data['time'].min()} to {data['time'].max()}")
    
    # Initialize backtest engine
    logger.info("\nInitializing backtest engine...")
    engine = HistoricalBacktestEngine(initial_balance=args.initial_balance)
    
    # Run backtest
    logger.info("\nRunning backtest simulation...")
    results = engine.run_backtest(
        symbol=args.symbol,
        timeframe=args.timeframe,
        data=data,
        max_positions=args.max_positions,
        risk_per_trade=args.risk_per_trade,
        max_holding_bars=args.max_holding_bars
    )
    
    # Generate report
    logger.info("\n" + "=" * 60)
    logger.info("BACKTEST COMPLETED")
    logger.info("=" * 60)
    
    visualizer = get_visualizer()
    report = visualizer.generate_report(results)
    print(report)
    
    # Save results to CSV
    if args.output:
        logger.info(f"\nSaving results to {args.output}...")
        trades_df = pd.DataFrame([{
            'entry_time': t.entry_time,
            'exit_time': t.exit_time,
            'symbol': t.symbol,
            'direction': t.direction,
            'entry_price': t.entry_price,
            'exit_price': t.exit_price,
            'volume': t.volume,
            'sl_price': t.sl_price,
            'tp_price': t.tp_price,
            'profit': t.profit,
            'profit_pct': t.profit_pct,
            'mae': t.max_adverse_excursion,
            'mfe': t.max_favorable_excursion,
            'duration_bars': t.duration_bars,
            'exit_reason': t.exit_reason
        } for t in results.trades])
        
        trades_df.to_csv(args.output, index=False)
        logger.info(f"Saved {len(trades_df)} trades to {args.output}")
        
        # Save equity curve
        equity_file = args.output.replace('.csv', '_equity.csv')
        equity_df = pd.DataFrame({
            'timestamp': results.equity_timestamps,
            'equity': results.equity_curve,
            'drawdown': results.drawdown_curve
        })
        equity_df.to_csv(equity_file, index=False)
        logger.info(f"Saved equity curve to {equity_file}")
    
    # Generate plots
    if args.plot:
        logger.info("\nGenerating plots...")
        try:
            import plotly.io as pio
            
            # Equity curve
            fig_equity = visualizer.plot_equity_curve(results)
            pio.write_html(fig_equity, 'backtest_equity.html')
            logger.info("Saved equity plot to backtest_equity.html")
            
            # Trade distribution
            fig_dist = visualizer.plot_trade_distribution(results)
            pio.write_html(fig_dist, 'backtest_distribution.html')
            logger.info("Saved distribution plot to backtest_distribution.html")
            
            # MAE/MFE
            fig_mae = visualizer.plot_mae_mfe(results)
            pio.write_html(fig_mae, 'backtest_mae_mfe.html')
            logger.info("Saved MAE/MFE plot to backtest_mae_mfe.html")
            
            # Monthly returns
            fig_monthly = visualizer.plot_monthly_returns(results)
            pio.write_html(fig_monthly, 'backtest_monthly.html')
            logger.info("Saved monthly returns plot to backtest_monthly.html")
            
        except Exception as e:
            logger.error(f"Failed to generate plots: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("BACKTEST FINISHED")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
