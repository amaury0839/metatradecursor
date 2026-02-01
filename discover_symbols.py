#!/usr/bin/env python3
"""
Discover all available symbols in ICMarkets MT5
"""
import MetaTrader5 as mt5
import json
from collections import defaultdict

def discover_symbols():
    """Explore all symbols available in MT5"""
    
    # Initialize MT5
    if not mt5.initialize(
        path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        login=52704771,
        password="Leonis1122",
        server="ICMarkets-Demo"
    ):
        print("❌ Failed to initialize MT5")
        return
    
    print("✅ MT5 initialized")
    
    # Get all symbols
    all_symbols = mt5.symbols_get()
    print(f"✅ Found {len(all_symbols)} total symbols\n")
    
    # Categorize by type
    categories = defaultdict(list)
    tradeable = []
    
    for symbol in all_symbols:
        symbol_name = symbol.name
        
        # Check if tradeable
        if symbol.trade_mode != mt5.SYMBOL_TRADE_MODE_DISABLED:
            tradeable.append(symbol_name)
            
            # Categorize
            name_upper = symbol_name.upper()
            
            if any(x in name_upper for x in ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'LTC', 'UNI', 'DOGE', 'AVAX', 'LINK', 'MATIC', 'ATOM']):
                categories['CRYPTO'].append(symbol_name)
            elif any(x in name_upper for x in ['US500', 'US100', 'NAS100', 'NIFTYCOIN']):
                categories['INDICES'].append(symbol_name)
            elif any(x in name_upper for x in ['GOLD', 'SILVER', 'COPPER', 'NATGAS', 'CRUDE', 'WTI', 'BRENT', 'CORN', 'WHEAT', 'SUGAR', 'COFFEE', 'COCOA']):
                categories['COMMODITIES'].append(symbol_name)
            elif any(x in name_upper for x in ['ES', 'NQ', 'YM', 'MES', 'MNQ', 'MYM', 'GC', 'SI', 'CL', 'NG', 'ZC', 'ZS']):
                categories['FUTURES'].append(symbol_name)
            elif any(x in name_upper for x in ['APPLE', 'GOOGLE', 'AMAZON', 'MSFT', 'TESLA', 'NVIDIA', 'META', 'AMZN', 'GOOG', 'AAPL', 'TSLA', 'NVDA', 'JPM', 'GS', 'BAC']):
                categories['STOCKS'].append(symbol_name)
            elif any(x in name_upper for x in ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SGD', 'HKD', 'ZAR', 'MXN', 'TRY', 'NOK', 'SEK', 'PLN']):
                categories['FOREX'].append(symbol_name)
            else:
                categories['OTHER'].append(symbol_name)
    
    # Print results
    print("=" * 80)
    print("📊 AVAILABLE SYMBOLS BY CATEGORY")
    print("=" * 80)
    
    for category in ['FOREX', 'INDICES', 'COMMODITIES', 'CRYPTO', 'STOCKS', 'FUTURES', 'OTHER']:
        symbols = categories[category]
        if symbols:
            print(f"\n🏷️  {category} ({len(symbols)} symbols):")
            print(f"    {', '.join(sorted(symbols)[:20])}")
            if len(symbols) > 20:
                print(f"    ... and {len(symbols) - 20} more")
    
    # Save to file
    output = {
        'total_symbols': len(all_symbols),
        'tradeable_symbols': len(tradeable),
        'categories': {k: v for k, v in categories.items() if v},
        'all_tradeable': sorted(tradeable)
    }
    
    with open('available_symbols.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Full list saved to available_symbols.json")
    print(f"\n📈 SUMMARY:")
    print(f"   Total: {len(all_symbols)}")
    print(f"   Tradeable: {len(tradeable)}")
    for cat, syms in sorted(categories.items(), key=lambda x: -len(x[1])):
        if syms:
            print(f"   {cat}: {len(syms)}")
    
    mt5.shutdown()

if __name__ == "__main__":
    discover_symbols()
