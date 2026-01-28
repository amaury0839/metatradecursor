#!/usr/bin/env python3
"""Simple test of decision engine components"""

import sys
import os

# Fix encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.ai.dynamic_decision_engine import TickerPerformanceTracker, DynamicRiskAdjuster
from app.ai.ticker_indicator_optimizer import get_ticker_indicator_optimizer
from app.core.config import get_config

print("\n" + "="*80)
print("TESTING DECISION ENGINE COMPONENTS")
print("="*80)

config = get_config()
tracker = TickerPerformanceTracker()
risk_adjuster = DynamicRiskAdjuster()
optimizer = get_ticker_indicator_optimizer()

# Test first 5 symbols
test_symbols = config.trading.default_symbols[:5]

for symbol in test_symbols:
    try:
        print(f"\nTesting {symbol}...")
        
        # Test performance tracker
        metrics = tracker.calculate_ticker_metrics(symbol, hours=1)
        print(f"  Performance: WR={metrics.get('win_rate', 0):.1%}, Trades={metrics.get('trades', 0)}")
        
        # Test risk adjuster
        risk = risk_adjuster.get_dynamic_risk(symbol)
        print(f"  Risk: Adjusted={risk['adjusted_risk_pct']:.2f}%, Multiplier={risk['multiplier']:.2f}x")
        
        # Test indicator optimizer
        indicators = optimizer.get_optimal_indicators(symbol)
        print(f"  Indicators: Score={indicators.get('optimization_score', 0):.2f}")
        
        print(f"  ✓ {symbol} test passed")
        
    except Exception as e:
        print(f"  ✗ {symbol} test failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
