#!/usr/bin/env python3
"""
Diagnose MT5 Connection and UI Data Status
"""
import sys
sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

from app.trading.mt5_client import get_mt5_client
from app.core.config import get_config
from app.core.logger import setup_logger
import MetaTrader5 as mt5

logger = setup_logger("connection_diag")

print("\n" + "=" * 80)
print("METATRADER5 CONNECTION DIAGNOSTIC")
print("=" * 80)

# Check 1: MT5 Module
print("\n1. MT5 Module Status:")
try:
    print(f"   MT5 imported: OK")
    print(f"   MT5 version: {mt5.version()}")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Check 2: Initialize MT5
print("\n2. MT5 Initialization:")
try:
    if mt5.initialize():
        print(f"   MT5 initialized: OK")
        account = mt5.account_info()
        if account:
            print(f"   Account: {account.login}")
            print(f"   Balance: ${account.balance}")
            print(f"   Equity: ${account.equity}")
            print(f"   Status: CONNECTED")
        else:
            print(f"   ERROR: Could not get account info")
    else:
        print(f"   ERROR: Could not initialize MT5")
        print(f"   Last error: {mt5.last_error()}")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 3: Get MT5 Client from app
print("\n3. App MT5 Client:")
try:
    client = get_mt5_client()
    if client:
        print(f"   Client initialized: OK")
        info = client.get_account_info()
        if info:
            print(f"   Account info: {info}")
        else:
            print(f"   WARNING: No account info from app client")
    else:
        print(f"   ERROR: Could not get app MT5 client")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 4: Symbol Data
print("\n4. Symbol Data Retrieval:")
try:
    config = get_config()
    symbols = config.trading.default_symbols[:3]  # Test first 3
    
    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"   {symbol}: bid={tick.bid}, ask={tick.ask} - OK")
        else:
            print(f"   {symbol}: ERROR getting tick")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 5: Crypto Symbols
print("\n5. Crypto Symbols:")
try:
    crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD"]
    for symbol in crypto_symbols:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"   {symbol}: bid={tick.bid}, ask={tick.ask} - OK")
        else:
            print(f"   {symbol}: ERROR getting tick")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 6: Positions
print("\n6. Open Positions:")
try:
    positions = mt5.positions_get()
    if positions:
        print(f"   Found {len(positions)} open positions")
        for pos in positions[:3]:
            print(f"     - {pos.symbol}: {pos.type_string()} {pos.volume} lots")
    else:
        print(f"   No open positions")
except Exception as e:
    print(f"   ERROR: {e}")

mt5.shutdown()

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
