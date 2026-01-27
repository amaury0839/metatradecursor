# 🧪 Backtesting System - Complete Guide

## 📖 Overview

The backtesting system allows you to test your trading strategy on historical data to evaluate performance metrics, optimize parameters, and validate your approach before live trading.

## ✨ Features

- **Historical Simulation**: Test strategies on real MT5 historical data
- **Comprehensive Metrics**: Win rate, profit factor, Sharpe ratio, Sortino ratio, max drawdown, MAE/MFE
- **Equity Curve Tracking**: Visualize account growth and drawdown over time
- **Trade Analysis**: Detailed breakdown by exit reason, duration, profit distribution
- **Multi-Symbol Support**: Compare performance across different instruments
- **Parameter Optimization**: Test different risk levels, stop loss/take profit settings
- **Multiple Interfaces**: Streamlit UI, standalone CLI, Python API
- **Export Capabilities**: CSV, JSON, HTML plots

## 🚀 Quick Start

### 1. Using Streamlit UI

```bash
python run_ui_improved.py
```

1. Navigate to the **🧪 Backtest** tab
2. Configure:
   - Symbol (e.g., EURUSD)
   - Timeframe (M15 recommended)
   - Date range (last 3-12 months)
   - Initial balance
   - Risk per trade (2.0% default)
3. Click **🚀 Run Backtest**
4. View results with interactive charts
5. Download CSV/reports

### 2. Using CLI Script

```bash
python run_backtest.py --symbol EURUSD --timeframe M15 --start 2024-01-01 --end 2024-12-31 --initial-balance 10000 --risk-per-trade 2.0 --plot
```

**Parameters:**
- `--symbol`: Trading symbol (required)
- `--timeframe`: M1, M5, M15, M30, H1, H4, D1 (default: M15)
- `--start`: Start date YYYY-MM-DD (required)
- `--end`: End date YYYY-MM-DD (required)
- `--initial-balance`: Initial account balance (default: 10000)
- `--risk-per-trade`: Risk percentage per trade (default: 2.0)
- `--max-positions`: Max concurrent positions (default: 1)
- `--max-holding-bars`: Timeout in bars (default: 100)
- `--output`: CSV output file (optional)
- `--plot`: Generate HTML plots (optional)

**Example Output:**
```
========================================
BACKTEST RESULTS REPORT
========================================

Period: 2024-01-01 to 2024-12-31
Symbol: EURUSD
Timeframe: M15
Total Bars: 25,000

----------------------------------------
PERFORMANCE SUMMARY
----------------------------------------
Initial Balance:    $10,000.00
Final Equity:       $12,450.00
Net Profit:         +$2,450.00
Return:             +24.50%

----------------------------------------
TRADE STATISTICS
----------------------------------------
Total Trades:       85
Winning Trades:     52 (61.2%)
Losing Trades:      33

Gross Profit:       $5,280.00
Gross Loss:         $2,830.00
Profit Factor:      1.87

Average Win:        $101.54
Average Loss:       $85.76
Average Trade:      $28.82

Largest Win:        $420.00
Largest Loss:       $180.00

----------------------------------------
RISK METRICS
----------------------------------------
Max Drawdown:       $680.00 (6.80%)
Sharpe Ratio:       1.42
Sortino Ratio:      2.15
```

### 3. Using Python API

```python
from datetime import datetime, timedelta
from app.backtest.historical_engine import HistoricalBacktestEngine
from app.backtest.data_loader import HistoricalDataLoader

# Load historical data
loader = HistoricalDataLoader()
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

data = loader.load_data('EURUSD', 'M15', start_date, end_date)

# Run backtest
engine = HistoricalBacktestEngine(initial_balance=10000)
results = engine.run_backtest(
    symbol='EURUSD',
    timeframe='M15',
    data=data,
    max_positions=1,
    risk_per_trade=2.0,
    max_holding_bars=100
)

# Access metrics
print(f"Net Profit: ${results.net_profit:.2f}")
print(f"Win Rate: {results.win_rate:.1f}%")
print(f"Profit Factor: {results.profit_factor:.2f}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown_pct:.2f}%")

# Access trades
for trade in results.trades:
    print(f"{trade.entry_time} {trade.direction} {trade.symbol} @ {trade.entry_price} -> {trade.exit_price} = ${trade.profit:.2f}")
```

## 📊 Understanding Metrics

### Win Rate
Percentage of winning trades out of total trades. Higher is better, but doesn't account for trade size.

**Formula:** `(Winning Trades / Total Trades) × 100`

**Good Values:**
- 50-60%: Acceptable for trending strategies
- 60-70%: Good performance
- 70%+: Excellent (but watch for curve fitting)

### Profit Factor
Ratio of gross profit to gross loss. Measures strategy efficiency.

**Formula:** `Gross Profit / Gross Loss`

**Interpretation:**
- <1.0: Losing strategy
- 1.0-1.5: Break-even to marginal
- 1.5-2.0: Good strategy
- 2.0-3.0: Very good
- 3.0+: Excellent (verify not overfit)

### Sharpe Ratio
Risk-adjusted return metric. Measures excess return per unit of risk.

**Formula:** `(Average Return - Risk-Free Rate) / Standard Deviation of Returns`

**Interpretation:**
- <0: Negative returns
- 0-1: Sub-optimal
- 1-2: Good
- 2-3: Very good
- 3+: Exceptional

### Sortino Ratio
Similar to Sharpe but only penalizes downside volatility.

**Formula:** `(Average Return - Risk-Free Rate) / Standard Deviation of Negative Returns`

**Higher than Sharpe = Strategy has positive skew (good)**

