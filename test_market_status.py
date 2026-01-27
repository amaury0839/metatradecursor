#!/usr/bin/env python
"""Test market status detection"""

import sys
sys.path.insert(0, '.')

from app.trading.market_status import get_market_status
from datetime import datetime

print(f"Hora UTC actual: {datetime.utcnow()}\n")

market_status = get_market_status()

# Test forex symbols
print("=== FOREX SYMBOLS ===")
forex_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
for symbol in forex_symbols:
    is_open = market_status.is_symbol_open(symbol)
    status_text = market_status.get_market_status_text(symbol)
    print(f"{symbol}: {is_open} - {status_text}")

print("\n=== CRYPTO SYMBOLS ===")
crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD"]
for symbol in crypto_symbols:
    is_open = market_status.is_symbol_open(symbol)
    status_text = market_status.get_market_status_text(symbol)
    print(f"{symbol}: {is_open} - {status_text}")

print("\n=== TRADEABLE NOW ===")
tradeable = market_status.get_tradeable_symbols()
print(f"Symbols open for trading: {tradeable}")
