#!/usr/bin/env python3
"""Quick test to see if crypto is trading"""

import sys
sys.path.insert(0, 'c:\\Users\\Shadow\\Downloads\\Metatrade')

from app.trading.market_status import MarketStatus
from app.trading.integrated_analysis import get_integrated_analyzer
from app.core.logger import setup_logger
from app.core.config import get_config

logger = setup_logger("test_crypto")

config = get_config()
market_status = MarketStatus()
analyzer = get_integrated_analyzer()

print("\n" + "="*80)
print("🔍 Testing if CRYPTO symbols can trade")
print("="*80 + "\n")

crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD"]

for symbol in crypto_symbols:
    print(f"\n{symbol}:")
    print("-" * 40)
    
    # Check if market is open
    is_open = market_status.is_symbol_open(symbol)
    status_text = market_status.get_market_status_text(symbol)
    print(f"  Market Open: {'✅ YES' if is_open else '❌ NO'} ({status_text})")
    
    if not is_open:
        print(f"  ⚠️  PROBLEM: {symbol} is marked as CLOSED!")
        continue
    
    # Analyze the symbol
    try:
        analysis = analyzer.analyze_symbol(symbol, "M15", skip_ai=True)
        signal = analysis.get("signal", "UNKNOWN")
        print(f"  Signal: {signal}")
    except Exception as e:
        print(f"  ❌ Analysis Error: {e}")

print("\n" + "="*80 + "\n")
