"""Example backtest script - Demonstrates how to use the backtesting system"""

from datetime import datetime, timedelta
from app.backtest.historical_engine import HistoricalBacktestEngine
from app.backtest.data_loader import HistoricalDataLoader
from app.backtest.visualizer import get_visualizer


def example_simple_backtest():
    """Simple backtest example"""
    print("=" * 60)
    print("SIMPLE BACKTEST EXAMPLE")
    print("=" * 60)
    
    # Configuration
    symbol = "EURUSD"
    timeframe = "M15"
    initial_balance = 10000
    risk_per_trade = 2.0
    
    # Date range: Last 3 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"\nSymbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Initial Balance: ${initial_balance:,.2f}")
    print(f"Risk per Trade: {risk_per_trade}%")
    
    # Load historical data
    print("\nLoading historical data...")
    loader = HistoricalDataLoader()
    data = loader.load_data(symbol, timeframe, start_date, end_date)
    
    if data is None or len(data) == 0:
        print("ERROR: Failed to load data")
        return
    
    print(f"Loaded {len(data):,} bars")
    
    # Run backtest
    print("\nRunning backtest...")
    engine = HistoricalBacktestEngine(initial_balance=initial_balance)
    
    results = engine.run_backtest(
        symbol=symbol,
        timeframe=timeframe,
        data=data,
        max_positions=1,
        risk_per_trade=risk_per_trade,
        max_holding_bars=100
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    visualizer = get_visualizer()
    report = visualizer.generate_report(results)
    print(report)
    
    # Save to CSV
    print("\nSaving results to CSV...")
    import pandas as pd
    
    trades_df = pd.DataFrame([{
        'entry_time': t.entry_time,
        'exit_time': t.exit_time,
        'symbol': t.symbol,
        'direction': t.direction,
        'entry_price': t.entry_price,
        'exit_price': t.exit_price,
        'volume': t.volume,
        'profit': t.profit,
        'profit_pct': t.profit_pct,
        'exit_reason': t.exit_reason
    } for t in results.trades])
    
    filename = f"backtest_{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    trades_df.to_csv(filename, index=False)
    print(f"Saved to {filename}")
    
    print("\nDone!")


def example_multi_symbol_backtest():
    """Multi-symbol backtest example"""
    print("=" * 60)
    print("MULTI-SYMBOL BACKTEST EXAMPLE")
    print("=" * 60)
    
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    timeframe = "M15"
    initial_balance = 10000
    
    # Date range: Last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print(f"\nSymbols: {', '.join(symbols)}")
    print(f"Timeframe: {timeframe}")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Load data for all symbols
    print("\nLoading historical data...")
    loader = HistoricalDataLoader()
    data_dict = loader.load_multiple_symbols(symbols, timeframe, start_date, end_date)
    
    # Run backtest for each symbol
    all_results = {}
    
    for symbol in symbols:
        print(f"\n--- Running backtest for {symbol} ---")
        
        data = data_dict.get(symbol)
        if data is None or len(data) == 0:
            print(f"ERROR: No data for {symbol}")
            continue
        
        print(f"Loaded {len(data):,} bars")
        
        engine = HistoricalBacktestEngine(initial_balance=initial_balance)
        results = engine.run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            data=data,
            max_positions=1,
            risk_per_trade=2.0,
            max_holding_bars=100
        )
        
        all_results[symbol] = results
        
        print(f"  Total Trades: {results.total_trades}")
        print(f"  Win Rate: {results.win_rate:.1f}%")
        print(f"  Net Profit: ${results.net_profit:,.2f}")
        print(f"  Profit Factor: {results.profit_factor:.2f}")
    
    # Summary comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    
    import pandas as pd
    
    summary = []
    for symbol, results in all_results.items():
        summary.append({
            'Symbol': symbol,
            'Trades': results.total_trades,
            'Win Rate': f"{results.win_rate:.1f}%",
            'Net Profit': f"${results.net_profit:,.2f}",
            'Profit Factor': f"{results.profit_factor:.2f}",
            'Max DD': f"-{results.max_drawdown_pct:.2f}%",
            'Sharpe': f"{results.sharpe_ratio:.2f}"
        })
    
    df = pd.DataFrame(summary)
    print(df.to_string(index=False))
    
    print("\nDone!")


def example_parameter_comparison():
    """Compare different risk parameters"""
    print("=" * 60)
    print("PARAMETER COMPARISON EXAMPLE")
    print("=" * 60)
    
    symbol = "EURUSD"
    timeframe = "M15"
    initial_balance = 10000
    
    # Test different risk levels
    risk_levels = [1.0, 2.0, 3.0, 5.0]
    
    # Date range: Last 3 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"\nSymbol: {symbol}")
    print(f"Testing risk levels: {risk_levels}")
    
    # Load data once
    print("\nLoading historical data...")
    loader = HistoricalDataLoader()
    data = loader.load_data(symbol, timeframe, start_date, end_date)
    
    if data is None or len(data) == 0:
        print("ERROR: Failed to load data")
        return
    
    print(f"Loaded {len(data):,} bars")
    
    # Run backtest for each risk level
    results_by_risk = {}
    
    for risk in risk_levels:
        print(f"\n--- Testing {risk}% risk per trade ---")
        
        engine = HistoricalBacktestEngine(initial_balance=initial_balance)
        results = engine.run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            data=data,
            max_positions=1,
            risk_per_trade=risk,
            max_holding_bars=100
        )
        
        results_by_risk[risk] = results
        
        print(f"  Net Profit: ${results.net_profit:,.2f}")
        print(f"  Win Rate: {results.win_rate:.1f}%")
        print(f"  Max DD: -{results.max_drawdown_pct:.2f}%")
    
    # Comparison table
    print("\n" + "=" * 60)
    print("RISK PARAMETER COMPARISON")
    print("=" * 60)
    
    import pandas as pd
    
    comparison = []
    for risk, results in results_by_risk.items():
        comparison.append({
            'Risk%': f"{risk}%",
            'Trades': results.total_trades,
            'Win Rate': f"{results.win_rate:.1f}%",
            'Net Profit': f"${results.net_profit:,.2f}",
            'Return%': f"{(results.net_profit/initial_balance*100):+.2f}%",
            'Max DD%': f"-{results.max_drawdown_pct:.2f}%",
            'Sharpe': f"{results.sharpe_ratio:.2f}"
        })
    
    df = pd.DataFrame(comparison)
    print(df.to_string(index=False))
    
    # Best result
    best_risk = max(results_by_risk.items(), key=lambda x: x[1].sharpe_ratio)
    print(f"\n✅ Best Sharpe Ratio: {best_risk[0]}% risk (Sharpe: {best_risk[1].sharpe_ratio:.2f})")
    
    print("\nDone!")


if __name__ == "__main__":
    print("BACKTESTING EXAMPLES")
    print("=" * 60)
    print("Choose an example:")
    print("1. Simple backtest (single symbol)")
    print("2. Multi-symbol comparison")
    print("3. Risk parameter optimization")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        example_simple_backtest()
    elif choice == "2":
        example_multi_symbol_backtest()
    elif choice == "3":
        example_parameter_comparison()
    else:
        print("Invalid choice. Running simple example...")
        example_simple_backtest()
