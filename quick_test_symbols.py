#!/usr/bin/env python3
"""
Quick validation - test available symbols without killing bot
Uses secondary MT5 connection
"""
import MetaTrader5 as mt5
import json
from time import sleep

# Symbols that ICMarkets typically has available
CANDIDATES = {
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADCHF", "CADJPY", "CHFJPY",
    "EURCHF", "EURGBP", "EURJPY", "NZDJPY", "GBPCHF", "GBPJPY",
    # Indices
    "US500", "US100", "NAS100", "UK100", "GER40", "FRA40", "AUS200", "HK50",
    # Commodities
    "GOLD", "SILVER", "COPPER", "CRUDE", "NATGAS", "BRENT",
    "CORN", "WHEAT", "SUGAR", "COCOA", "COFFEE",
    # Stocks (major)
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META",
    "JPM", "GS", "BAC", "NFLX", "JNJ", "XOM", "CVX",
    # Crypto
    "BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD", "ADAUSD", "DOTUSD",
    "LTCUSD", "UNIUSD", "XLMUSD", "DOGEUSD", "AVAXUSD", "LINKUSD", "MATICUSD",
    # Futures (major)
    "ES", "NQ", "YM", "GC", "CL", "NG",
}

def quick_test():
    """Quick test of available symbols"""
    print("🔌 Initializing MT5...")
    
    if not mt5.initialize():
        print("❌ Failed to init MT5")
        return {}
    
    print(f"✅ Testing {len(CANDIDATES)} candidate symbols...\n")
    
    valid = []
    for symbol in sorted(CANDIDATES):
        try:
            info = mt5.symbol_info(symbol)
            if info and info.trade_mode != mt5.SYMBOL_TRADE_MODE_DISABLED:
                valid.append(symbol)
                print(f"✅ {symbol}")
            else:
                print(f"❌ {symbol} (disabled or not found)")
        except:
            print(f"⚠️  {symbol} (error)")
    
    mt5.shutdown()
    
    print(f"\n✅ Found {len(valid)} valid symbols")
    
    # Save results
    with open('validated_symbols.txt', 'w') as f:
        for s in valid:
            f.write(s + '\n')
    
    return valid

if __name__ == "__main__":
    valid_symbols = quick_test()
    print(f"\n📁 Saved to validated_symbols.txt")
    print(f"\n📊 Summary: {len(valid_symbols)} tradeable symbols")
