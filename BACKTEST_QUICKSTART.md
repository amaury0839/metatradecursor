# 🧪 Backtest Quick Reference

## 🚀 Quick Start (60 seconds)

```bash
# 1. Start UI
python run_ui_improved.py

# 2. Navigate to "🧪 Backtest" tab

# 3. Configure:
#    - Symbol: EURUSD
#    - Timeframe: M15  
#    - Date Range: Last 3 months
#    - Risk: 2%

# 4. Click "🚀 Run Backtest"

# 5. View results & download CSV
```

## 📊 Understanding Results

### Good Strategy Indicators
- ✅ Win Rate: 50-65%
- ✅ Profit Factor: 1.5-3.0
- ✅ Sharpe Ratio: >1.0
- ✅ Max Drawdown: <15%

### Warning Signs
- ⚠️ Win Rate: <40% or >80%
- ⚠️ Profit Factor: <1.2
- ⚠️ Sharpe Ratio: <0.5
- ⚠️ Max Drawdown: >25%

## 🔧 CLI One-Liners

```bash
# Basic test
python run_backtest.py --symbol EURUSD --timeframe M15 --start 2024-01-01 --end 2024-12-31

# With plots
python run_backtest.py --symbol EURUSD --timeframe M15 --start 2024-01-01 --end 2024-12-31 --plot

# Multiple symbols
for s in EURUSD GBPUSD USDJPY; do
  python run_backtest.py --symbol $s --timeframe M15 --start 2024-01-01 --end 2024-12-31 --output ${s}.csv
done

# Risk optimization
for r in 1.0 2.0 3.0; do
  python run_backtest.py --symbol EURUSD --timeframe M15 --risk-per-trade $r --start 2024-01-01 --end 2024-12-31
done
```

## 💻 Python API

```python
from app.backtest import HistoricalBacktestEngine, HistoricalDataLoader
from datetime import datetime, timedelta

# Load data
loader = HistoricalDataLoader()
end = datetime.now()
start = end - timedelta(days=90)
data = loader.load_data('EURUSD', 'M15', start, end)

# Run backtest
engine = HistoricalBacktestEngine(initial_balance=10000)
results = engine.run_backtest(
    symbol='EURUSD',
    timeframe='M15',
    data=data,
    risk_per_trade=2.0
)

# Access metrics
print(f"Win Rate: {results.win_rate:.1f}%")
print(f"Net Profit: ${results.net_profit:.2f}")
print(f"Profit Factor: {results.profit_factor:.2f}")
print(f"Max DD: {results.max_drawdown_pct:.2f}%")
print(f"Sharpe: {results.sharpe_ratio:.2f}")

# Export
trades_df = pd.DataFrame([{...} for t in results.trades])
trades_df.to_csv('results.csv')
```

## 📈 Common Tasks

### Task 1: Validate Current Strategy
```bash
python run_backtest.py \
  --symbol EURUSD \
  --timeframe M15 \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --risk-per-trade 2.0 \
  --initial-balance 10000 \
  --plot
```

### Task 2: Compare Symbols
```python
symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
results = {}

for symbol in symbols:
    data = loader.load_data(symbol, 'M15', start, end)
    results[symbol] = engine.run_backtest(symbol, 'M15', data)

# Compare
for s, r in results.items():
    print(f"{s}: PF={r.profit_factor:.2f}, WR={r.win_rate:.1f}%")
```

### Task 3: Optimize Risk
```python
best_sharpe = -999
best_risk = None

for risk in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    r = engine.run_backtest('EURUSD', 'M15', data, risk_per_trade=risk)
    if r.sharpe_ratio > best_sharpe:
        best_sharpe = r.sharpe_ratio
        best_risk = risk

print(f"Optimal risk: {best_risk}% (Sharpe: {best_sharpe:.2f})")
```

## 🎯 Metric Quick Reference

| Metric | Formula | Good Value | Bad Value |
|--------|---------|------------|-----------|
| Win Rate | Winners / Total | 50-65% | <40% or >80% |
| Profit Factor | Profit / Loss | 1.5-3.0 | <1.2 |
| Sharpe Ratio | Ret / StdDev | >1.0 | <0.5 |
| Sortino Ratio | Ret / DownStdDev | >1.5 | <0.8 |
| Max Drawdown | Peak to Trough % | <15% | >25% |

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to load data" | Check MT5 connection |
| "No trades executed" | Lower confidence threshold |
| "Very low win rate" | Review SL/TP settings |
| Slow performance | Reduce date range |

## 📚 Examples

```bash
# Run examples
python examples_backtest.py
# Choose: 1=Simple, 2=Multi-symbol, 3=Optimization
```

## 🔗 Documentation

- Full Guide: `BACKTEST_GUIDE.md`
- Implementation: `BACKTEST_IMPLEMENTATION_COMPLETE.md`
- Code: `app/backtest/`
- Tests: `test_backtest.py`

---

**Need Help?** Check logs in `logs/backtest_*.log`