### Max Drawdown
Largest peak-to-trough decline in equity. Measures worst-case scenario.

**Formula:** `(Trough Value - Peak Value) / Peak Value × 100`

**Acceptable Levels:**
- <10%: Conservative
- 10-20%: Moderate
- 20-30%: Aggressive
- 30%+: Very aggressive (risky)

### MAE (Max Adverse Excursion)
Worst price movement against the position before exit.

**Use:** Optimize stop loss placement. If MAE consistently smaller than SL, tighten stops.

### MFE (Max Favorable Excursion)
Best price movement in favor before exit.

**Use:** Optimize take profit placement. If MFE consistently larger than TP, widen targets.

## 🔧 Advanced Usage

### Multi-Symbol Comparison

```python
from app.backtest.data_loader import HistoricalDataLoader
from app.backtest.historical_engine import HistoricalBacktestEngine

symbols = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]
loader = HistoricalDataLoader()

# Load all symbols
data_dict = loader.load_multiple_symbols(symbols, 'M15', start_date, end_date)

# Test each symbol
results = {}
for symbol in symbols:
    engine = HistoricalBacktestEngine(initial_balance=10000)
    results[symbol] = engine.run_backtest(
        symbol=symbol,
        timeframe='M15',
        data=data_dict[symbol],
        max_positions=1,
        risk_per_trade=2.0
    )

# Compare
for symbol, result in results.items():
    print(f"{symbol}: {result.profit_factor:.2f} PF, {result.win_rate:.1f}% WR")
```

### Parameter Optimization

```python
# Test different risk levels
risk_levels = [1.0, 1.5, 2.0, 2.5, 3.0]

best_sharpe = -999
best_params = {}

for risk in risk_levels:
    results = engine.run_backtest(
        symbol='EURUSD',
        timeframe='M15',
        data=data,
        risk_per_trade=risk
    )
    
    if results.sharpe_ratio > best_sharpe:
        best_sharpe = results.sharpe_ratio
        best_params = {'risk': risk}

print(f"Optimal risk: {best_params['risk']}% (Sharpe: {best_sharpe:.2f})")
```

### Save/Load Historical Data

```python
# Download and save
data = loader.load_data('EURUSD', 'M15', start_date, end_date)
loader.save_to_csv(data, 'eurusd_m15_historical.csv')

# Load from CSV (faster for repeated backtests)
data = loader.load_from_csv('eurusd_m15_historical.csv')
```

## 📈 Visualization

The backtesting system generates several interactive charts:

1. **Equity Curve**: Account growth over time
2. **Drawdown Chart**: Visualize risk periods
3. **Trade Distribution**: Histogram of profit/loss
4. **Monthly Returns Heatmap**: Performance by month/year
5. **MAE vs MFE Scatter**: Stop loss/take profit optimization

Access via:
- Streamlit UI (automatic)
- CLI with `--plot` flag (saves HTML files)
- Python API using `visualizer.plot_*()` methods

## 🎯 Best Practices

### 1. Use Sufficient Data
- **Minimum:** 3 months
- **Recommended:** 6-12 months
- **Ideal:** 2+ years

### 2. Test Multiple Timeframes
- M15 for intraday scalping
- H1/H4 for swing trading
- D1 for position trading

### 3. Avoid Curve Fitting
- If metrics are "too good" (>90% win rate, >5 PF), likely overfit
- Test on out-of-sample data
- Walk-forward validation recommended

### 4. Consider Slippage/Commissions
- Current engine uses ideal fills
- Real trading has spreads, commissions, slippage
- Reduce expected returns by 20-30%

### 5. Multiple Symbol Validation
- Strategy should work on correlated pairs
- Don't optimize for single instrument

### 6. Risk Management Validation
- Test different risk levels (1%, 2%, 3%)
- Ensure max drawdown is acceptable
- Calculate position sizing for live account

## 🛠️ Troubleshooting

### "Failed to load historical data"
- Check MT5 connection: `python test_mt5_connection.py`
- Verify symbol is available on your broker
- Try shorter date range (some brokers have limited history)
- Check symbol spelling (EURUSD vs EUR/USD)

### "No trades executed"
- Strategy may be too conservative
- Check confidence threshold in config.py
- Verify indicators are generating signals
- Review logs for "No signal" messages

### "Very low win rate"
- Strategy may not be profitable
- Check stop loss placement (too tight?)
- Review take profit targets (too far?)
- Analyze MAE/MFE to optimize

### Slow Performance
- Reduce date range
- Use lower resolution timeframe (H1 instead of M1)
- Save data to CSV for repeated tests
- Limit concurrent positions

## 📝 Examples

See `examples_backtest.py` for:
1. Simple backtest (single symbol)
2. Multi-symbol comparison
3. Risk parameter optimization

Run: `python examples_backtest.py`

## 🔜 Future Enhancements

- [ ] Walk-forward optimization
- [ ] Monte Carlo simulation
- [ ] Commission/slippage modeling
- [ ] Multi-timeframe analysis
- [ ] Correlation matrix for symbols
- [ ] Performance attribution (which signals work best)
- [ ] Strategy comparison (A/B testing)
- [ ] Real-time backtest vs live comparison

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review MT5 connection status
3. Verify historical data availability
4. Test with known profitable symbols (EURUSD, GBPUSD)

## 📚 Related Files

- `app/backtest/historical_engine.py` - Core backtest logic
- `app/backtest/data_loader.py` - MT5 data interface
- `app/backtest/visualizer.py` - Chart generation
- `app/ui/pages_backtest.py` - Streamlit interface
- `run_backtest.py` - CLI script
- `examples_backtest.py` - Usage examples
