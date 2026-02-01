#!/usr/bin/env python3
"""
Diagnose why bot is not trading
"""
import sys
sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

from app.trading.market_status import MarketStatus
from app.trading.integrated_analysis import IntegratedAnalyzer
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("trading_diag")

print("\n" + "=" * 80)
print("TRADING BOT DIAGNOSTIC")
print("=" * 80)

# Check 1: Configuration
print("\n1. CONFIGURATION CHECK:")
try:
    config = get_config()
    print(f"   Total symbols: {len(config.trading.default_symbols) + len(config.trading.crypto_symbols)}")
    print(f"   Forex symbols: {len(config.trading.default_symbols)}")
    print(f"   Crypto symbols: {len(config.trading.crypto_symbols)}")
    print(f"   Crypto list: {config.trading.crypto_symbols}")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 2: Market Status
print("\n2. MARKET STATUS CHECK:")
market = MarketStatus()
test_symbols = ["EURUSD", "BTCUSD", "ETHUSD", "BNBUSD"]
for symbol in test_symbols:
    is_open = market.is_symbol_open(symbol)
    print(f"   {symbol}: {'OPEN' if is_open else 'CLOSED'}")

# Check 3: Analysis - Can we generate signals?
print("\n3. SIGNAL GENERATION CHECK:")
analyzer = IntegratedAnalyzer()
timeframe = "M15"

for symbol in ["BTCUSD", "ETHUSD", "BNBUSD"][:2]:
    try:
        analysis = analyzer.analyze_symbol(symbol, timeframe, skip_ai=True)
        signal = analysis.get("signal", "ERROR")
        tech_data = analysis.get("technical", {}).get("data", {})
        rsi = tech_data.get("rsi", "N/A")
        print(f"   {symbol}: signal={signal}, RSI={rsi}")
    except Exception as e:
        print(f"   {symbol}: ERROR - {e}")

# Check 4: Position sizing
print("\n4. POSITION SIZING CHECK:")
try:
    from app.trading.risk_manager import RiskManager
    risk = RiskManager()
    
    # Test position size calculation
    equity = 4635  # From earlier check
    risk_per_trade = 0.75  # 0.75% per trade
    
    size = risk.calculate_position_size(
        symbol="BTCUSD",
        entry_price=84000,
        stop_loss=83000,
        current_equity=equity
    )
    print(f"   Test position size (BTCUSD): {size:.4f} lots")
    
    if size == 0:
        print(f"   WARNING: Position size is ZERO - Check risk parameters")
    
except Exception as e:
    print(f"   ERROR: {e}")

# Check 5: Look at actual logs
print("\n5. RECENT LOG ENTRIES:")
try:
    with open(r'c:\Users\Shadow\Downloads\Metatrade\logs\trading_bot.log', 'r') as f:
        lines = f.readlines()
    
    # Get last 20 lines
    recent = [l.strip() for l in lines[-20:] if 'BTCUSD' in l or 'ETHUSD' in l or 'crypto' in l.lower()]
    if recent:
        print(f"   Found {len(recent)} recent crypto references:")
        for line in recent[-5:]:
            print(f"     {line[:100]}...")
    else:
        print(f"   NO crypto trading attempts found in recent logs")
        
except Exception as e:
    print(f"   ERROR reading logs: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
