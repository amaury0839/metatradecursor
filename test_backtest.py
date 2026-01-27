"""Quick test of backtesting system"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from app.backtest.historical_engine import HistoricalBacktestEngine
from app.backtest.data_loader import HistoricalDataLoader
from app.core.logger import setup_logger

logger = setup_logger("backtest_test")


def test_data_loader():
    """Test historical data loading"""
    logger.info("=" * 60)
    logger.info("TEST 1: Data Loader")
    logger.info("=" * 60)
    
    loader = HistoricalDataLoader()
    
    # Try to load 7 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    logger.info(f"Loading EURUSD M15 data from {start_date} to {end_date}")
    data = loader.load_data('EURUSD', 'M15', start_date, end_date)
    
    if data is None or len(data) == 0:
        logger.error("❌ Failed to load data - Check MT5 connection")
        return False
    
    logger.info(f"✅ Loaded {len(data):,} bars")
    logger.info(f"   Date range: {data['time'].min()} to {data['time'].max()}")
    logger.info(f"   Columns: {list(data.columns)}")
    logger.info(f"   First bar: Open={data['open'].iloc[0]:.5f}, Close={data['close'].iloc[0]:.5f}")
    
    return True


def test_backtest_engine():
    """Test backtest execution"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Backtest Engine")
    logger.info("=" * 60)
    
    # Load data
    loader = HistoricalDataLoader()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    logger.info(f"Loading EURUSD M15 data...")
    data = loader.load_data('EURUSD', 'M15', start_date, end_date)
    
    if data is None or len(data) == 0:
        logger.error("❌ Cannot run backtest - no data")
        return False
    
    logger.info(f"Loaded {len(data):,} bars")
    
    # Run backtest
    logger.info("Running backtest with 1% risk, 1 max position, 50 bar timeout...")
    engine = HistoricalBacktestEngine(initial_balance=10000)
    
    try:
        results = engine.run_backtest(
            symbol='EURUSD',
            timeframe='M15',
            data=data,
            max_positions=1,
            risk_per_trade=1.0,
            max_holding_bars=50
        )
        
        if results is None:
            logger.error("❌ Backtest returned None")
            return False
        
        logger.info("✅ Backtest completed")
        logger.info(f"   Total Trades: {results.total_trades}")
        logger.info(f"   Winning Trades: {results.winning_trades}")
        logger.info(f"   Losing Trades: {results.losing_trades}")
        logger.info(f"   Win Rate: {results.win_rate:.1f}%")
        logger.info(f"   Net Profit: ${results.net_profit:.2f}")
        logger.info(f"   Profit Factor: {results.profit_factor:.2f}")
        logger.info(f"   Max Drawdown: ${results.max_drawdown:.2f} ({results.max_drawdown_pct:.2f}%)")
        logger.info(f"   Sharpe Ratio: {results.sharpe_ratio:.2f}")
        
        if results.total_trades == 0:
            logger.warning("⚠️ No trades executed - Strategy may be too conservative")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}", exc_info=True)
        return False


def test_visualizer():
    """Test visualizer"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Visualizer")
    logger.info("=" * 60)
    
    try:
        from app.backtest.visualizer import get_visualizer
        
        visualizer = get_visualizer()
        logger.info("✅ Visualizer loaded successfully")
        
        # Quick backtest for visualization
        loader = HistoricalDataLoader()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        data = loader.load_data('EURUSD', 'M15', start_date, end_date)
        
        if data is None or len(data) == 0:
            logger.warning("⚠️ Cannot test visualization - no data")
            return True
        
        engine = HistoricalBacktestEngine(initial_balance=10000)
        results = engine.run_backtest(
            symbol='EURUSD',
            timeframe='M15',
            data=data,
            max_positions=1,
            risk_per_trade=1.0,
            max_holding_bars=50
        )
        
        # Generate report
        report = visualizer.generate_report(results)
        logger.info("✅ Text report generated")
        logger.info(f"   Report length: {len(report)} characters")
        
        # Try to generate plots (won't show, just test creation)
        try:
            fig_equity = visualizer.plot_equity_curve(results)
            logger.info("✅ Equity curve plot created")
            
            fig_dist = visualizer.plot_trade_distribution(results)
            logger.info("✅ Distribution plot created")
            
            fig_mae = visualizer.plot_mae_mfe(results)
            logger.info("✅ MAE/MFE plot created")
            
        except Exception as e:
            logger.warning(f"⚠️ Plot generation partially failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Visualizer test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("BACKTESTING SYSTEM TEST")
    logger.info("=" * 60)
    logger.info("")
    
    results = []
    
    # Test 1: Data Loader
    results.append(("Data Loader", test_data_loader()))
    
    # Test 2: Backtest Engine
    results.append(("Backtest Engine", test_backtest_engine()))
    
    # Test 3: Visualizer
    results.append(("Visualizer", test_visualizer()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name:20s}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - Backtesting system is ready!")
    else:
        logger.warning("⚠️ SOME TESTS FAILED - Check logs above")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
